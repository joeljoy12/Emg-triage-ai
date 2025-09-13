import json, random
from pathlib import Path

# -------------------------
# Central config
# -------------------------
RR_RANGES = {
    "Immediate_RR": [31, 32, 34, 36, 38, 40, 42],
    "Minor":        [18, 20, 22, 24, 26],
    "Delayed":      [18, 20, 22, 24, 26, 28],
    "Expectant":    [0],
}

PHRASE_BANK = {
    "Immediate_RR": [
        "breathing fast", "breathing very fast", "breathing rapidly",
        "tachypneic", "gasping for air"
    ],
    "Immediate_Perfusion": [
        "weak pulse", "thready pulse", "skin pale and clammy",
        "cap refill 3 seconds", "signs of poor circulation"
    ],
    "Immediate_Mental": [
        "unresponsive", "not responding", "unconscious",
        "cannot follow commands", "not following commands"
    ],
    "Minor": [
        "walking", "ambulatory", "moving independently",
        "walking unaided", "walking and talking"
    ],
    "Delayed": [
        "injured but stable", "follows commands, stable vitals",
        "bleeding controlled, speaking clearly",
        "fracture present, stable", "burns limited area, airway intact"
    ],
    "Expectant": [
        "not breathing even after airway reposition",
        "no breathing and pulseless", "apneic despite airway"
    ],
}

# -------------------------
# Helpers
# -------------------------
def make_desc(age, sex, phrase, rr=None, extra=""):
    parts = [f"{age}{sex}", phrase]
    if rr is not None:
        parts.append(f"RR {rr}")
    if extra:
        parts.append(extra)
    return ", ".join(parts)

def case_obj(description, rr, pulse, cap, label):
    return {
        "description": description,
        "vitals": {"resp_rate": rr, "pulse": pulse, "cap_refill": cap},
        "expected_triage": label
    }

# -------------------------
# Generators
# -------------------------
def gen_immediate_rr(n=20, seed=11):
    random.seed(seed)
    out = []
    for _ in range(n):
        age, sex = random.choice([7,12,25,40,65]), random.choice(["M","F"])
        rr = random.choice(RR_RANGES["Immediate_RR"])  # >30
        phrase = random.choice(PHRASE_BANK["Immediate_RR"])
        desc = make_desc(age, sex, phrase, rr, extra=random.choice([
            "speaking","speaking in short phrases","able to answer questions"
        ]))
        out.append(case_obj(desc, rr, pulse=random.choice(["strong","normal"]), cap="<2", label="Immediate"))
    return out

def gen_immediate_perfusion(n=15, seed=12):
    random.seed(seed)
    out = []
    for _ in range(n):
        age, sex = random.choice([7,12,25,40,65]), random.choice(["M","F"])
        rr = random.choice([18,20,22,24,26,28])  # ≤30
        phrase = random.choice(PHRASE_BANK["Immediate_Perfusion"])
        out.append(case_obj(make_desc(age, sex, phrase, rr),
                            rr, pulse=random.choice(["weak","none"]), cap=">2", label="Immediate"))
    return out

def gen_immediate_mental(n=15, seed=13):
    random.seed(seed)
    out = []
    for _ in range(n):
        age, sex = random.choice([7,12,25,40,65,80]), random.choice(["M","F"])
        rr = random.choice([18,20,22,24,26,28])  # ≤30
        phrase = random.choice(PHRASE_BANK["Immediate_Mental"])
        out.append(case_obj(make_desc(age, sex, phrase, rr),
                            rr, pulse="strong", cap="<2", label="Immediate"))
    return out

def gen_delayed(n=50, seed=14):
    random.seed(seed)
    out = []
    for _ in range(n):
        age, sex = random.choice([12,20,30,40,50,65]), random.choice(["M","F"])
        rr = random.choice(RR_RANGES["Delayed"])  # ≤30
        phrase = random.choice(PHRASE_BANK["Delayed"])
        out.append(case_obj(make_desc(age, sex, phrase, rr, extra=random.choice([
            "alert and follows commands", "calm and responsive", "answers questions clearly"
        ])), rr, pulse="strong", cap="<2", label="Delayed"))
    return out

def gen_minor(n=50, seed=15):
    random.seed(seed)
    out = []
    for _ in range(n):
        age, sex = random.choice([10,20,30,50]), random.choice(["M","F"])
        rr = random.choice(RR_RANGES["Minor"])
        phrase = random.choice(PHRASE_BANK["Minor"])
        out.append(case_obj(make_desc(age, sex, phrase, rr, extra="calm and coherent"),
                            rr, pulse="strong", cap="<2", label="Minor"))
    return out

def gen_expectant(n=50, seed=16):
    random.seed(seed)
    out = []
    for _ in range(n):
        age, sex = random.choice([50,65,70,80]), random.choice(["M","F"])
        rr = 0
        phrase = random.choice(PHRASE_BANK["Expectant"])
        out.append(case_obj(make_desc(age, sex, phrase, rr),
                            rr, pulse="none", cap=">2", label="Expectant"))
    return out

# -------------------------
# Final dataset builder (200 total)
# -------------------------
def build_dataset_200():
    out = []
    out += gen_immediate_rr()        # 20
    out += gen_immediate_perfusion() # 15
    out += gen_immediate_mental()    # 15
    out += gen_delayed()             # 50
    out += gen_minor()               # 50
    out += gen_expectant()           # 50
    return out

# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    data = build_dataset_200()
    print(f"Generated {len(data)} cases")

    # Save
    out_path = Path("datasets/cases_expanded.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(data)} cases to {out_path}")
