"""Independent review cases for conditional knowledge and declared restrictions."""

from ace_epics.knowledge import BibbDefinition, ObjectDefinition, PropertySpec, ServiceRequirement
from ace_epics.model import Bibb, Restrictions
from ace_epics.validation import Context, Query, validate
from ace_epics.validation.rules.bibbs import resolve
from ace_epics.values import UnspecifiedValue
from tests.validation.conftest import entry, integer, set_value


def result(document, provider, rule):
    return validate(document, provider, rules=[rule]).results[0]


def custom_bibbs(document, provider, definitions):
    document.bibbs = [Bibb.model_validate("CUSTOM-A")]
    provider.bibb = lambda name: definitions.get(name)


def test_conditional_dependencies_keep_alternatives_and_terminate_cycles(document, provider):
    custom_bibbs(
        document,
        provider,
        {
            "custom-a": BibbDefinition(
                conditional_requirements=[
                    {
                        "condition": {"kind": "protocol_revision_at_least", "revision": 7},
                        "requires_bibbs": ["CUSTOM-B"],
                    }
                ]
            ),
            "custom-b": BibbDefinition(
                requires_bibbs=["CUSTOM-A"],
                object_type_alternatives=[["file", "calendar"]],
                service_alternatives=[[{"name": "write-property", "execute": True}]],
            ),
        },
    )
    definition = resolve(Context(document, provider), "CUSTOM-A")
    assert definition is not None
    assert definition.object_type_alternatives == [["file", "calendar"]]
    assert result(document, provider, "C5-01").outcome == "fail"
    assert result(document, provider, "C5-04").outcome == "fail"
    assert result(document, provider, "C5-05").outcome == "fail"


def test_service_conditions_are_conjunctions_and_unknown_execution_does_not_pass(
    document, provider
):
    custom_bibbs(
        document,
        provider,
        {
            "custom-a": BibbDefinition(
                services=[
                    ServiceRequirement(
                        name="write-property",
                        execute=True,
                        conditions=[{"kind": "service_parameter_used"}],
                    )
                ]
            ),
        },
    )
    assert result(document, provider, "C5-05").outcome == "skipped"
    provider.bibb = lambda name: BibbDefinition(
        services=[
            ServiceRequirement(
                name="write-property",
                execute=True,
                conditions=[{"kind": "protocol_revision_at_least", "revision": 7}],
            )
        ]
    )
    assert result(document, provider, "C5-05").outcome == "fail"


def test_executed_service_alternatives_false_unknown_and_true(document, provider):
    from ace_epics.values import BooleanValue

    custom_bibbs(
        document,
        provider,
        {
            "custom-a": BibbDefinition(
                service_alternatives=[
                    [
                        {"name": "confirmed-cov-notification", "execute": True},
                        {"name": "unconfirmed-cov-notification", "execute": True},
                    ]
                ]
            ),
        },
    )
    assert result(document, provider, "C5-05").outcome == "fail"
    bits = document.device.property("protocol-services-supported").value.elements
    position = provider.services(30)["confirmed-cov-notification"]
    bits[position] = UnspecifiedValue()
    assert result(document, provider, "C5-05").outcome == "skipped"
    bits[position] = BooleanValue(value=True)
    assert result(document, provider, "C5-05").outcome == "pass"
    provider.services = lambda revision: {}
    assert result(document, provider, "C5-05").outcome == "skipped"


def specs(provider, properties):
    provider.object_definition = lambda object_type, revision: ObjectDefinition(
        source="review synthetic facts",
        object_type=object_type,
        revision=30,
        properties=properties,
    )


def test_relative_restriction_bounds_unknown_then_resolved(document, provider):
    specs(
        provider,
        {
            "present-value": PropertySpec(
                requirement="optional",
                datatype="Unsigned",
                range={"min": 1, "max_property": "number-of-states"},
            )
        },
    )
    obj = document.objects[1]
    obj.property("present-value").restrictions = Restrictions(maximum=integer(11))
    assert result(document, provider, "C5-20").outcome == "skipped"
    set_value(obj, "number-of-states", integer(10))
    assert result(document, provider, "C5-20").outcome == "fail"
    obj.property("present-value").restrictions = None
    from ace_epics.validation.query import primitive

    assert primitive(Query(document, provider).limits(obj, "present-value").maximum) == 10
    assert result(document, provider, "C5-20").outcome == "pass"


def test_length_resolution_and_inverted_restrictions(document, provider):
    specs(
        provider,
        {
            "present-value": PropertySpec(
                requirement="optional",
                datatype="CharacterString",
                range={"max_length": 20, "max_resolution": 2},
                min_range={"max_length": 10},
            )
        },
    )
    obj = document.objects[1]
    assert Query(document, provider).limits(obj, "present-value").maximum_length_string == 20
    prop = obj.property("present-value")
    prop.restrictions = Restrictions(maximum_length_string=21)
    assert result(document, provider, "C5-20").outcome == "fail"
    prop.restrictions = Restrictions(maximum_length_string=9)
    assert result(document, provider, "C5-20").outcome == "fail"
    prop.restrictions = Restrictions(maximum_length_string=15, resolution=integer(3))
    assert result(document, provider, "C5-20").outcome == "fail"
    prop.restrictions = Restrictions(minimum=integer(2), maximum=integer(1))
    assert result(document, provider, "C5-20").outcome == "fail"


def test_property_list_allows_unlisted_numeric_proprietary_properties(document, provider):
    obj = document.objects[1]
    obj.property("property-list").value.elements.append(integer(700))
    assert result(document, provider, "C5-16").outcome == "pass"
    obj.properties.append(entry("vendor-counter", integer(3)))
    assert result(document, provider, "C5-16").outcome == "skipped"
    obj.property("property-list").value.elements.append(integer(700))
    assert result(document, provider, "C5-16").outcome == "fail"


def test_required_object_unspecified_bit_is_not_false(document, provider):
    custom_bibbs(document, provider, {"custom-a": BibbDefinition(object_types=["device"])})
    bits = document.device.property("protocol-object-types-supported").value.elements
    bits[provider.object_types(30)["device"]] = UnspecifiedValue()
    assert result(document, provider, "C5-03").outcome == "skipped"


def test_provider_effective_bibb_preserves_dependency_alternatives_and_conditions(provider):
    definitions = {
        "custom-a": BibbDefinition(requires_bibbs=["CUSTOM-B"]),
        "custom-b": BibbDefinition(
            service_alternatives=[[{"name": "write-property", "execute": True}]],
            bibb_alternatives=[["DM-TS-B", "DM-UTC-B"]],
            services=[
                ServiceRequirement(
                    name="read-property",
                    execute=True,
                    conditions=[{"kind": "protocol_revision_at_least", "revision": 7}],
                )
            ],
        ),
    }
    provider.bibb = lambda name: definitions.get(name.lower())
    definition = provider.effective_bibb("CUSTOM-A")
    assert definition is not None
    for key in ("service_alternatives", "bibb_alternatives"):
        assert definition.model_dump()[key] == definitions["custom-b"].model_dump()[key]
    condition = definition.conditional_requirements[0]
    assert condition["condition"] == {
        "kind": "all",
        "conditions": [{"kind": "protocol_revision_at_least", "revision": 7}],
    }
    assert condition["services"][0]["conditions"] == []


def test_object_alternative_unspecified_bit_cannot_prove_failure(document, provider):
    custom_bibbs(
        document,
        provider,
        {
            "custom-a": BibbDefinition(object_type_alternatives=[["file", "calendar"]]),
        },
    )
    bits = document.device.property("protocol-object-types-supported").value.elements
    bits[provider.object_types(30)["file"]] = UnspecifiedValue()
    assert result(document, provider, "C5-03").outcome == "skipped"


def test_annex_k_cov_multiple_requires_one_notification_execution_bit(document, provider):
    document.bibbs = [Bibb.model_validate("DS-COVM-A")]
    assert result(document, provider, "C5-05").outcome == "fail"
    from ace_epics.values import BooleanValue

    bits = document.device.property("protocol-services-supported").value.elements
    bits[provider.services(30)["unconfirmed-cov-notification-multiple"]] = BooleanValue(value=True)
    # Required alternative is satisfied, but the confirmed/unconfirmed request
    # parameter is external evidence and its conditional obligation stays unknown.
    assert result(document, provider, "C5-05").outcome == "skipped"


def test_declared_capabilities_gate_custom_rule_without_running_check(document, provider):
    from dataclasses import dataclass

    from tests.validation.test_engine import CustomRule

    @dataclass
    class CapabilityRule(CustomRule):
        requires: frozenset[str] = frozenset({"custom-table"})

        def check(self, ctx):
            raise AssertionError("Unavailable capability must prevent evaluation")

    report = validate(document, provider, rules=[CapabilityRule()])
    assert report.results[0].outcome == "skipped"
    assert "custom-table" in report.diagnostics[0].message


def test_custom_capability_and_legacy_provider_remain_extensible(document, provider):
    from typing import cast

    from ace_epics.knowledge import KnowledgeProvider
    from tests.validation.test_engine import CustomRule

    rule = CustomRule(requires=frozenset({"custom-table"}))
    provider.capabilities = lambda: frozenset({"custom-table"})
    assert validate(document, provider, rules=[rule]).results[0].outcome == "pass"

    class LegacyProvider:
        def __getattr__(self, name):
            if name == "capabilities":
                raise AttributeError(name)
            return getattr(provider, name)

    assert (
        validate(document, cast(KnowledgeProvider, LegacyProvider()), rules=[rule])
        .results[0]
        .outcome
        == "pass"
    )


def test_capabilities_describe_families_not_complete_revision_coverage(document, provider):
    from ace_epics.knowledge import JsonKnowledgeProvider, NullProvider

    shipped = JsonKnowledgeProvider()
    assert {"bibbs", "objects", "services", "object_types"} <= shipped.capabilities()
    assert not NullProvider().capabilities()
    document.bibbs = []
    # An empty claim section cannot hide an explicitly absent required table.
    assert result(document, NullProvider(), "C5-01").outcome == "skipped"
    # Instance consistency is self-contained even with no external capabilities.
    assert result(document, NullProvider(), "C5-07").outcome == "pass"
    document.objects.pop()
    assert result(document, NullProvider(), "C5-07").outcome == "fail"
    set_value(document.device, "protocol-revision", integer(999))
    finding = result(document, shipped, "C5-06")
    assert finding.outcome == "skipped"
    assert "enumeration unavailable" in finding.diagnostics[0].message


def test_custom_json_provider_advertises_only_available_tables(tmp_path):
    import json

    from ace_epics.knowledge import JsonKnowledgeProvider

    provider = JsonKnowledgeProvider(tmp_path)
    assert not provider.capabilities()
    (tmp_path / "services.json").write_text(
        json.dumps(
            {
                "source": "review synthetic data",
                "revision": 30,
                "values": {"read-property": 12},
            }
        )
    )
    # A fresh loader sees newly supplied tables; existing instances cache reads.
    assert JsonKnowledgeProvider(tmp_path).capabilities() == frozenset({"services"})
