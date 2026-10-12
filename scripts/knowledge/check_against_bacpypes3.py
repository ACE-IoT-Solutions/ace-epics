"""Dev-only numeric interoperability check against the MIT-licensed bacpypes3.

Run: uv run --with bacpypes3 python scripts/knowledge/check_against_bacpypes3.py

The ASHRAE standard is the authority. The comparison stack can lag that edition;
missing names are reported separately and do not falsify the extracted tables.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def canonical(name: str) -> str:
    """Convert stack camelCase identifiers to BACnet hyphenated names."""
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", name)
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", name)
    name = name.replace("_", "-").lower()
    # The stack uses earlier published spellings for these unchanged IDs.
    return {
        "date-pattern-value": "datepattern-value",
        "datetime-pattern-value": "datetimepattern-value",
        "time-pattern-value": "timepattern-value",
        "auto-slave-discovery": "auto-subordinate-discovery",
        "manual-slave-address-binding": "manual-subordinate-address-binding",
        "slave-address-binding": "subordinate-address-binding",
        "slave-proxy-enable": "subordinate-proxy-enable",
        "max-master": "max-manager",
    }.get(name, name)


def compare(data_root: Path, *, require_complete: bool = False) -> int:
    from bacpypes3.basetypes import ObjectTypesSupported, Segmentation, ServicesSupported
    from bacpypes3.primitivedata import ObjectType, PropertyIdentifier

    classes = {
        "object_types": ObjectType,
        "services": ServicesSupported,
        "property_identifiers": PropertyIdentifier,
        "enums/segmentation": Segmentation,
    }
    failures = 0
    for filename, cls in classes.items():
        data = json.loads((data_root / f"{filename}.json").read_text())
        entries = getattr(cls, "_enum_map", None)
        if entries is None:
            entries = cls._bitstring_names
        stack = {canonical(name): value for name, value in entries.items() if isinstance(name, str)}
        # Bacpypes3 retains historical names, while this comparison targets the
        # source edition's current live enumeration.
        current = {
            name: value
            for name, value in data["values"].items()
            if data.get("removed_revision", {}).get(name, data["revision"] + 1) > data["revision"]
        }
        missing = sorted(set(current) - set(stack))
        mismatches = {
            name: (value, stack[name])
            for name, value in current.items()
            if name in stack and stack[name] != value
        }
        failures += len(mismatches) + (len(missing) if require_complete else 0)
        print(
            f"{filename}: {len(current) - len(missing)} compared, "
            f"{len(mismatches)} mismatches, {len(missing)} absent from stack"
        )
        for name, (expected, actual) in mismatches.items():
            print(f"  MISMATCH {name}: standard={expected}, stack={actual}")
        if missing:
            print("  Stack missing: " + ", ".join(missing))
        if filename == "object_types":
            bits = {
                canonical(name): value
                for name, value in ObjectTypesSupported._bitstring_names.items()
            }
            for name, expected in current.items():
                if name in bits and bits[name] != expected:
                    failures += 1
                    print(f"  MISMATCH object support bit {name}: {bits[name]} != {expected}")
    return int(bool(failures))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="also fail when bacpypes3 lacks a current standard name",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2] / "src/ace_epics/knowledge/data"
    return compare(root, require_complete=args.require_complete)


if __name__ == "__main__":
    raise SystemExit(main())
