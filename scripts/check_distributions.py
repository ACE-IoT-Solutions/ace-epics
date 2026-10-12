"""Audit release archives for packaged data and excluded private standard sources."""

import argparse
import tarfile
import zipfile
from pathlib import Path

REQUIRED = {
    "ace_epics/py.typed",
    "ace_epics/model/document.py",
    "ace_epics/codecs/_schema.py",
    "ace_epics/codecs/data/ontology.ttl",
    "ace_epics/codecs/data/shapes.ttl",
    "ace_epics/knowledge/data/bibbs.json",
    "ace_epics/knowledge/data/services.json",
    "ace_epics/knowledge/data/object_types.json",
    "ace_epics/knowledge/data/property_identifiers.json",
    "ace_epics/knowledge/data/objects/device.json",
}


def check(path: Path) -> None:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
    else:
        with tarfile.open(path) as archive:
            names = archive.getnames()
    normalized = {name.split("src/", 1)[-1] for name in names}
    source = Path(__file__).resolve().parents[1] / "src"
    packaged_data = {
        str(item.relative_to(source)).replace("\\", "/")
        for item in source.joinpath("ace_epics").rglob("*")
        if item.is_file() and item.suffix in {".json", ".ttl"}
    }
    missing = (REQUIRED | packaged_data) - normalized
    private = [
        name
        for name in names
        if (
            name.lower().endswith(".pdf")
            or "/private/" in name
            or "/resources/" in name
            or "135-2024.txt" in name
        )
    ]
    assert not missing, f"{path}: missing packaged files {sorted(missing)}"
    assert not private, f"{path}: private standard source files {private}"
    assert any(name.endswith("LICENSE") for name in names), f"{path}: Apache license absent"
    if path.suffix != ".whl":
        assert any(name.endswith("schema/epics-document.schema.json") for name in names), (
            f"{path}: published schema source absent"
        )
    print(f"PASS {path.name}: required data and license present; private sources excluded")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", nargs="+", type=Path)
    args = parser.parse_args()
    for archive in args.archives:
        check(archive)
