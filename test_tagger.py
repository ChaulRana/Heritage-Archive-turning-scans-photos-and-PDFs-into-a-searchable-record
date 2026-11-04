from services.tagger import analyse

def test_temple_in_gujarat():
    r = analyse("The Sun Temple at Modhera, Gujarat was built in the 11th century by the Solanki dynasty.")
    assert r["category"] == "temple"
    assert r["location"] == "Gujarat"
    assert r["era"] == "Medieval"
