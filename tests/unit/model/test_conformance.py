import pytest
from pydantic import ValidationError

from ace_epics.model.conformance import (
    Bibb,
    ObjectTypeSupport,
    ServiceSupport,
    SpecialFunctionality,
)


@pytest.mark.parametrize("initiate,execute", [(True, False), (False, True), (True, True)])
def test_services(initiate, execute):
    assert (
        ServiceSupport(name="Who-Is", initiate=initiate, execute=execute).name.canonical == "who-is"
    )


def test_service_requires_direction():
    with pytest.raises(ValidationError):
        ServiceSupport(name="ReadProperty")


@pytest.mark.parametrize("alias", ["Createable", "Creatable", "createable", "creatable"])
def test_creation_aliases(alias):
    item = ObjectTypeSupport(name="Analog Value", **{alias: True, "Deleteable": True})
    assert item.createable and item.deleteable
    assert item.model_dump(by_alias=True)["Createable"]


def test_default_flags_and_bibb_warnings():
    assert not ObjectTypeSupport(name="Device").createable
    assert not Bibb.model_validate("DS-RP-B").warnings()
    assert Bibb.model_validate("vendor-custom").warnings()[0].code == "M-BIBB-NAME"


def test_special_numbers_and_advisory_windows():
    assert not SpecialFunctionality(segmented_requests_window=4).warnings()
    assert SpecialFunctionality(
        segmented_requests_window=0, segmented_responses_window=128
    ).warnings()
    for bad in [-1, 1476.0]:
        with pytest.raises(ValidationError):
            SpecialFunctionality(max_apdu_size=bad)
