
import json, re, hashlib
from pathlib import Path

IN_PATH  = Path("datasets/cases_expanded.json")        # your raw 200 cases
OUT_CLEAN = Path("datasets/cases_expanded.clean.json") # cleaned output
OUT_REJ   = Path("datasets/cases_expanded.rejects.json") # bad cases for review

# --- allowed values ---
ALLOWED_LABELS = {"Immediate","Delayed","Minor","Expectant"}
ALLOWED_PULSES = {"strong","normal","weak","none"}

RR_RE = re.compile(r"\bRR\s*([0-9]+)\b", re.IGNORECASE)

def norm_pulse(p):
    if p is None: return None
    s = str(p).strip().lower()
    if s == "week": s = "weak"     # typo fix
    if s in {"absent","no"}: s = "none"
    if s == "ok": s = "normal"
    return s if s in ALLOWED_PULSES else s


def rr_from_text(desc):
     m = RR_RE.search(desc)
     return int(m.group(1)) if m else None
 
 
def hash_case(c):
    vit = c["vitals"]
    key = "|".join([
        c.get("description","").strip().lower(),
        str(vit.get("resp_rate")),
         str(vit.get("pulse")).strip().lower(),
        str(vit.get("cap_refill")),
        c.get("expected_triage","")
    ])
    
    return hashlib.sha1(key.encode("utf-8")).hexdigest()

def main():
    data = json.load(open(IN_PATH, "r", encoding="utf-8"))
    clean, rejects, seen = [], [], set()

    for c in data:
        reasons = []
        desc = c.get("description","")
        vit = c.get("vitals",{})
        label = c.get("expected_triage")
        

     # --- normalize pulse ---
        vit["pulse"] = norm_pulse(vit.get("pulse"))

 # --- schema check ---
        if label not in ALLOWED_LABELS:
            reasons.append("invalid label")

        if "resp_rate" not in vit or "pulse" not in vit or "cap_refill" not in vit:
            reasons.append("missing vital field")
            
          # --- consistency check ---
        rr_text = rr_from_text(desc)
        if rr_text and isinstance(vit.get("resp_rate"), int) and rr_text != vit["resp_rate"]:
            reasons.append(f"RR mismatch (text={rr_text}, vitals={vit['resp_rate']})")
        
         # --- dedupe check ---
        h = hash_case(c)
        if h in seen:
            reasons.append("duplicate")
        else:
            seen.add(h)
            
         # --- dedupe check ---
        h = hash_case(c)
        if h in seen:
            reasons.append("duplicate")
        else:
            seen.add(h)
        
          # --- collect result ---
        if reasons:
            rejects.append({"case": c, "reasons": reasons})
        else:
            clean.append(c)

# --- save files ---
    json.dump(clean, open(OUT_CLEAN,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    json.dump(rejects, open(OUT_REJ,"w",encoding="utf-8"), indent=2, ensure_ascii=False)

    print(f"Input: {len(data)}")
    print(f"Clean: {len(clean)}")
    print(f"Rejects: {len(rejects)} (see {OUT_REJ})")
    print(f"Wrote clean dataset to {OUT_CLEAN}")

if __name__ == "__main__":
    main()



    