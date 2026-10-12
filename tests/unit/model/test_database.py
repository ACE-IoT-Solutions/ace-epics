import pytest
from pydantic import ValidationError

from ace_epics.model.database import Access, ObjectIdentifier, PropertyEntry, TestObject
from ace_epics.model.names import NamedToken
from ace_epics.values import IntegerValue, UnspecifiedValue


def obj(properties=None, **kwargs):
    data = {
        "identifier": ObjectIdentifier(object_type="analog-value", instance=6),
        "name": "AV6",
        "object_type": "Analog Value",
        "properties": properties or [],
    }
    return TestObject.model_validate(data | kwargs)


@pytest.mark.parametrize("instance", [0, 4194303])
def test_object_identifier_bounds(instance):
    ident = ObjectIdentifier(object_type="analog-value", instance=instance)
    assert str(ident) == f"(analog-value, {instance})"
    assert not ident.is_proprietary


@pytest.mark.parametrize(
    "args",
    [
        {"object_type": 127, "instance": 1},
        {"object_type": "device", "instance": -1},
        {"object_type": "device", "instance": 4194304},
    ],
)
def test_invalid_identifiers(args):
    with pytest.raises(ValidationError):
        ObjectIdentifier(**args)


def test_proprietary_header_only():
    ident = ObjectIdentifier(object_type=700, instance=1)
    assert ident.is_proprietary and str(ident) == "(proprietary 700, 1)"
    proprietary = obj(identifier=ident, object_type=700)
    assert not proprietary.properties
    with pytest.raises(ValidationError):
        obj(
            identifier=ident,
            object_type=700,
            properties=[PropertyEntry(name="present-value", value=IntegerValue(value=1))],
        )


def test_mismatch_duplicates_and_repeated_headers():
    with pytest.raises(ValidationError):
        obj(object_type="analog-input")
    with pytest.raises(ValidationError):
        obj(
            [
                PropertyEntry(name=n, value=IntegerValue(value=1))
                for n in ["Present_Value", "present-value"]
            ]
        )
    with pytest.raises(ValidationError):
        obj([PropertyEntry(name="object-name", value=UnspecifiedValue())])


def test_property_helpers_and_non_readable_marker():
    prop = PropertyEntry(
        name="Present_Value",
        value=UnspecifiedValue(),
        access="C",
        comment="Writable when out of service",
        not_readable=True,
    )
    item = obj([prop])
    assert item.property("present value") == prop
    assert item.property(NamedToken(canonical="present-value")) == prop
    assert item.property("missing") is None
    assert item.has_property("PRESENT-VALUE")
    assert item.property_names() == {NamedToken(canonical="present-value")}
    assert prop.access == Access.C and prop.not_readable
    assert PropertyEntry(name="x", value=IntegerValue(value=1)).access == Access.R


def test_header_metadata_keys_and_default_elision():
    from ace_epics.model import PropertyMetadata

    item = obj(header_metadata={"object-name": PropertyMetadata(access="W", comment="Renameable")})
    assert item.header_metadata["object-name"].access == Access.W
    assert obj(header_metadata={"object-type": PropertyMetadata()}).header_metadata == {}
    with pytest.raises(ValidationError, match="three object headers"):
        obj(header_metadata={"present-value": PropertyMetadata(access="C")})
    proprietary = obj(
        identifier=ObjectIdentifier(object_type=700, instance=1),
        object_type=700,
        header_metadata={"object-name": PropertyMetadata(access="W")},
    )
    assert proprietary.header_metadata["object-name"].access == Access.W
