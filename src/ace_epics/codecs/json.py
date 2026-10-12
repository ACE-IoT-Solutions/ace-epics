"""JSON interchange for EPICS values and declarations (ASHRAE 135.1 Clause 4)."""

import json as _json
from pathlib import Path
from typing import IO, Any

from ace_epics.diagnostics import EpicsError
from ace_epics.model.document import EpicsDocument

from ._interchange import ValueMode, decode_document, document_data, failure
from .base import ParseResult, document_from_result

name = "json"
extensions = (".json",)
media_type = "application/json"


def parse(data: str | bytes, **opts: Any) -> ParseResult:
    """Read JSON recoverably; failures carry diagnostics without a document (Clause 4)."""
    try:
        try:
            decoded = _json.loads(data)
        except (ValueError, UnicodeError, RecursionError) as exc:
            raise failure(f"Invalid JSON: {exc}") from exc
        doc = decode_document(decoded)
        return ParseResult(doc, doc.diagnostics)
    except EpicsError as exc:
        return ParseResult(None, exc.diagnostics)


def loads(data: str | bytes, *, raise_on_error: bool = True, **opts: Any) -> EpicsDocument:
    """Read a JSON document, raising collected failures by default (Clause 4)."""
    return document_from_result(parse(data, **opts), raise_on_error=raise_on_error)


def dumps(
    doc: EpicsDocument,
    *,
    values: ValueMode = "tree",
    preserve_raw: bool = False,
    indent: int | None = 2,
    **opts: Any,
) -> str:
    """Write deterministic, exact tagged values or canonical EPICS literals (4.4)."""
    return (
        _json.dumps(
            document_data(doc, values=values, preserve_raw=preserve_raw),
            ensure_ascii=False,
            allow_nan=False,
            indent=indent,
        )
        + "\n"
    )


def load(src: Path | str | IO[str] | IO[bytes], **opts: Any) -> EpicsDocument:
    """Read JSON from a path or file object (Clause 4 interchange)."""
    data = Path(src).read_bytes() if isinstance(src, (str, Path)) else src.read()
    return loads(data, **opts)


def dump(doc: EpicsDocument, dst: Path | str | IO[str], **opts: Any) -> None:
    """Write JSON to a path or text file object (Clause 4 interchange)."""
    text = dumps(doc, **opts)
    if isinstance(dst, (str, Path)):
        Path(dst).write_text(text, encoding="utf-8")
    else:
        dst.write(text)


def schema() -> dict[str, Any]:
    """Return the published ace-epics/1 interchange schema (Clause 4)."""
    from ._schema import document_schema

    return document_schema()
