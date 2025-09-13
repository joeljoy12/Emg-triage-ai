# scripts/start_engine.py
import re

def _to_num(x):
    try:
        return float(x)
    except Exception:
        return None

def _norm(x):
    return (x or "").strip().lower()

def _has(text, keywords):
    t = _norm(text)
    return any(k in t for k in keywords)

def start_triage(case: dict) -> str:
    """
    Returns one of: Immediate, Delayed, Minor, Expectant
    """
    desc = _norm(case.get("description", ""))
    vit  = case.get("vitals", {}) or {}
    rr   = _to_num(vit.get("resp_rate"))
    pulse = _norm(vit.get("pulse"))
    cr    = vit.get("cap_refill")

    # cap refill normalize
    cr_val = None
    if isinstance(cr, (int, float)): cr_val = float(cr)
    elif isinstance(cr, str):
        s = cr.strip()
        if re.match(r"^>\s*2", s): cr_val = 3.0   # poor perfusion
        elif re.match(r"^<\s*2", s): cr_val = 1.0
        else:
            try: cr_val = float(s)
            except: cr_val = None

    # description signals
    no_breathing = _has(desc, ["no breathing", "not breathing"])
    after_airway = _has(desc, ["after airway", "despite airway", "even after airway", "reposition"])
    airway_then_breath = _has(desc, ["until airway opened, then resumes breathing", "then breathing"])
    unresponsive = _has(desc, ["unresponsive", "not responsive", "doesn't follow commands", "cannot follow commands", "unconscious"])
    ambulatory = _has(desc, ["walking", "moving independently", "ambulatory", "walking unaided"])
    massive_bleeding = _has(desc, ["heavy bleeding", "severe bleeding", "uncontrolled bleeding"])

    # Expectant
    no_pulse = pulse in {"none", "absent", ""}
    if (no_breathing and after_airway) or (no_breathing and no_pulse):
        return "Expectant"

    # Immediate
    if rr is not None and rr > 30: return "Immediate"
    if cr_val is not None and cr_val > 2: return "Immediate"
    if pulse in {"weak", "none", "absent"}: return "Immediate"
    if unresponsive: return "Immediate"
    if massive_bleeding: return "Immediate"
    if airway_then_breath: return "Immediate"

    # Minor
    if ambulatory: return "Minor"

    # Otherwise
    return "Delayed"

# quick manual check
if __name__ == "__main__":
    demo = {
        "description": "Heavy forearm bleeding, pale, dizzy, responsive to voice",
        "vitals": {"resp_rate": 28, "pulse": "fast", "cap_refill": ">2"}
    }
    print(start_triage(demo))  # expect: Immediate
