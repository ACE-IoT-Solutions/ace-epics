"""JSON Schema projection for Clause 4 interchange documents."""

from copy import deepcopy
from typing import Any

from ace_epics.codecs._interchange import FORMAT, SCHEMA, VALUE_KINDS
from ace_epics.model.document import EpicsDocument


def document_schema() -> dict[str, Any]:
    """Adapt the Pydantic schema for compact names and literal value alternatives (4.4)."""
    schema = deepcopy(EpicsDocument.model_json_schema(by_alias=False, mode="serialization"))
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = SCHEMA
    schema["title"] = "BACnet EPICS document, ace-epics/1"
    schema["properties"]["$schema"] = {"type": "string", "const": SCHEMA}
    schema["properties"]["format"] = {"type": "string", "const": FORMAT}
    schema["required"] = [*schema.get("required", []), "format", "$schema"]
    for definition in schema.get("$defs", {}).values():
        if set(definition.get("properties", {})) == {"canonical", "raw"}:
            original = dict(definition)
            definition.clear()
            definition["anyOf"] = [{"type": "string"}, original]

    def adapt(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                adapt(item)
        elif isinstance(value, dict):
            for item in list(value.values()):
                adapt(item)
            discriminator = value.get("discriminator", {})
            if set(discriminator.get("mapping", {})) & VALUE_KINDS:
                original = dict(value)
                value.clear()
                value["anyOf"] = [{"type": "string"}, original]
            if value.get("$ref") == "#/$defs/WildcardValue":
                value.clear()
                value["anyOf"] = [{"const": "*"}, {"$ref": "#/$defs/WildcardValue"}]

    adapt(schema)
    schema["examples"] = [
        {
            "$schema": SCHEMA,
            "format": FORMAT,
            "general": {
                "vendor_name": "Example Controls",
                "product_name": "Synthetic Device",
                "product_model_number": "EX-1",
                "product_description": "Invented example",
            },
        }
    ]
    return schema
