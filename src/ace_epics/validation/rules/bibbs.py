"""BIBB, service direction, and object obligations (135.1 Clause 5(a)-(e))."""

from collections.abc import Iterable
from typing import TYPE_CHECKING

from ace_epics.diagnostics import Diagnostic
from ace_epics.knowledge.provider import BibbDefinition, ServiceRequirement

from . import name

if TYPE_CHECKING:
    from ..engine import Context
    from . import ConsistencyRule


def applicable(ctx: "Context", condition: dict) -> bool | None:
    """Evaluate Annex K conditions established by the EPICS itself (Clause 5(a)-(e))."""
    kind = condition.get("kind")
    if kind == "protocol_revision_at_least":
        revision = ctx.query.protocol_revision
        return revision >= condition["revision"] if revision is not None else None
    if kind == "object_type_supported":
        return ctx.document.supports_object_type(condition["object_type"])
    if kind == "writable_property_present":
        return any(
            ctx.query.is_writable(obj, condition["property"])
            for obj in ctx.document.objects
            if obj.has_property(condition["property"])
        )
    if kind in {"any", "all"}:
        results = [applicable(ctx, item) for item in condition["conditions"]]
        if kind == "any":
            return True if True in results else None if None in results else False
        return False if False in results else None if None in results else True
    return None


def resolve(ctx: "Context", bibb_name: str) -> BibbDefinition | None:
    """Expand mandatory Annex K dependencies for all providers (Clause 5(a)-(e))."""
    pending = [bibb_name]
    visited: set[str] = set()
    objects: set[str] = set()
    services: dict[str, tuple[bool, bool]] = {}
    alternatives: list[list[str]] = []
    conditional: list[dict] = []
    extras: dict[str, list] = {"service_alternatives": [], "bibb_alternatives": []}
    unresolved = []

    def include(requirement: dict) -> None:
        objects.update(requirement.get("object_types", []))
        alternatives.extend(requirement.get("object_type_alternatives", []))
        for key in extras:
            extras[key].extend(requirement.get(key, []))
        pending.extend(requirement.get("requires_bibbs", []))
        for service_data in requirement.get("services", []):
            service = ServiceRequirement.model_validate(service_data)
            if service.conditions:
                conditional.append(
                    {
                        "services": [service.model_copy(update={"conditions": []}).model_dump()],
                        "condition": {"kind": "all", "conditions": service.conditions},
                    }
                )
                continue
            old = services.get(name(service.name), (False, False))
            services[name(service.name)] = (old[0] or service.initiate, old[1] or service.execute)

    # Both dependency kinds share one visited set: cycles terminate without losing
    # alternatives or conditions from a conditional child.
    while pending or conditional:
        if pending:
            current = name(pending.pop())
            if current in visited:
                continue
            visited.add(current)
            definition = ctx.provider.bibb(current)
            if definition is None:
                return None
            include(definition.model_dump())
            conditional.extend(definition.conditional_requirements)
        else:
            requirement = conditional.pop()
            applies = applicable(ctx, requirement.get("condition", {}))
            if applies is None:
                unresolved.append(requirement)
            elif applies:
                include(requirement)
    conditional = unresolved
    return BibbDefinition(
        services=[
            ServiceRequirement(name=n, initiate=i, execute=e)
            for n, (i, e) in sorted(services.items())
        ],
        object_types=sorted(objects),
        object_type_alternatives=alternatives,
        conditional_requirements=conditional,
        **extras,
    )


def check(rule: "ConsistencyRule", ctx: "Context") -> Iterable[Diagnostic]:
    """Verify unconditional and alternative requirements for Clause 5(a)-(e)."""
    doc, query = ctx.document, ctx.query
    for claimed in doc.bibbs:
        bibb_name = name(claimed)
        definition = resolve(ctx, bibb_name)
        if definition is None:
            yield rule.skipped(f"Knowledge unavailable for BIBB {bibb_name} or a dependency")
            continue
        types = set(definition.object_types)
        section = {name(t.name) for t in doc.object_types}
        database = {name(obj.object_type) for obj in doc.objects}
        if rule.id in {"C5-01", "C5-02", "C5-03"}:
            enumeration = {}
            bits = []
            if rule.id == "C5-03":
                enumeration = ctx.provider.object_types(query.protocol_revision)
                bits = query.object_types_supported_bits
                if not enumeration or bits is None:
                    yield rule.skipped(
                        f"Supported-object bits or enumeration unavailable for {bibb_name}"
                    )
                    continue
                supported = {
                    n
                    for n, position in enumeration.items()
                    if position < len(bits) and bits[position] is True
                }
            else:
                supported = section if rule.id == "C5-01" else database
            for required in sorted(types - supported):
                position = enumeration.get(required) if rule.id == "C5-03" else None
                if rule.id == "C5-03" and (
                    position is None or (position < len(bits) and bits[position] is None)
                ):
                    yield rule.skipped(f"Object bit {required} is unresolved for {bibb_name}")
                else:
                    yield rule.finding(f"{bibb_name} requires object type {required}")
            for alternatives in definition.object_type_alternatives:
                if not set(alternatives) & supported:
                    if rule.id == "C5-03" and any(
                        (position := enumeration.get(option)) is None
                        or (position < len(bits) and bits[position] is None)
                        for option in alternatives
                    ):
                        yield rule.skipped(f"Object alternative bits unresolved for {bibb_name}")
                    else:
                        yield rule.finding(f"{bibb_name} requires one of {alternatives}")
        elif rule.id == "C5-04":
            for service in definition.services:
                if not doc.supports_service(
                    service.name,
                    initiate=True if service.initiate else None,
                    execute=True if service.execute else None,
                ):
                    yield rule.finding(
                        f"{bibb_name} requires {service.name} "
                        f"initiate={service.initiate}, execute={service.execute}"
                    )
            for options in getattr(definition, "service_alternatives", []):
                if not any(
                    doc.supports_service(
                        option["name"],
                        initiate=True if option.get("initiate") else None,
                        execute=True if option.get("execute") else None,
                    )
                    for option in options
                ):
                    yield rule.finding(
                        f"{bibb_name} requires at least one service alternative: {options}"
                    )
        elif rule.id == "C5-05":
            enumeration = ctx.provider.services(query.protocol_revision)
            bits = query.services_supported_bits
            executed = [service for service in definition.services if service.execute]
            options_groups = [
                options
                for options in getattr(definition, "service_alternatives", [])
                if options and all(option.get("execute") for option in options)
            ]
            if (executed or options_groups) and (not enumeration or bits is None):
                yield rule.skipped(f"Service bit vector or enumeration unavailable for {bibb_name}")
            elif executed or options_groups:
                assert bits is not None
                for service in executed:
                    position = enumeration.get(name(service.name))
                    if position is None:
                        yield rule.skipped(f"Unknown service {service.name} for {bibb_name}")
                    elif position >= len(bits) or bits[position] is False:
                        yield rule.finding(
                            f"{bibb_name} requires executed-service bit {service.name}"
                        )
                    elif bits[position] is None:
                        yield rule.skipped(f"Service bit {service.name} is unspecified")
                for options in options_groups:
                    states = []
                    for option in options:
                        position = enumeration.get(name(option["name"]))
                        states.append(
                            None
                            if position is None
                            else bits[position]
                            if position < len(bits)
                            else False
                        )
                    if True not in states:
                        if None in states:
                            yield rule.skipped(
                                f"Service alternative bits unresolved for {bibb_name}"
                            )
                        else:
                            yield rule.finding(
                                f"{bibb_name} requires an executed-service alternative bit"
                            )
        for options in getattr(definition, "bibb_alternatives", []):
            if not any(doc.supports_bibb(option) for option in options):
                yield rule.finding(f"{bibb_name} requires one of the BIBBs {options}")
        relevant = [
            item
            for item in definition.conditional_requirements
            if item.get("requires_bibbs")
            or (item.get("object_type_alternatives") and rule.id in {"C5-01", "C5-02", "C5-03"})
            or (item.get("service_alternatives") and rule.id in {"C5-04", "C5-05"})
            or (item.get("object_types") and rule.id in {"C5-01", "C5-02", "C5-03"})
            or (item.get("services") and rule.id in {"C5-04", "C5-05"})
        ]
        if relevant:
            yield rule.skipped(f"{bibb_name} has unresolved conditional obligations")
