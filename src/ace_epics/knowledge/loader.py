"""Load sourced Clause 5 knowledge with explicit revision coverage."""

import json
from collections.abc import Mapping
from importlib.resources import files
from pathlib import Path
from typing import Any

from .provider import (
    BibbDefinition,
    NullProvider,
    ObjectDefinition,
    ServiceRequirement,
    normalize_name,
)


class JsonKnowledgeProvider(NullProvider):
    """Versioned tables for 135.1 Clause 5 from packaged or custom JSON data."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.root = (
            Path(path) if path is not None else files("ace_epics.knowledge").joinpath("data")
        )
        self._cache: dict[str, dict[str, Any]] = {}

    def _read(self, relative: str) -> dict[str, Any]:
        if relative not in self._cache:
            resource = self.root.joinpath(relative)
            if not resource.is_file():
                self._cache[relative] = {}
            else:
                data = json.loads(resource.read_text(encoding="utf-8"))
                if not isinstance(data, dict) or not data.get("source"):
                    raise ValueError(f"Knowledge table {relative} requires a source edition")
                self._cache[relative] = data
        return self._cache[relative]

    def _enumeration(self, filename: str, revision: int | None) -> Mapping[str, int]:
        data = self._read(filename)
        if not data:
            return {}
        current = data.get("revision") if revision is None else revision
        if current is None or not data.get("coverage_min_revision", current) <= current <= data.get(
            "revision", current
        ):
            return {}
        introduced = data.get("introduced_revision", {})
        removed = data.get("removed_revision", {})
        return {
            normalize_name(name): number
            for name, number in data.get("values", {}).items()
            if introduced.get(name, 0) <= current
            and (name not in removed or current < removed[name])
        }

    def _count(self, filename: str, revision: int | None) -> int | None:
        data = self._read(filename)
        current = data.get("revision") if revision is None else revision
        return data.get("bit_counts", {}).get(str(current))

    def capabilities(self) -> frozenset[str]:
        """Available Clause 5 table families; revision/object coverage is checked per lookup."""
        available = {
            capability
            for capability, filename in (
                ("object_types", "object_types.json"),
                ("services", "services.json"),
                ("bibbs", "bibbs.json"),
                ("property_identifiers", "property_identifiers.json"),
            )
            if self._read(filename)
        }
        directory = self.root.joinpath("objects")
        if directory.is_dir() and any(
            item.is_file() and item.name.endswith(".json") for item in directory.iterdir()
        ):
            available.add("objects")
        return frozenset(available)

    def object_types(self, revision: int | None) -> Mapping[str, int]:
        """Names and identifiers available at a sourced revision (C5-06)."""
        return self._enumeration("object_types.json", revision)

    def object_types_bit_count(self, revision: int | None) -> int | None:
        """Exact sourced bit count, without extrapolation (C5-14)."""
        return self._count("object_types.json", revision)

    def services(self, revision: int | None) -> Mapping[str, int]:
        """Supported-service bit positions (C5-05)."""
        return self._enumeration("services.json", revision)

    def services_bit_count(self, revision: int | None) -> int | None:
        """Exact sourced service bit count (C5-13)."""
        return self._count("services.json", revision)

    def property_identifiers(self) -> Mapping[str, int]:
        """Factual property names and numbers (Clause 7.1.2)."""
        return self._read("property_identifiers.json").get("values", {})

    def bibb(self, name: str) -> BibbDefinition | None:
        """Return an Annex K definition for Clause 5(a)-(e), preserving conditions."""
        entries = self._read("bibbs.json").get("definitions", {})
        entry = next(
            (v for k, v in entries.items() if normalize_name(k) == normalize_name(name)), None
        )
        return BibbDefinition.model_validate(entry) if entry is not None else None

    def effective_bibb(self, name: str) -> BibbDefinition | None:
        """Resolve Annex K dependencies for Clause 5(a)-(e); missing data stays unavailable."""
        root = self.bibb(name)
        if root is None:
            return None
        pending = [normalize_name(name)]
        visited: set[str] = set()
        directions: dict[str, tuple[bool, bool]] = {}
        objects: set[str] = set()
        alternatives: list[list[str]] = []
        conditional: list[dict[str, Any]] = []
        extras: dict[str, list] = {"service_alternatives": [], "bibb_alternatives": []}
        while pending:
            key = pending.pop()
            if key in visited:
                continue
            visited.add(key)
            definition = self.bibb(key)
            if definition is None:
                return None
            pending.extend(normalize_name(n) for n in definition.requires_bibbs)
            for key in extras:
                extras[key].extend(getattr(definition, key, []))
            for service in definition.services:
                if service.conditions:
                    conditional.append(
                        {
                            "services": [
                                service.model_copy(update={"conditions": []}).model_dump()
                            ],
                            "condition": {"kind": "all", "conditions": service.conditions},
                        }
                    )
                    continue
                service_name = normalize_name(service.name)
                previous = directions.get(service_name, (False, False))
                directions[service_name] = (
                    previous[0] or service.initiate,
                    previous[1] or service.execute,
                )
            objects.update(definition.object_types)
            alternatives.extend(definition.object_type_alternatives)
            conditional.extend(definition.conditional_requirements)
        return root.model_copy(
            update={
                "services": [
                    ServiceRequirement(name=n, initiate=i, execute=e)
                    for n, (i, e) in sorted(directions.items())
                ],
                "object_types": sorted(objects),
                "object_type_alternatives": alternatives,
                "conditional_requirements": conditional,
                **extras,
            }
        )

    def object_definition(self, object_type: str, revision: int | None) -> ObjectDefinition | None:
        """Return Clause 12 definitions only within explicitly verified coverage."""
        name = normalize_name(object_type)
        if not name or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in name):
            return None
        data = (
            self._read(f"objects/revisions/{revision}/{name}.json") if revision is not None else {}
        )
        if not data:
            data = self._read(f"objects/{name}.json")
        if not data:
            return None
        current = data.get("revision") if revision is None else revision
        minimum = data.get("coverage_min_revision", data.get("revision"))
        if current is None or minimum is None or not minimum <= current <= data["revision"]:
            return None
        return ObjectDefinition.model_validate(data)
