import json
from pathlib import Path

IN  = Path("datasets/cases_expanded.json")
OUT = Path("datasets/train.jsonl")

SYSTEM = ("You are an offline emergency triage assistant following START and WHO Basic Emergency Care. "
          "Only immediate, non-invasive first-aid steps. No medications. No diagnoses. "
          "Return valid JSON with keys: triage_level, actions, reasoning, disclaimer.")

def actions_for (label):
    if label=="immediate":
        return ["Open and maintain airway",
                "Control severe bleeding if present",
                "Monitor breathing continuously",
                "Prepare for rapid transport"]

    if label == "Delayed":
        return ["Immobilize injured limb",
                "Cold pack if swelling",
                "Reassess every 10–15 minutes",
                "Prepare for transport when possible"]
    if label == "Minor":
        return ["Clean minor wounds",
                "Provide reassurance",
                "Keep warm and hydrated",
                "Direct to minor treatment area"]
    if label == "Expectant":
        return ["Attempt airway once; if no breathing, prioritize others",
                "Provide comfort care",
                "Reassure bystanders"]
    return ["Reassess and follow START"]

def reason_for(label, c):
    v = c.get("vitals", {})
    rr = v.get("resp_rate"); pulse = (v.get("pulse") or "").lower()
    cap = str(v.get("cap_refill"))


    if label == "Immediate":
        if isinstance(rr, (int,float)) and rr > 30: return "Respiratory rate >30/min triggers Immediate."
        if pulse in {"weak","none"}: return "Poor perfusion (weak/absent pulse) triggers Immediate."
        try: cap_num = float(cap)
        except: cap_num = None
        if cap_num and cap_num > 2: return "Capillary refill >2 seconds triggers Immediate."
        return "Mental status or other red flags trigger Immediate."
    if label == "Minor": return "Ambulatory/walking with stable vitals qualifies as Minor."
    if label == "Delayed": return "Injured, stable vitals, follows commands → Delayed per START."
    if label == "Expectant": return "Apneic after airway or pulseless with no breathing → Expectant."
    return "START rule applied."

def build_input(c):
    return ("Triage this case.\n"
            f"Description: {c['description']}\n"
            f"Vitals: {json.dumps(c['vitals'], ensure_ascii=False)}")


def main():
    data = json.load(open(IN, "r", encoding="utf-8"))
    with open(OUT, "w", encoding="utf-8") as f:
        for c in data:
            label = c["expected_triage"]
            output_obj = {
                "triage_level": label,
                "actions": actions_for(label),
                "reasoning": reason_for(label, c),
                "disclaimer": "Support tool only; not a substitute for professional medical judgment."
            }
            row = {
                "system": SYSTEM,
                "instruction": "Follow START + WHO guidance. Output strict JSON.",
                "input": build_input(c),
                "output": json.dumps(output_obj, ensure_ascii=False),
                "meta": {"label": label}
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {OUT}")

if __name__ == "__main__":
    main()




    
    