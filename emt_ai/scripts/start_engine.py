# scripts/start_engine.py
import json
from typing import Optional, Union

def start_triage(
    description: str,
    resp_rate: Optional[float] = None,
    pulse: Optional[str] = None,
    cap_refill: Optional[Union[str, float]] = None,
) -> str:
    """
    Deterministic START-style triage.
    Returns one of: "Expectant", "Immediate", "Minor", "Delayed"
    """
    desc  = (description or "").lower().strip()
    pulse = (pulse or "").lower().strip()

    # --- helper: parse capillary refill like ">2", "<2", "3", 3.0 ---
    def parse_cap_refill(x):
        if x is None:
            return None
        s = str(x).strip().lower()
        try:
            return float(s)  # plain number
        except ValueError:
            if s.startswith(">"):
                try:
                    return float(s[1:]) + 0.01  # treat >2 as just over 2
                except ValueError:
                    return None
            if s.startswith("<"):
                try:
                    return float(s[1:]) - 0.01  # treat <2 as just under 2
                except ValueError:
                    return None
        return None

    cr = parse_cap_refill(cap_refill)

    # --- EXPECTANT ---
    # No breathing + no pulse, or explicit “not breathing even after airway”
    if (("not breathing" in desc) or ("no breathing" in desc) or (resp_rate == 0)) and (
        pulse in {"none", "absent"} or "no pulse" in desc
    ):
        return "Expectant"
    if (("not breathing" in desc) or ("no breathing" in desc)) and (
        "after airway" in desc or "despite airway" in desc or "even after airway" in desc
    ):
        return "Expectant"

    # --- IMMEDIATE ---
    if resp_rate is not None and resp_rate > 30:
        return "Immediate"
    if cr is not None and cr > 2.0:
        return "Immediate"
    if pulse in {"weak", "none", "absent"}:
        return "Immediate"
    if any(k in desc for k in [
        "unresponsive",
        "cannot follow commands",
        "not following commands",
        "doesn't follow commands",
        "unconscious",
    ]):
        return "Immediate"
        # --- If text says "no/not breathing" but no pulse info, treat as Immediate (airway step implied) ---
    if ("no breathing" in desc) or ("not breathing" in desc):
        # If pulseless, it's Expectant (handled above), otherwise assume Immediate after airway reposition
        return "Immediate"


    # --- MINOR (ambulatory) ---
    if any(k in desc for k in ["walking", "ambulatory", "moving independently", "walking unaided"]):
        return "Minor"

    # --- DEFAULT ---
    return "Delayed"


# ----------------- OPTIONAL: only runs when you execute this file directly -----------------
if __name__ == "__main__":
    with open("./scripts/cases.json", "r", encoding="utf-8") as f:
        cases = json.load(f)

    correct = 0
    for i, c in enumerate(cases, 1):
        vitals = c.get("vitals", {})
        pred = start_triage(
            c.get("description", ""),
            vitals.get("resp_rate"),
            vitals.get("pulse"),
            vitals.get("cap_refill"),
        )
        expected = c.get("expected_triage")
        mark = "✅" if pred == expected else "❌"
        print(f"{i:02d} {mark} predicted={pred:9s} expected={expected:9s} | {c.get('description','')}")
        correct += int(pred == expected)
        

    print(f"\nAccuracy: {correct}/{len(cases)} = {correct/len(cases)*100:.1f}%")

    # Sanity checks
    print(start_triage("No breathing, no pulse", 0, "none", ">2"))                 # Expectant
    print(start_triage("Conscious but RR 40", 40, "strong", "<2"))                 # Immediate
    print(start_triage("Unconscious but breathing", 20, "strong", "<2"))           # Immediate
    print(start_triage("Ambulatory with sprained ankle", 18, "strong", "<2"))      # Minor
