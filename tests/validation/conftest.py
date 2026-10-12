"""Invented documents and knowledge for independent Clause5 rule mutations."""

import pytest

from ace_epics.knowledge import JsonKnowledgeProvider, ObjectDefinition, PropertySpec
from ace_epics.model import (
    Access,
    Bibb,
    EpicsDocument,
    GeneralInformation,
    ObjectIdentifier,
    ObjectTypeSupport,
    PropertyEntry,
    ServiceSupport,
    TestObject,
)
from ace_epics.model.names import NamedToken
from ace_epics.values import (
    BooleanValue,
    EnumeratedValue,
    GroupValue,
    IntegerValue,
    ObjectIdentifierValue,
)


def token(value):
    return NamedToken.model_validate(value)


def entry(name, value, access=Access.R):
    return PropertyEntry(name=token(name), value=value, access=access)


def group(elements):
    return GroupValue(delimiter="{", elements=elements)


def integer(value):
    return IntegerValue(value=value)


def enumeration(value):
    return EnumeratedValue(name=token(value))


def set_value(obj, prop, value):
    found = obj.property(prop)
    if found is None:
        obj.properties.append(entry(prop, value))
    else:
        found.value = value


def refresh_property_lists(document):
    for obj in document.objects:
        names = [p.name for p in obj.properties if p.name.canonical != "property-list"]
        set_value(obj, "property-list", group([EnumeratedValue(name=n) for n in names]))


class SyntheticProvider(JsonKnowledgeProvider):
    """Targeted invented specs isolate each rule from unrelated required properties."""

    def object_definition(self, object_type, revision):
        if revision is None:
            return None
        properties = {
            "property-list": PropertySpec(
                requirement="required",
                datatype="BACnetARRAY",
                access="R",
                read_only=True,
                introduced_rev=14,
            ),
        }
        for header in ("object-identifier", "object-name", "object-type"):
            properties[header] = PropertySpec(requirement="required", datatype="synthetic")
        if object_type == "device":
            for prop in (
                "protocol-revision",
                "protocol-object-types-supported",
                "protocol-services-supported",
                "segmentation-supported",
                "max-segments-accepted",
                "object-list",
            ):
                properties[prop] = PropertySpec(requirement="required", datatype="synthetic")
        if object_type == "analog-output":
            properties.update(
                {
                    "present-value": PropertySpec(
                        requirement="required",
                        datatype="Real",
                        access="W",
                        range={"min": 0, "max": 100},
                        min_range={"min": 10, "max": 90},
                    ),
                    "relinquish-default": PropertySpec(
                        requirement="conditional",
                        datatype="Real",
                        conditions=[{"kind": "required_if_present", "property": "priority-array"}],
                    ),
                    "old-property": PropertySpec(
                        requirement="optional", datatype="Integer", deprecated_rev=12
                    ),
                    "new-property": PropertySpec(
                        requirement="optional", datatype="Integer", introduced_rev=30
                    ),
                }
            )
        return ObjectDefinition(
            source="synthetic unit facts",
            object_type=object_type,
            revision=30,
            coverage_min_revision=0,
            properties=properties,
        )


@pytest.fixture
def provider():
    return SyntheticProvider()


@pytest.fixture
def document(provider):
    types = provider.object_types(30)
    services = provider.services(30)
    device = TestObject(
        identifier=ObjectIdentifier(object_type=token("device"), instance=100),
        name="Imagined Controller",
        object_type=token("device"),
        properties=[
            entry("protocol-revision", integer(30)),
            entry(
                "protocol-object-types-supported",
                group(
                    [
                        BooleanValue(value=i in {types["device"], types["analog-output"]})
                        for i in range(provider.object_types_bit_count(30))
                    ]
                ),
            ),
            entry(
                "protocol-services-supported",
                group(
                    [
                        BooleanValue(value=i == services["read-property"])
                        for i in range(provider.services_bit_count(30))
                    ]
                ),
            ),
            entry("segmentation-supported", enumeration("segmented-both")),
            entry("max-segments-accepted", integer(2)),
            entry(
                "object-list",
                group(
                    [
                        ObjectIdentifierValue(object_type=token("device"), instance=100),
                        ObjectIdentifierValue(object_type=token("analog-output"), instance=1),
                    ]
                ),
            ),
        ],
    )
    output = TestObject(
        identifier=ObjectIdentifier(object_type=token("analog-output"), instance=1),
        name="Invented Output",
        object_type=token("analog-output"),
        properties=[entry("present-value", integer(50), Access.W)],
    )
    doc = EpicsDocument(
        general=GeneralInformation(
            vendor_name="Imaginary Instruments",
            product_name="Synthetic Controller",
            product_model_number="TEST-1",
            product_description="Synthetic fixture",
        ),
        bibbs=[Bibb.model_validate("DS-RP-B")],
        services=[ServiceSupport(name=token("read-property"), initiate=False, execute=True)],
        object_types=[
            ObjectTypeSupport(name=token("device")),
            ObjectTypeSupport(name=token("analog-output")),
        ],
        objects=[device, output],
    )
    refresh_property_lists(doc)
    return doc
