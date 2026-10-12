"""Sourced Clause12 property consistency checks (135.1 Clause 5(i),(j),(m),(p)-(r))."""

from collections.abc import Iterable
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from ace_epics.diagnostics import Diagnostic
from ace_epics.model import Access
from ace_epics.validation.query import primitive

from . import name, property_names, scalar

if TYPE_CHECKING:
    from ..engine import Context
    from . import ConsistencyRule


def condition(ctx: "Context", obj: Any, data: dict[str, Any]) -> bool | None:
    """Resolve EPICS facts for Clause 5(j); external implementation features stay unknown."""
    properties = property_names(obj)
    results: list[bool | None] = []
    if "commandable" in data:
        results.append(("priority-array" in properties) == data["commandable"])
    if "feature" in data:
        results.append(None)
    if "service" in data or "services_any" in data:
        services = data.get("services_any", [data.get("service")])
        direction = data.get("direction", "execute")
        results.append(
            any(
                name(service.name) in services and getattr(service, direction, False)
                for service in ctx.document.services
            )
        )
    if data.get("kind") in {"only_if_any_present", "required_if_any_present"}:
        results.append(bool(set(data["properties"]) & properties))
    if "any_presence" in data:
        results.append(bool(set(data["any_presence"]) & properties))
    if "property" in data:
        prop = data["property"]
        if data["kind"] == "required_if_present":
            results.append(prop in properties)
        else:
            value = scalar(ctx, obj, prop)
            if value is None or data.get("initialized"):
                results.append(None)
            elif "equals" in data:
                results.append(value == data["equals"])
    if False in results:
        return False
    return None if not results or None in results else True


def bounds(spec_range: dict[str, Any], ctx: "Context", obj: Any) -> tuple[Any, Any]:
    """Resolve constant/property-relative standard range endpoints (5(q),(r))."""
    if spec_range.get("equals_object_instance"):
        return obj.identifier.instance, obj.identifier.instance
    minimum = spec_range.get("min")
    maximum = spec_range.get("max")
    if "min_property" in spec_range:
        minimum = scalar(ctx, obj, spec_range["min_property"])
    if "max_property" in spec_range:
        maximum = scalar(ctx, obj, spec_range["max_property"])
    return minimum, maximum


def numeric(value: Any) -> bool:
    """Boolean values do not count as numeric range endpoints (5(q))."""
    return isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)


def check(rule: "ConsistencyRule", ctx: "Context") -> Iterable[Diagnostic]:
    """Evaluate revision-specific property definitions for Clause 5(i),(j),(m),(p)-(r)."""
    revision = ctx.query.protocol_revision
    for obj in ctx.document.objects:
        identifier = str(obj.identifier)
        definition = ctx.provider.object_definition(name(obj.object_type), revision)
        historical_partial = False
        if definition is None and rule.id in {"C5-10", "C5-15"}:
            definition = ctx.provider.object_definition(name(obj.object_type), None)
            historical_partial = definition is not None
        if definition is None:
            yield rule.skipped(
                f"Object definition unavailable for {obj.object_type} at revision {revision}"
            )
            continue
        present = property_names(obj)
        if historical_partial:
            yield rule.skipped(
                f"Only verified lifecycle facts available for {obj.object_type} "
                f"at revision {revision}"
            )
        elif rule.id == "C5-10":
            standard_names = set(ctx.provider.property_identifiers())
            for undefined in sorted((present & standard_names) - set(definition.properties)):
                yield rule.finding(
                    f"Standard property {undefined} is not defined for {obj.object_type}",
                    object_id=identifier,
                    prop=undefined,
                )
        specs = definition.properties
        if rule.id == "C5-15":
            specs = {**definition.historical_properties, **specs}
        for prop, spec in specs.items():
            entry = ctx.query._entry(obj, prop)
            value = scalar(ctx, obj, prop)
            if prop == "object-name":
                value = obj.name
            elif prop == "object-type":
                value = name(obj.object_type)
            elif prop == "object-identifier":
                value = obj.identifier
            exists = prop in present
            if rule.id == "C5-09":
                if spec.requirement == "required" and not exists:
                    yield rule.finding(
                        f"Required property {prop} is missing", object_id=identifier, prop=prop
                    )
            elif rule.id == "C5-10" and exists:
                if revision is None:
                    yield rule.skipped(
                        "Protocol_Revision absent; property introduction cannot be checked"
                    )
                elif spec.introduced_rev is not None and revision < spec.introduced_rev:
                    yield rule.finding(
                        f"{prop} was introduced at revision {spec.introduced_rev}",
                        object_id=identifier,
                        prop=prop,
                    )
            elif rule.id == "C5-15" and exists:
                if revision is None:
                    yield rule.skipped("Protocol_Revision absent; lifecycle cannot be checked")
                else:
                    for transition in (spec.deprecated_rev, spec.removed_rev):
                        if transition is not None and revision > transition:
                            yield rule.finding(
                                f"{prop} is unavailable after revision {transition}",
                                object_id=identifier,
                                prop=prop,
                            )
                            break
            elif rule.id == "C5-11":
                for data in spec.conditions:
                    kind = data["kind"]
                    if kind in {
                        "required_if",
                        "required_if_present",
                        "only_if",
                        "only_if_any_present",
                        "required_if_any_present",
                    }:
                        applies = condition(ctx, obj, data)
                        if applies is None:
                            if (kind.startswith("only_if") and exists) or (
                                not kind.startswith("only_if") and not exists
                            ):
                                yield rule.skipped(f"Cannot determine condition for {prop}: {data}")
                        elif (kind.startswith("only_if") and exists and not applies) or (
                            not kind.startswith("only_if") and applies and not exists
                        ):
                            yield rule.finding(
                                f"Conditional presence requirement for {prop} is unsatisfied",
                                object_id=identifier,
                                prop=prop,
                            )
                    elif kind == "requires_property" and exists and data["property"] not in present:
                        yield rule.finding(
                            f"{prop} requires {data['property']}", object_id=identifier, prop=prop
                        )
                    elif kind == "all_or_none":
                        group = set(data["properties"])
                        if group & present and not group <= present:
                            yield rule.finding(
                                f"Properties must occur together: {sorted(group)}",
                                object_id=identifier,
                                prop=prop,
                            )
                    elif kind == "at_least_one" and not set(data["properties"]) & present:
                        yield rule.finding(
                            f"At least one of {data['properties']} is required",
                            object_id=identifier,
                            prop=prop,
                        )
            elif rule.id == "C5-12" and entry is not None:
                if spec.access in {"W", "C"} and entry.access == Access.R:
                    yield rule.finding(
                        f"{prop} must be marked writable or conditionally writable",
                        object_id=identifier,
                        prop=prop,
                    )
            elif rule.id == "C5-18" and exists:
                read_only = spec.read_only
                for data in spec.conditions:
                    if data["kind"] == "read_only_if":
                        applies = condition(ctx, obj, data)
                        if applies is None:
                            if entry is not None and entry.access != Access.R:
                                yield rule.skipped(f"Cannot resolve read-only condition for {prop}")
                        else:
                            read_only |= applies
                if read_only and entry is not None and entry.access != Access.R:
                    yield rule.finding(f"{prop} must be read-only", object_id=identifier, prop=prop)
            elif rule.id == "C5-19" and exists and spec.range:
                node = ctx.query.value(obj, prop)
                if node is not None and node.kind == "unspecified":
                    continue
                if (
                    node is not None
                    and node.kind == "null"
                    and (numeric(spec.range.get("min")) or numeric(spec.range.get("max")))
                ):
                    yield rule.finding(
                        f"{prop} NULL is outside the standard numeric range",
                        object_id=identifier,
                        prop=prop,
                    )
                    continue
                minimum, maximum = bounds(spec.range, ctx, obj)
                if ("max_property" in spec.range and maximum is None) or (
                    "min_property" in spec.range and minimum is None
                ):
                    yield rule.skipped(f"Standard range for {prop} depends on unspecified property")
                if numeric(value) and (
                    (numeric(minimum) and value < minimum) or (numeric(maximum) and value > maximum)
                ):
                    yield rule.finding(
                        f"{prop} value {value} is outside standard range {minimum}..{maximum}",
                        object_id=identifier,
                        prop=prop,
                    )
                if isinstance(value, list):
                    low, high = spec.range.get("element_min"), spec.range.get("element_max")
                    if any(
                        numeric(v) and ((numeric(low) and v < low) or (numeric(high) and v > high))
                        for v in value
                    ):
                        yield rule.finding(
                            f"{prop} contains an element outside {low}..{high}",
                            object_id=identifier,
                            prop=prop,
                        )
                if isinstance(value, (str, bytes, list)) and (
                    len(value) < spec.range.get("min_length", 0)
                    or ("max_length" in spec.range and len(value) > spec.range["max_length"])
                ):
                    yield rule.finding(
                        f"{prop} length violates standard limits", object_id=identifier, prop=prop
                    )
            elif rule.id == "C5-20" and entry is not None:
                limits = ctx.query.limits(obj, prop)
                lo, hi = primitive(limits.minimum), primitive(limits.maximum)
                if numeric(lo) and numeric(hi) and lo > hi:
                    yield rule.finding(
                        f"{prop} restriction minimum exceeds maximum",
                        object_id=identifier,
                        prop=prop,
                    )
                for standard, minimum_required in ((spec.range, False), (spec.min_range, True)):
                    if not standard:
                        continue
                    std_lo, std_hi = bounds(standard, ctx, obj)
                    if any(
                        f"{key}_property" in standard and endpoint is None
                        for key, endpoint in (("min", std_lo), ("max", std_hi))
                    ):
                        yield rule.skipped(
                            f"Restriction range for {prop} depends on unspecified property"
                        )
                    outside = (
                        numeric(lo)
                        and numeric(std_lo)
                        and (lo > std_lo if minimum_required else lo < std_lo)
                    ) or (
                        numeric(hi)
                        and numeric(std_hi)
                        and (hi < std_hi if minimum_required else hi > std_hi)
                    )
                    lengths = [
                        length
                        for length in (
                            limits.maximum_length_string,
                            limits.maximum_length_list,
                            limits.maximum_length_array,
                        )
                        if length is not None
                    ]
                    if not minimum_required and "min_length" in standard:
                        outside |= any(length < standard["min_length"] for length in lengths)
                    length_limit = standard.get("max_length")
                    if length_limit is not None:
                        outside |= any(
                            length < length_limit if minimum_required else length > length_limit
                            for length in lengths
                        )
                    resolution = primitive(limits.resolution)
                    required_step = standard.get("step") if minimum_required else None
                    if numeric(resolution) and numeric(required_step):
                        if resolution <= 0:
                            outside = True
                        else:
                            ratio = Decimal(str(required_step)) / Decimal(str(resolution))
                            outside |= ratio != ratio.to_integral_value()
                            if numeric(lo) and numeric(std_lo):
                                offset = (Decimal(str(std_lo)) - Decimal(str(lo))) / Decimal(
                                    str(resolution)
                                )
                                outside |= offset != offset.to_integral_value()
                    maximum_resolution = standard.get("max_resolution")
                    if numeric(resolution) and numeric(maximum_resolution):
                        outside |= resolution > maximum_resolution
                    if outside:
                        yield rule.finding(
                            f"{prop} restriction "
                            + (
                                "excludes minimum required range"
                                if minimum_required
                                else "exceeds standard range"
                            ),
                            object_id=identifier,
                            prop=prop,
                        )
