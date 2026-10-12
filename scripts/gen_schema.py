"""Publish the Clause 4 JSON Schema snapshot."""

import json
from pathlib import Path

from ace_epics.codecs._schema import document_schema

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "schema/epics-document.schema.json"

if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(document_schema(), indent=2) + "\n", encoding="utf-8")
