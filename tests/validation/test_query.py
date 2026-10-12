"""Query API behavior needed by external Clause7 tools."""

from ace_epics.model import Access, Restrictions
from ace_epics.validation import Query
from ace_epics.validation.query import primitive
from ace_epics.values import UnspecifiedValue
from tests.validation.conftest import integer, set_value


def test_access_readability_and_array_index_zero(document, provider):
    query = Query(document, provider)
    output = document.objects[1]
    assert query.access(output, "present-value") == Access.W
    assert query.is_writable(output, "present-value")
    assert not query.is_conditionally_writable(output, "present-value")
    assert not query.is_read_only(output, "present-value")
    output.properties[0].access = Access.C
    assert query.is_writable(output, "present-value")
    assert query.is_conditionally_writable(output, "present-value")
    assert query.is_readable(output, "present-value")
    output.properties[0].not_readable = True
    assert not query.is_readable(output, "present-value")
    assert not query.is_readable(output, "missing")
    assert query.array_length(document.device, "object-list") == 2
    assert query.array_length(output, "present-value") is None
    assert query.is_unspecified(UnspecifiedValue())
    assert not query.is_unspecified(integer(0))


def test_limits_resolve_override_default_standard_and_variant_signature(document, provider):
    query = Query(document, provider)
    output = document.objects[1]
    assert primitive(query.limits(output, "present-value").maximum) == 100
    document.default_restrictions.real = Restrictions(minimum=integer(10), maximum=integer(90))
    output.properties[0].restrictions = Restrictions(maximum=integer(80))
    limits = query.limits(output, "present-value")
    assert primitive(limits.minimum) == 10 and primitive(limits.maximum) == 80
    copy = output.model_copy(deep=True)
    copy.identifier.instance = 2
    document.objects.append(copy)
    # Values alone do not define a Clause7.1.2 property variant.
    set_value(copy, "present-value", integer(60))
    assert len(query.variants("analog-output")) == 1
    copy.properties[0].restrictions.maximum = integer(70)
    assert len(query.variants("analog-output")) == 2
    copy.properties[0].restrictions.maximum = integer(80)
    copy.properties[0].not_readable = True
    assert len(query.variants("analog-output")) == 2


def test_datatype_defaults_only_apply_to_writable_properties(document, provider):
    output = document.objects[1]
    document.default_restrictions.real = Restrictions(maximum=integer(80))
    query = Query(document, provider)
    assert primitive(query.limits(output, "present-value").maximum) == 80
    output.properties[0].access = Access.R
    assert primitive(query.limits(output, "present-value").maximum) == 100
    output.properties[0].restrictions = Restrictions(maximum=integer(75))
    assert primitive(query.limits(output, "present-value").maximum) == 75


def test_query_missing_values_proprietary_headers_and_inferred_types(document):
    import pytest

    from ace_epics.model import ObjectIdentifier, TestObject
    from ace_epics.values import EnumeratedValue, ObjectIdentifierValue
    from tests.validation.conftest import entry

    obj = TestObject(
        identifier=ObjectIdentifier(object_type=700, instance=1), object_type=700, name="Private"
    )
    query = Query(document)
    assert query.value(None, "missing") is None
    node = query.value(obj, "object-type")
    assert isinstance(node, EnumeratedValue) and node.proprietary_number == 700
    assert query.datatype(obj, "object-name") == "character-string"
    assert query.datatype(obj, "missing") is None
    assert query.is_read_only(obj, "object-name")
    with pytest.raises(KeyError):
        query.access(obj, "missing")
    with pytest.raises(KeyError):
        query.limits(obj, "missing")
    assert primitive(ObjectIdentifierValue(object_type=700, instance=None)) is None
    obj.properties.append(entry("vendor-value", integer(3), Access.W))
    document.default_restrictions.signed_integer = Restrictions(maximum=integer(4))
    assert primitive(query.limits(obj, "vendor-value").maximum) == 4
    assert query.object_list is not None
    assert query.expected_property_list(obj) == {obj.properties[-1].name}


def test_standard_fractional_bounds_and_array_list_lengths(document):
    from ace_epics.knowledge import ObjectDefinition, PropertySpec
    from ace_epics.values import parse_value
    from tests.validation.conftest import SyntheticProvider, entry, group

    class Ranges(SyntheticProvider):
        def object_definition(self, object_type, revision):
            return ObjectDefinition(
                source="invented",
                object_type=object_type,
                revision=30,
                properties={
                    "present-value": PropertySpec(
                        requirement="required", datatype="Real", range={"min": -1.25, "max": "2.5"}
                    ),
                    "samples": PropertySpec(
                        requirement="optional",
                        datatype="BACnetARRAY of Real",
                        range={"max_length": 10},
                    ),
                    "events": PropertySpec(
                        requirement="optional", datatype="List of Real", range={"max_length": 12}
                    ),
                },
            )

    obj = document.objects[1]
    obj.properties.extend(
        [entry("samples", group([]), Access.W), entry("events", group([]), Access.W)]
    )
    document.default_restrictions.variable_length_array = Restrictions(maximum_length_array=8)
    document.default_restrictions.list = Restrictions(maximum_length_list=9)
    query = Query(document, Ranges())
    limits = query.limits(obj, "present-value")
    assert limits.minimum == parse_value("-1.25")[0]
    assert limits.maximum == parse_value("2.5")[0]
    assert query.limits(obj, "samples").maximum_length_array == 8
    assert query.limits(obj, "events").maximum_length_list == 9
    obj.property("events").access = Access.R
    assert query.limits(obj, "events").maximum_length_list == 12
