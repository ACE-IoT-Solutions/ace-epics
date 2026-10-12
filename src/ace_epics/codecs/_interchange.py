"""Shared tagged-tree/text representation of the Clause 4 document model."""

from collections.abc import Mapping
from typing import Any, Literal

from pydantic import TypeAdapter, ValidationError

from ace_epics.diagnostics import Diagnostic, EpicsError, Severity, register_diagnostic
from ace_epics.lexer import TokenKind, tokenize
from ace_epics.model.document import EpicsDocument
from ace_epics.values.nodes import ValueNode
from ace_epics.values.parser import ValueParser, parse_value
from ace_epics.values.render import render

FORMAT = "ace-epics/1"
SCHEMA = "https://w3id.org/ace-epics/schema/1/epics-document.json"
VALUES = TypeAdapter(ValueNode)
ValueMode = Literal["tree", "text"]
VALUE_KINDS = {
    "null",
    "boolean",
    "integer",
    "real",
    "octet-string",
    "character-string",
    "enumerated",
    "empty",
    "unspecified",
    "wildcard",
    "date",
    "time",
    "date-range",
    "object-identifier",
    "context-tagged",
    "group",
}
VALUE_FIELDS = {"value", "minimum", "maximum", "resolution"}
DATE_FIELDS = {"weekday", "day", "month", "year", "hour", "minute", "second", "hundredth"}


def failure(message: str, code: str = "SERDES-INPUT") -> EpicsError:
    """Create a structured interchange failure (Clauses 4 and 14)."""
    return EpicsError([Diagnostic(code=code, severity=Severity.ERROR, message=message, clause="4")])


def document_data(
    doc: EpicsDocument, *, values: ValueMode = "tree", preserve_raw: bool = False
) -> dict[str, Any]:
    """Serialize the document, compacting names and optionally rendering values (4.4)."""
    if values not in {"tree", "text"}:
        raise ValueError("values must be 'tree' or 'text'")

    def convert(value: Any) -> Any:
        if isinstance(value, list):
            return [convert(item) for item in value]
        if not isinstance(value, dict):
            return value
        if set(value) <= {"canonical", "raw"} and "canonical" in value:
            return value if preserve_raw else value["canonical"]
        if value.get("kind") in VALUE_KINDS:
            if values == "text":
                return render(VALUES.validate_python(value))
            if value["kind"] == "wildcard":
                return "*"
        return {key: convert(item) for key, item in value.items()}

    result = convert(doc.model_dump(mode="json", by_alias=False, exclude={"source"}))
    return {"$schema": SCHEMA, "format": FORMAT, **result}


def decode_document(data: Any) -> EpicsDocument:
    """Accept compact names and either tagged or literal values (Clause 4 interchange)."""
    if not isinstance(data, Mapping):
        raise failure("Interchange input must contain a document mapping")
    content = dict(data)
    version = content.pop("format", FORMAT)
    content.pop("$schema", None)
    if version != FORMAT:
        raise failure(f"Unsupported interchange format: {version!r}", "SERDES-VERSION")
    findings: list[Diagnostic] = []

    def restore(
        value: Any,
        *,
        field: str | None = None,
        in_node: bool = False,
        parent_kind: str | None = None,
    ) -> Any:
        if isinstance(value, list):
            return [restore(item, in_node=in_node, parent_kind=parent_kind) for item in value]
        if isinstance(value, dict):
            kind = value.get("kind")
            node = kind in VALUE_KINDS
            return {
                key: restore(item, field=key, in_node=node, parent_kind=kind if node else None)
                for key, item in value.items()
            }
        if value == "*" and in_node and (field in DATE_FIELDS or field is None):
            return {"kind": "wildcard"}
        text_position = (field in VALUE_FIELDS and not in_node) or (
            in_node and (field is None or (field == "value" and parent_kind == "context-tagged"))
        )
        if isinstance(value, str) and text_position:
            if value == "":
                return {"kind": "empty"}
            node, diagnostics = parse_value(value)
            tokens, _ = tokenize(value)
            parser = ValueParser(tokens)
            parser.parse()
            if parser.current.kind != TokenKind.EOF:
                raise failure("Unexpected trailing content in EPICS literal", "SERDES-VALUE")
            if any(d.severity == Severity.ERROR for d in diagnostics):
                raise EpicsError(diagnostics)
            findings.extend(diagnostics)
            return node.model_dump(mode="json")
        return value

    try:
        doc = EpicsDocument.model_validate(restore(content))
    except (ValidationError, ValueError, TypeError, RecursionError) as exc:
        raise failure(str(exc)) from exc
    doc.diagnostics.extend(findings)
    return doc


for _code, _description in {
    "SERDES-INPUT": "Malformed interchange document",
    "SERDES-VERSION": "Unsupported interchange format version",
    "SERDES-VALUE": "Unexpected trailing content in a value literal",
    "YAML-LIMIT": "YAML expansion or nesting limit exceeded",
    "YAML-ALIAS": "Recursive YAML alias rejected",
    "RDF-SHAPE": "RDF structural requirement is missing or ambiguous",
    "RDF-LIST": "RDF list is malformed or cyclic",
    "RDF-LIMIT": "RDF node expansion limit exceeded",
    "RDF-DOCUMENT": "RDF must contain one EPICS document",
    "RDF-INPUT": "Invalid RDF syntax",
}.items():
    register_diagnostic(_code, "4", _description)
