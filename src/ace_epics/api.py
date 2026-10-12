"""File-level parsing and format conversion helpers (135.1 Clause4)."""

from pathlib import Path
from typing import Any

from ace_epics.codecs import registry
from ace_epics.diagnostics import EpicsError, Severity
from ace_epics.model import EpicsDocument


def load(path: str | Path, *, format: str | None = None, **opts: Any) -> EpicsDocument:
    """Load a Clause4 document, inferring its format from its extension."""
    codec = registry.get(format) if format else registry.for_path(path)
    return codec.load(path, **opts)


def dump(doc: EpicsDocument, path: str | Path, *, format: str | None = None, **opts: Any) -> None:
    """Write a Clause4 document in the inferred or selected serialization."""
    codec = registry.get(format) if format else registry.for_path(path)
    codec.dump(doc, path, **opts)


def convert(
    src: str | Path,
    dst: str | Path,
    *,
    from_format: str | None = None,
    to_format: str | None = None,
    read_options: dict[str, Any] | None = None,
    write_options: dict[str, Any] | None = None,
) -> EpicsDocument:
    """Convert any supported Clause4 serialization through the shared document model."""
    document = load(src, format=from_format, **(read_options or {}))
    if any(d.severity == Severity.ERROR for d in document.diagnostics):
        raise EpicsError(document.diagnostics)
    dump(document, dst, format=to_format, **(write_options or {}))
    return document
