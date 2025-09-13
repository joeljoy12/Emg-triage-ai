from test_start_engine import start_triage

def case(desc, rr=None, pulse="strong", cr="<2"):
    return {
        "description": desc,
        "vitals": {"resp_rate": rr, "pulse": pulse, "cap_refill": cr}
    }

def test_immediate_rr_over_30():
    c = case("Breathing fast", rr=31, pulse="strong", cr="<2")
    assert start_triage(c) == "Immediate"

def test_immediate_poor_perfusion():
    c = case("Looks pale", rr=20, pulse="weak", cr=">2")
    assert start_triage(c) == "Immediate"

def test_minor_ambulatory():
    c = case("Walking with small cuts", rr=18, pulse="strong", cr="<2")
    assert start_triage(c) == "Minor"

def test_expectant_no_breathing_after_airway():
    c = case("No breathing even after airway reposition", rr=0, pulse="none", cr=">2")
    assert start_triage(c) == "Expectant"

def test_delayed_default():
    c = case("Open arm fracture, stable, follows commands", rr=20, pulse="strong", cr="<2")
    assert start_triage(c) == "Delayed"
