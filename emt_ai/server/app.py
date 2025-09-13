# server/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys, pathlib
import requests
from typing import List
from datetime import datetime




# Make sure 'scripts' is on path BEFORE importing
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from scripts.start_engine import start_triage  # noqa: E402

from server.llm_client import LLMClient  # noqa: E402

app = FastAPI(title="Emergency Triage (Offline)")
llm = LLMClient()  # default model = phi3:mini (change via env TRIAGE_LLM_MODEL)

# CORS (for local UI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # tighten for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ models ------------------
class Vitals(BaseModel):
    resp_rate: Optional[float] = None
    pulse: Optional[str] = None
    cap_refill: Optional[str | float] = None

class TriageIn(BaseModel):
    description: str
    vitals: Optional[Vitals] = None

# ------------------ demo actions ------------------
ACTIONS = {
    "Immediate": [
        "Open and maintain airway",
        "Control major external bleeding",
        "Position for breathing",
        "Prepare rapid transport",
        "Reassess every 2–3 minutes",
    ],
    "Delayed": [
        "Immobilize injured limb",
        "Cold pack if swelling",
        "Reassess every 10–15 minutes",
        "Prepare for transport when possible",
    ],
    "Minor": [
        "Clean minor wounds with clean water",
        "Apply clean dressing",
        "Provide reassurance",
        "Advise self-care and recheck if worse",
    ],
    "Expectant": [
        "Prioritize comfort and dignity",
        "Monitor for return of breathing",
        "Allocate resources to salvageable patients",
        "Reassess periodically if safe",
    ],
}

@app.get("/health")
def health():
    return {"ok": True, "offline": True}

# Store last N cases in memory
RECENT_CASES: List[dict] = []

# ------------------ main triage endpoint ------------------
# ------------------ main triage endpoint ------------------
@app.post("/triage")
def triage(inp: TriageIn):
    v = inp.vitals or Vitals()

    label = start_triage(inp.description, v.resp_rate, v.pulse, v.cap_refill)

    # reason (rule or LLM)
    d = (inp.description or "").lower().strip()
    cap_str = str(v.cap_refill).strip().lower() if v.cap_refill is not None else ""
    why = (
        "no breathing + no pulse"
        if (("no breathing" in d or "not breathing" in d or (v.resp_rate == 0))
            and (v.pulse or "").lower() in {"none", "absent"})
        else "RR > 30" if (v.resp_rate is not None and v.resp_rate > 30)
        else "capillary refill > 2s" if (
            (cap_str.startswith(">") and cap_str[1:].replace(".","",1).isdigit() and float(cap_str[1:]) >= 2)
            or (cap_str.replace(".","",1).isdigit() and float(cap_str) > 2)
        )
        else "poor perfusion / mental status" if (
            (v.pulse or "").lower() in {"weak", "none", "absent"}
            or any(k in d for k in ["unresponsive", "cannot follow commands", "unconscious"])
        )
        else "ambulatory" if any(k in d for k in [
            "walking", "ambulatory", "moving independently", "walking unaided"
        ])
        else "default"
    )

    # NEW: build vitals dict and ask the local LLM for a short reason
    vitals_dict = {
        "resp_rate": v.resp_rate,
        "pulse": v.pulse,
        "cap_refill": v.cap_refill,
    }
    llm_reason = llm.safe_reason(label, inp.description, vitals_dict)  # returns None if Ollama down
    reason_text = llm_reason or f" {why}."            # fallback to rule reason

    # NEW: confidence from rule signal strength
    conf = confidence_from_rule(why, v)

    result = {
        "triage_level": label,
        "actions": ACTIONS[label],
        "reasoning": reason_text,
        "disclaimer": "Support tool only; not a substitute for professional medical judgment.",
        "confidence": conf,
        "ts": datetime.utcnow().isoformat(),   # NEW
        "raw": inp.dict(),  # optional: store original input
# optional: store original input
    }

    RECENT_CASES.insert(0, result)
    if len(RECENT_CASES) > 20:
        RECENT_CASES.pop()

    return result


# ------------------ list recent cases ------------------
@app.get("/cases")
def get_cases():
    return RECENT_CASES



# ------------------ helper: confidence scoring (not used yet) ------------------
def confidence_from_rule(why: str, v) -> float:
    base = 0.7
    if "no breathing + no pulse" in why: base = 0.98
    elif "RR > 30" in why:               base = 0.92
    elif "capillary refill > 2s" in why: base = 0.88
    elif "poor perfusion / mental status" in why: base = 0.84
    elif "ambulatory" in why:            base = 0.9

    # small penalties for missing vitals
    if v.resp_rate is None: base -= 0.03
    if not v.pulse:         base -= 0.03
    if v.cap_refill is None:base -= 0.02

    return max(0.5, min(0.99, base))

