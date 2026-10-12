"""Missing, ambiguous, and proprietary data must remain distinct from valid empty data."""

from ace_epics.knowledge import JsonKnowledgeProvider
from ace_epics.model import ObjectIdentifier, PropertyEntry, TestObject
from ace_epics.validation import validate
from ace_epics.values import ObjectIdentifierValue, UnspecifiedValue
from tests.validation.conftest import enumeration, group, integer, set_value, token


def result(doc, provider, rule):
    return validate(doc, provider, rules=[rule]).results[0]


def test_object_list_includes_proprietary_identifiers(document, provider):
    obj = TestObject(
        identifier=ObjectIdentifier(object_type=700, instance=1),
        object_type=700,
        name="Private Object",
    )
    document.objects.append(obj)
    assert result(document, provider, "C5-08").outcome == "fail"
    document.device.property("object-list").value.elements.append(
        ObjectIdentifierValue(object_type=700, instance=1)
    )
    assert result(document, provider, "C5-08").outcome == "pass"
    # Repeated entries fail even if their distinct set matches the database.
    document.device.property("object-list").value.elements.append(
        ObjectIdentifierValue(object_type=700, instance=1)
    )
    assert result(document, provider, "C5-08").outcome == "fail"


def test_property_list_numeric_ids_duplicates_and_exclusions(document, provider):
    for obj in document.objects:
        identifiers = provider.property_identifiers()
        entries = [
            integer(identifiers[p.name.canonical])
            for p in obj.properties
            if p.name.canonical != "property-list"
        ]
        set_value(obj, "property-list", group(entries))
    assert result(document, provider, "C5-16").outcome == "pass"
    document.objects[1].property("property-list").value.elements.append(integer(77))
    assert result(document, provider, "C5-16").outcome == "fail"
    set_value(document.objects[1], "property-list", group([integer(85), integer(85)]))
    assert result(document, provider, "C5-16").outcome == "fail"
    document.objects[1].properties.remove(document.objects[1].property("property-list"))
    assert result(document, provider, "C5-16").outcome == "fail"


def test_bit_vectors_unspecified_malformed_and_unknown_type(document, provider):
    set_value(document.device, "protocol-object-types-supported", UnspecifiedValue())
    assert result(document, provider, "C5-06").outcome == "skipped"
    assert result(document, provider, "C5-14").outcome == "skipped"
    set_value(document.device, "protocol-object-types-supported", group([]))
    from ace_epics.model import ObjectTypeSupport

    document.object_types.append(ObjectTypeSupport(name=token("unknown-standard-type")))
    findings = result(document, provider, "C5-06").diagnostics
    assert any("Unknown standard" in d.message for d in findings)
    set_value(document.device, "object-list", integer(42))
    assert result(document, provider, "C5-08").outcome == "fail"
    set_value(document.device, "segmentation-supported", UnspecifiedValue())
    assert result(document, provider, "C5-17").outcome == "skipped"


def test_verified_historical_lifecycle_fails_without_claiming_full_coverage(document):
    provider = JsonKnowledgeProvider()
    set_value(document.device, "protocol-revision", integer(13))
    # Property_List was introduced at revision14; independently verified metadata
    # can prove this violation even when a whole revision13 snapshot is unavailable.
    result_value = result(document, provider, "C5-10")
    assert result_value.outcome == "fail"
    assert any(
        d.property == "property-list" and d.severity == "error" for d in result_value.diagnostics
    )
    assert any(d.severity == "skipped" for d in result_value.diagnostics)


def test_nonexistent_standard_property_for_known_object_type(document, provider):
    document.objects[1].properties.append(
        PropertyEntry(name=token("vendor-name"), value=enumeration("synthetic"))
    )
    assert result(document, provider, "C5-10").outcome == "fail"


def test_external_object_features_are_conjunctive(document, provider):
    from ace_epics.validation import Context
    from ace_epics.validation.rules.objects import condition

    ctx = Context(document, provider)
    obj = document.objects[1]
    obj.properties.append(PropertyEntry(name=token("priority-array"), value=group([])))
    assert (
        condition(ctx, obj, {"kind": "required_if", "commandable": True, "feature": "value-source"})
        is None
    )
    assert (
        condition(
            ctx, obj, {"kind": "required_if", "commandable": False, "feature": "value-source"}
        )
        is False
    )


def test_null_is_not_an_unspecified_bit_or_numeric_value(document, provider):
    from ace_epics.validation import Query
    from ace_epics.values import NullValue

    set_value(document.device, "protocol-object-types-supported", group([NullValue()]))
    assert Query(document, provider).object_types_supported_bits is None
    set_value(document.device, "protocol-object-types-supported", group([UnspecifiedValue()]))
    assert Query(document, provider).object_types_supported_bits == [None]
    set_value(document.objects[1], "present-value", NullValue())
    assert result(document, provider, "C5-19").outcome == "fail"
    set_value(document.objects[1], "present-value", UnspecifiedValue())
    assert result(document, provider, "C5-19").outcome == "pass"
