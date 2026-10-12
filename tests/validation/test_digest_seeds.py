"""Exact remaining examples from Clause5 digest section7, seeds 4-31."""

import pytest

from ace_epics.diagnostics import Severity
from ace_epics.knowledge import BibbDefinition, JsonKnowledgeProvider
from ace_epics.model import Access, ObjectTypeSupport, Restrictions
from ace_epics.validation import validate
from ace_epics.values import BooleanValue, ObjectIdentifierValue
from tests.validation.conftest import enumeration, group, integer, set_value, token


def result(document, provider, rule):
    return validate(document, provider, rules=[rule]).results[0]


def test_seed04_unset_analog_input_bit_with_retained_section(document, provider):
    document.object_types.append(ObjectTypeSupport(name=token("analog-input")))
    original = provider.bibb
    provider.bibb = lambda n: (
        BibbDefinition(object_types=["analog-input"]) if n == "ds-rp-b" else original(n)
    )
    report = validate(document, provider, rules=["C5-06", "C5-03"])
    assert [r.outcome for r in report.results] == ["fail", "fail"]
    assert report.results[1].diagnostics[0].caused_by == ["C5-06"]


def test_seed06_initiate_only_b_side_service(document, provider):
    document.services[0].initiate = True
    document.services[0].execute = False
    assert result(document, provider, "C5-04").outcome == "fail"


def test_seed07_extra_object_list_entry(document, provider):
    document.device.property("object-list").value.elements.append(
        ObjectIdentifierValue(object_type=token("analog-value"), instance=3)
    )
    assert result(document, provider, "C5-08").outcome == "fail"


def test_seed12_revision_five_property_list_introduction(document):
    set_value(document.device, "protocol-revision", integer(5))
    diagnostics = result(document, JsonKnowledgeProvider(), "C5-10").diagnostics
    assert any(d.property == "property-list" and d.severity == Severity.ERROR for d in diagnostics)


@pytest.mark.parametrize("offset,expected", [(-1, "fail"), (0, "pass"), (1, "fail")])
def test_seed16_revision_fourteen_service_vector_length(document, provider, offset, expected):
    set_value(document.device, "protocol-revision", integer(14))
    length = provider.services_bit_count(14)
    assert length is not None
    set_value(
        document.device,
        "protocol-services-supported",
        group([BooleanValue(value=False) for _ in range(length + offset)]),
    )
    assert result(document, provider, "C5-13").outcome == expected


def test_seed19_revision_fifteen_property_list_membership_and_order(document, provider):
    set_value(document.device, "protocol-revision", integer(15))
    for obj in document.objects:
        obj.property("property-list").value.elements.reverse()
    assert result(document, provider, "C5-16").outcome == "pass"
    document.device.property("property-list").value.elements.pop()
    assert result(document, provider, "C5-16").outcome == "fail"
    document.device.property("property-list").value.elements.append(enumeration("object-name"))
    assert result(document, provider, "C5-16").outcome == "fail"


@pytest.mark.parametrize("segmentation", ["segmented-transmit", "no-segmentation"])
def test_seed21_segmentation_without_receiving(document, provider, segmentation):
    set_value(document.device, "segmentation-supported", enumeration(segmentation))
    set_value(document.device, "max-segments-accepted", integer(1))
    assert result(document, provider, "C5-17").outcome == "pass"


def test_seed26_datatype_default_restrictions_are_validated(document, provider):
    obj = document.objects[1]
    assert obj.property("present-value").access == Access.W
    assert obj.property("present-value").restrictions is None
    document.default_restrictions.real = Restrictions(maximum=integer(101))
    assert result(document, provider, "C5-20").outcome == "fail"
    document.default_restrictions.real.maximum = integer(100)
    assert result(document, provider, "C5-20").outcome == "pass"


def test_seed27_missing_internal_processing_timer_warns(document):
    from ace_epics.codecs.epics import dumps, parse

    result = parse(dumps(document))
    assert any(
        d.code == "P-TIMERS-INCOMPLETE" and "internal_processing_fail_time" in d.message
        for d in result.diagnostics
    )


def test_seed31_absent_device_has_one_root_error(document, provider):
    document.objects.pop(0)
    report = validate(document, provider)
    errors = [d for d in report.diagnostics if d.severity == Severity.ERROR]
    assert [d.code for d in errors] == ["S-02"]
