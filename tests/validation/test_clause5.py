"""Clause5 tests use independent mutations and preserve revision/unspecified semantics."""

import pytest

from ace_epics.diagnostics import Severity
from ace_epics.knowledge import BibbDefinition, NullProvider
from ace_epics.model import Access, ObjectTypeSupport, Restrictions
from ace_epics.validation import RULES, validate
from ace_epics.values import UnspecifiedValue
from tests.validation.conftest import entry, enumeration, group, integer, set_value, token


def outcome(document, provider, rule):
    return validate(document, provider, rules=[rule]).results[0]


@pytest.mark.parametrize("rule", [r.id for r in RULES])
def test_independent_baseline_passes_every_rule(document, provider, rule):
    result = outcome(document, provider, rule)
    assert result.outcome == "pass", result.diagnostics


@pytest.mark.parametrize("rule", [r.id for r in RULES if r.requires])
def test_missing_knowledge_is_skipped(document, rule):
    result = outcome(document, NullProvider(), rule)
    # C5-07 uses names directly and does not require an enumeration table.
    assert result.outcome == ("pass" if rule == "C5-07" else "skipped")


@pytest.mark.parametrize(
    "rule,mutation",
    [
        ("C5-04", lambda d: setattr(d.services[0], "execute", False)),
        ("C5-05", lambda d: set_value(d.device, "protocol-services-supported", group([]))),
        ("C5-06", lambda d: d.object_types.pop()),
        ("C5-07", lambda d: d.objects.pop()),
        ("C5-08", lambda d: set_value(d.device, "object-list", group([]))),
        ("C5-09", lambda d: d.objects[1].properties.pop(0)),
        (
            "C5-10",
            lambda d: (
                set_value(d.device, "protocol-revision", integer(29)),
                d.objects[1].properties.append(entry("new-property", integer(1))),
            ),
        ),
        ("C5-11", lambda d: d.objects[1].properties.append(entry("priority-array", group([])))),
        ("C5-12", lambda d: setattr(d.objects[1].properties[0], "access", Access.R)),
        ("C5-13", lambda d: set_value(d.device, "protocol-services-supported", group([]))),
        ("C5-14", lambda d: set_value(d.device, "protocol-object-types-supported", group([]))),
        ("C5-15", lambda d: d.objects[1].properties.append(entry("old-property", integer(1)))),
        ("C5-16", lambda d: set_value(d.device, "property-list", group([]))),
        ("C5-17", lambda d: set_value(d.device, "max-segments-accepted", integer(1))),
        ("C5-18", lambda d: setattr(d.device.property("property-list"), "access", Access.C)),
        ("C5-19", lambda d: set_value(d.objects[1], "present-value", integer(101))),
        (
            "C5-20",
            lambda d: setattr(
                d.objects[1].properties[0], "restrictions", Restrictions(minimum=integer(-1))
            ),
        ),
        ("S-01", lambda d: d.objects.append(d.objects[0])),
        ("S-02", lambda d: d.objects.pop(0)),
        ("S-03", lambda d: setattr(d.fail_times, "notification_fail_time", -1)),
        (
            "S-04",
            lambda d: setattr(
                d.objects[1].properties[0],
                "restrictions",
                Restrictions(minimum=enumeration("active")),
            ),
        ),
    ],
)
def test_rule_fails_on_targeted_mutation(document, provider, rule, mutation):
    mutation(document)
    result = outcome(document, provider, rule)
    assert result.outcome == "fail", result.diagnostics
    assert all(d.code == rule and d.clause for d in result.diagnostics)


@pytest.mark.parametrize("rule", ["C5-01", "C5-02", "C5-03"])
def test_bibb_local_object_requirements(document, provider, rule):
    original = provider.bibb
    provider.bibb = lambda n: (
        BibbDefinition(object_types=["analog-input"]) if n == "ds-rp-b" else original(n)
    )
    assert outcome(document, provider, rule).outcome == "fail"


def test_property_list_old_revision_not_applicable(document, provider):
    set_value(document.device, "protocol-revision", integer(13))
    assert outcome(document, provider, "C5-16").outcome == "not_applicable"
    document.device.properties.remove(document.device.property("protocol-revision"))
    assert outcome(document, provider, "C5-16").outcome == "not_applicable"


def test_deprecation_boundary_and_unspecified_range(document, provider):
    document.objects[1].properties.append(entry("old-property", integer(1)))
    set_value(document.device, "protocol-revision", integer(12))
    assert outcome(document, provider, "C5-15").outcome == "pass"
    set_value(document.device, "protocol-revision", integer(13))
    assert outcome(document, provider, "C5-15").outcome == "fail"
    set_value(document.objects[1], "present-value", UnspecifiedValue())
    assert outcome(document, provider, "C5-19").outcome == "pass"


def test_dynamic_file_exception_is_warning(document, provider):
    document.object_types.append(ObjectTypeSupport(name=token("file")))
    result = outcome(document, provider, "C5-07")
    assert result.outcome == "pass"
    assert result.diagnostics[0].severity == Severity.WARNING


def test_minimum_required_range_and_conditional_access(document, provider):
    prop = document.objects[1].properties[0]
    prop.restrictions = Restrictions(minimum=integer(20), maximum=integer(80))
    assert outcome(document, provider, "C5-20").outcome == "fail"
    prop.access = Access.C
    assert outcome(document, provider, "C5-12").outcome == "pass"


def test_dependency_cause_and_selection(document, provider):
    document.object_types.pop()
    report = validate(document, provider, rules=["C5-03", "C5-06"])
    assert [r.rule_id for r in report.results] == ["C5-06", "C5-03"]
    # Give C5-03 a concrete failed requirement explained by C5-06.
    original = provider.bibb
    provider.bibb = lambda n: (
        BibbDefinition(object_types=["analog-input"]) if n == "ds-rp-b" else original(n)
    )
    report = validate(document, provider, rules=["C5-03", "C5-06"])
    assert report.results[1].diagnostics[0].caused_by == ["C5-06"]
    with pytest.raises(KeyError):
        validate(document, provider, rules=["missing"])
    with pytest.raises(ValueError, match="unique"):
        validate(document, provider, rules=["S-01", "S-01"])
