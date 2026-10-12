import pytest
from pydantic import ValidationError

from ace_epics.model.names import NamedToken, normalize_name


@pytest.mark.parametrize(
    "text", ["Present_Value", "present value", "PRESENT---VALUE", " present_value "]
)
def test_normalization(text):
    token = NamedToken.model_validate(text)
    assert token.canonical == normalize_name(text) == "present-value"
    assert token.raw == text
    assert token == NamedToken(canonical="present-value", raw="other spelling")
    assert hash(token) == hash(NamedToken.model_validate({"name": "Present Value"}))
    assert str(token) == token.name == "present-value"
    assert token.original == text
    assert token != "present-value"


def test_aliases_and_freezing():
    assert NamedToken.model_validate({"name": "Device", "original": "DEVICE"}).canonical == "device"
    with pytest.raises(ValidationError):
        NamedToken(canonical="device").__setattr__("canonical", "other")
