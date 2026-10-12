"""Conditional facts are checked when known and reported when unresolved."""

from ace_epics.knowledge import BibbDefinition, ObjectDefinition, PropertySpec
from ace_epics.model import Bibb
from ace_epics.validation import validate
from ace_epics.validation.rules.bibbs import applicable
from tests.validation.conftest import entry, group, integer, set_value, token


def result(doc, provider, rule):
    return validate(doc, provider, rules=[rule]).results[0]


def spec_provider(provider, properties):
    provider.object_definition = lambda type_name, revision: ObjectDefinition(
        source="synthetic", object_type=type_name, revision=30, properties=properties
    )


def test_object_condition_groups_and_known_property_values(document, provider):
    spec_provider(
        provider,
        {
            "dependent": PropertySpec(
                requirement="conditional",
                datatype="Integer",
                conditions=[{"kind": "required_if", "property": "enabled", "equals": True}],
            ),
            "a": PropertySpec(
                requirement="conditional",
                datatype="Integer",
                conditions=[{"kind": "all_or_none", "properties": ["a", "b"]}],
            ),
            "choice": PropertySpec(
                requirement="conditional",
                datatype="Integer",
                conditions=[{"kind": "at_least_one", "properties": ["choice", "other"]}],
            ),
            "parent": PropertySpec(
                requirement="optional",
                datatype="Integer",
                conditions=[{"kind": "requires_property", "property": "child"}],
            ),
        },
    )
    from ace_epics.values import BooleanValue

    for obj in document.objects:
        obj.properties.extend(
            [entry("enabled", BooleanValue(value=False)), entry("choice", integer(1))]
        )
    assert result(document, provider, "C5-11").outcome == "pass"
    document.objects[1].properties.append(entry("a", integer(1)))
    assert result(document, provider, "C5-11").outcome == "fail"
    document.objects[1].properties.append(entry("b", integer(2)))
    document.objects[1].properties.append(entry("parent", integer(1)))
    assert "parent requires child" in result(document, provider, "C5-11").diagnostics[0].message
    document.objects[1].properties.append(entry("child", integer(1)))
    set_value(document.objects[1], "enabled", BooleanValue(value=True))
    assert result(document, provider, "C5-11").outcome == "fail"


def test_unknown_conditions_cannot_pass_missing_obligations(document, provider):
    spec_provider(
        provider,
        {
            "feature-property": PropertySpec(
                requirement="conditional",
                datatype="Integer",
                conditions=[{"kind": "required_if", "feature": "implementation-feature"}],
            ),
        },
    )
    assert result(document, provider, "C5-11").outcome == "skipped"
    for obj in document.objects:
        obj.properties.append(entry("feature-property", integer(1)))
    assert result(document, provider, "C5-11").outcome == "pass"


def test_minimum_readable_does_not_mean_mandatory_read_only(document, provider):
    spec_provider(
        provider,
        {
            "present-value": PropertySpec(requirement="optional", datatype="Integer", access="R"),
        },
    )
    assert result(document, provider, "C5-18").outcome == "pass"
    spec_provider(
        provider,
        {
            "present-value": PropertySpec(
                requirement="optional",
                datatype="Integer",
                access="R",
                conditions=[{"kind": "read_only_if", "property": "enabled", "equals": True}],
            ),
        },
    )
    from ace_epics.values import BooleanValue

    set_value(document.objects[1], "enabled", BooleanValue(value=True))
    assert result(document, provider, "C5-18").outcome == "fail"


def test_dynamic_standard_bounds_and_constructed_element_ranges(document, provider):
    spec_provider(
        provider,
        {
            "present-value": PropertySpec(
                requirement="optional",
                datatype="Unsigned",
                range={"min": 1, "max_property": "number-of-states"},
            ),
            "priority": PropertySpec(
                requirement="optional",
                datatype="BACnetARRAY",
                range={"element_min": 1, "element_max": 16},
            ),
        },
    )
    assert result(document, provider, "C5-19").outcome == "skipped"
    set_value(document.objects[1], "number-of-states", integer(10))
    assert result(document, provider, "C5-19").outcome == "fail"
    set_value(document.objects[1], "present-value", integer(5))
    set_value(document.objects[1], "priority", group([integer(0), integer(17)]))
    assert result(document, provider, "C5-19").outcome == "fail"


def test_bibb_explicit_revision_conditions_and_service_alternative(document, provider):
    document.bibbs = [Bibb.model_validate("DM-TM-A")]
    assert result(document, provider, "C5-04").outcome == "fail"
    from ace_epics.model import ServiceSupport

    document.services.append(
        ServiceSupport(name=token("unconfirmed-text-message"), initiate=True, execute=False)
    )
    assert result(document, provider, "C5-04").outcome == "pass"
    document.bibbs = [Bibb.model_validate("NM-RC-B")]
    assert result(document, provider, "C5-01").outcome == "fail"  # revision>=17 requiresNetworkPort
    set_value(document.device, "protocol-revision", integer(16))
    assert result(document, provider, "C5-01").outcome == "pass"


def test_bibb_external_service_parameters_stay_unknown(document, provider):
    document.bibbs = [Bibb.model_validate("DS-COV-A")]
    from ace_epics.model import ServiceSupport

    document.services.append(
        ServiceSupport(name=token("subscribe-cov"), initiate=True, execute=False)
    )
    assert result(document, provider, "C5-04").outcome == "skipped"
    # No local object requirements are introduced by the unknown service parameter.
    assert result(document, provider, "C5-01").outcome == "pass"


def test_boolean_composite_bibb_conditions(document, provider):
    from ace_epics.validation import Context

    ctx = Context(document, provider)
    missing = {"kind": "object_type_supported", "object_type": "file"}
    known = {"kind": "object_type_supported", "object_type": "device"}
    unknown = {"kind": "service_parameter_used"}
    assert applicable(ctx, {"kind": "any", "conditions": [known, unknown]}) is True
    assert applicable(ctx, {"kind": "any", "conditions": [missing, unknown]}) is None
    assert applicable(ctx, {"kind": "all", "conditions": [missing, unknown]}) is False
    assert applicable(ctx, {"kind": "all", "conditions": [known, unknown]}) is None
    assert (
        applicable(ctx, {"kind": "writable_property_present", "property": "present-value"}) is True
    )


def test_unknown_bibb_and_dependency_explicitly_skipped(document, provider):
    document.bibbs = [Bibb.model_validate("CUSTOM-X-A")]
    assert result(document, provider, "C5-04").outcome == "skipped"
    original = provider.bibb
    provider.bibb = lambda n: (
        BibbDefinition(requires_bibbs=["MISSING-B"]) if n == "ds-rp-b" else original(n)
    )
    document.bibbs = [Bibb.model_validate("DS-RP-B")]
    assert result(document, provider, "C5-04").outcome == "skipped"


def test_declared_service_conditions_and_any_present_groups(document, provider):
    from ace_epics.model import ServiceSupport
    from ace_epics.validation import Context
    from ace_epics.validation.rules.objects import condition
    from tests.validation.conftest import token

    ctx = Context(document, provider)
    obj = document.device
    data = {"kind": "required_if", "service": "subscribe-cov", "direction": "execute"}
    assert condition(ctx, obj, data) is False
    document.services.append(ServiceSupport(name=token("subscribe-cov"), execute=True))
    assert condition(ctx, obj, data) is True
    assert condition(ctx, obj, {**data, "direction": "initiate"}) is False
    assert condition(ctx, obj, {**data, "feature": "external"}) is None
    assert (
        condition(
            ctx,
            obj,
            {
                "kind": "only_if",
                "services_any": ["read-property", "unknown"],
                "direction": "execute",
            },
        )
        is True
    )
    assert (
        condition(
            ctx, obj, {"kind": "only_if_any_present", "properties": ["object-list", "unknown"]}
        )
        is True
    )
    assert (
        condition(ctx, obj, {"kind": "required_if_any_present", "properties": ["unknown"]}) is False
    )
    assert condition(ctx, obj, {"kind": "only_if", "any_presence": ["object-list"]}) is True


def test_historical_object_instance_range_and_required_write_grid(document, provider):
    from ace_epics.knowledge import PropertySpec
    from ace_epics.model import Restrictions
    from ace_epics.validation import Query, validate
    from tests.validation.conftest import SyntheticProvider, integer, set_value

    class SourcedRanges(SyntheticProvider):
        def object_definition(self, object_type, revision):
            definition = super().object_definition(object_type, revision)
            assert definition is not None
            if object_type == "analog-output":
                definition.properties["present-value"] = PropertySpec(
                    requirement="required", datatype="Real", range={"equals_object_instance": True}
                )
            return definition

    obj = document.objects[1]
    set_value(obj, "present-value", integer(obj.identifier.instance + 1))
    knowledge = SourcedRanges()
    assert validate(document, knowledge, rules=["C5-19"]).results[0].outcome == "fail"
    limits = Query(document, knowledge).limits(obj, "present-value")
    assert limits.minimum == limits.maximum == integer(obj.identifier.instance)
    set_value(obj, "present-value", integer(obj.identifier.instance))
    assert validate(document, knowledge, rules=["C5-19"]).results[0].outcome == "pass"

    original = provider.object_definition

    def grid(object_type, revision):
        definition = original(object_type, revision)
        assert definition is not None
        if object_type == "analog-output":
            definition.properties["present-value"] = definition.properties[
                "present-value"
            ].model_copy(update={"min_range": {"min": 10, "max": 90, "step": 15}})
        return definition

    provider.object_definition = grid
    obj.property("present-value").restrictions = Restrictions(resolution=integer(10))
    assert validate(document, provider, rules=["C5-20"]).results[0].outcome == "fail"
    obj.property("present-value").restrictions.resolution = integer(5)
    assert validate(document, provider, rules=["C5-20"]).results[0].outcome == "pass"
