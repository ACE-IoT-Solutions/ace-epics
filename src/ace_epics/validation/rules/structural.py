"""Structure, bit vectors, and self-contained consistency checks (Clause 5)."""

import math
from collections import Counter
from collections.abc import Iterable
from typing import TYPE_CHECKING

from ace_epics.diagnostics import Diagnostic, Severity

from . import name, scalar

if TYPE_CHECKING:
    from ..engine import Context
    from . import ConsistencyRule


def check(rule: "ConsistencyRule", ctx: "Context") -> Iterable[Diagnostic]:
    """Evaluate Tier0/1 checks without hiding unavailable facts (Clause 5)."""
    doc, query, provider = ctx.document, ctx.query, ctx.provider
    key = rule.id
    device = doc.device
    revision = query.protocol_revision
    if key == "S-01":
        counts = Counter(str(obj.identifier) for obj in doc.objects)
        for identifier, count in counts.items():
            if count > 1:
                yield rule.finding(
                    f"Duplicate identifier {identifier} ({count} objects)", object_id=identifier
                )
        return
    if key == "S-02":
        count = sum(name(obj.object_type) == "device" for obj in doc.objects)
        if count != 1:
            yield rule.finding(f"Expected one Device object; found {count}")
        return
    if key == "S-03":
        for timer, value in doc.fail_times.model_dump().items():
            values = value.items() if isinstance(value, dict) else [(timer, value)]
            for timer_name, seconds in values:
                if seconds is not None and (not math.isfinite(seconds) or seconds < 0):
                    yield rule.finding(f"{timer_name} must be finite and non-negative")
        return
    if key == "S-04":
        for obj in doc.objects:
            properties = [
                ctx.query._entry(obj, prop)
                for prop in sorted(
                    {entry.name.canonical for entry in obj.properties}
                    | {"object-name", "object-type", "object-identifier"}
                )
            ]
            for entry in properties:
                if entry is None or entry.restrictions is None or entry.value.kind == "unspecified":
                    continue
                for field in ("minimum", "maximum", "resolution"):
                    bound = getattr(entry.restrictions, field)
                    if bound is None:
                        continue
                    if bound.kind != entry.value.kind and not {bound.kind, entry.value.kind} <= {
                        "integer",
                        "real",
                    }:
                        yield rule.finding(
                            f"{field} datatype differs from {entry.name}",
                            object_id=str(obj.identifier),
                            prop=entry.name.canonical,
                        )
        return
    if key == "C5-07":
        for supported in doc.object_types:
            obj_name = name(supported.name)
            if obj_name == "device" and device is None:
                yield rule.skipped("Device instance unavailable; S-02 reports the root error")
                continue
            if not doc.objects_of_type(obj_name):
                yield rule.finding(
                    f"Supported type {obj_name} has no database instance",
                    severity=Severity.WARNING if obj_name == "file" else Severity.ERROR,
                )
        return
    if key == "C5-16":
        identifiers = provider.property_identifiers()
        reverse = {number: n for n, number in identifiers.items()}
        for obj in doc.objects:
            entries = scalar(ctx, obj, "property-list")
            if not isinstance(entries, list):
                yield rule.finding(
                    "Property_List must be present and specified",
                    object_id=str(obj.identifier),
                    prop="property-list",
                )
                continue
            actual = [
                reverse.get(v, f"proprietary-{v}") if type(v) is int else name(v) for v in entries
            ]
            expected = {entry.canonical for entry in query.expected_property_list(obj)}
            if any(type(v) is int and v < 512 and v not in reverse for v in entries):
                yield rule.skipped(
                    "Numeric Property_List identifiers need property enumeration data"
                )
                continue
            extra = set(actual) - expected
            # Clause 7.1.3 permits unlisted proprietary properties. Numeric IDs
            # cannot establish the identity of a vendor-named EPICS property.
            proprietary_extra = {
                reverse.get(v, f"proprietary-{v}")
                for v in entries
                if type(v) is int and v >= 512 and v not in reverse
            }
            missing = expected - set(actual)
            unidentified = missing - set(identifiers)
            if unidentified and proprietary_extra:
                yield rule.skipped(
                    "Vendor property names cannot be correlated with numeric Property_List IDs"
                )
                missing -= unidentified
            if len(actual) != len(set(actual)) or missing or extra - proprietary_extra:
                yield rule.finding(
                    f"Property_List differs: expected {sorted(expected)}, got {actual}",
                    object_id=str(obj.identifier),
                    prop="property-list",
                )
        return
    if device is None:
        yield rule.skipped("Device object unavailable; see S-02")
        return
    if key == "C5-08":
        listed = query.object_list
        if listed is None:
            yield rule.finding(
                "Object_List must be a specified list of object identifiers",
                object_id=str(device.identifier),
                prop="object-list",
            )
            return
        actual = [str(identifier) for identifier in listed]
        expected = [str(obj.identifier) for obj in doc.objects]
        if Counter(actual) != Counter(expected) or len(actual) != len(set(actual)):
            yield rule.finding(
                f"Object_List differs from database: listed {actual}, database {expected}",
                object_id=str(device.identifier),
                prop="object-list",
            )
    elif key == "C5-06":
        enumeration = provider.object_types(revision)
        bits = query.object_types_supported_bits
        if not enumeration:
            yield rule.skipped("Object-type enumeration unavailable for declared revision")
        elif bits is None or any(bit is None for bit in bits):
            yield rule.skipped("Protocol_Object_Types_Supported is unspecified or malformed")
        else:
            listed = {name(entry.name) for entry in doc.object_types}
            supported = {
                n for n, position in enumeration.items() if position < len(bits) and bits[position]
            }
            unknown = listed - set(enumeration)
            if unknown:
                yield rule.finding(f"Unknown standard object types: {sorted(unknown)}")
            if listed != supported:
                yield rule.finding(
                    f"Object-type section {sorted(listed)} differs from bits {sorted(supported)}",
                    prop="protocol-object-types-supported",
                )
    elif key in {"C5-13", "C5-14"}:
        service = key == "C5-13"
        count = (
            (
                provider.services_bit_count(revision)
                if service
                else provider.object_types_bit_count(revision)
            )
            if revision is not None
            else None
        )
        bits = query.services_supported_bits if service else query.object_types_supported_bits
        if count is None:
            yield rule.skipped("Exact bit count unavailable for declared Protocol_Revision")
        elif bits is None:
            yield rule.skipped("Supported bit string is unspecified or malformed")
        elif len(bits) != count:
            yield rule.finding(
                f"Supported bit string length {len(bits)} must be {count}",
                prop="protocol-services-supported"
                if service
                else "protocol-object-types-supported",
            )
    elif key == "C5-17":
        segmentation = scalar(ctx, device, "segmentation-supported")
        if segmentation is None:
            yield rule.skipped("Segmentation_Supported is unspecified or absent")
        elif name(segmentation) in {"segmented-both", "segmented-receive"}:
            segments = scalar(ctx, device, "max-segments-accepted")
            if type(segments) is not int or segments <= 1:
                yield rule.finding(
                    "Receiving segmentation requires Max_Segments_Accepted > 1",
                    object_id=str(device.identifier),
                    prop="max-segments-accepted",
                )
