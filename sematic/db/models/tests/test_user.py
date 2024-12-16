# Sematic
from sematic.db.models.factories import make_user


def test_friendly_name():
    john = make_user(email="john@beatles.co.uk")
    assert john.get_friendly_name() == "john@beatles.co.uk"

    paul = make_user(email="paul@beatles.co.uk", first_name="Paul")
    assert paul.get_friendly_name() == "Paul"

    george = make_user(email="paul@beatles.co.uk", last_name="Harrison")
    assert george.get_friendly_name() == "Harrison"

    ringo = make_user(email="ringo@beatles.co.uk", first_name="Ringo", last_name="Starr")
    assert ringo.get_friendly_name() == "Ringo Starr"
