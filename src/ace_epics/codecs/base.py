"""Shared codec contract for the Clause 4 EPICS document representation."""

from dataclasses import dataclass
from typing import Any, Protocol

from ace_epics.diagnostics import Diagnostic, EpicsError, Severity
from ace_epics.model import EpicsDocument


@dataclass(frozen=True)
class ParseResult:
    """A recoverable document or failure diagnostics without invented data (Clause 4)."""

    document: EpicsDocument | None
    diagnostics: list[Diagnostic]

    @property
    def has_errors(self) -> bool:
        """Whether any reader finding is an error (Clauses 4 and 14)."""
        return any(d.severity == Severity.ERROR for d in self.diagnostics)


def document_from_result(result: ParseResult, *, raise_on_error: bool = True) -> EpicsDocument:
    """Return a recovered document or raise its collected failures (Clause 4)."""
    if result.document is None or (raise_on_error and result.has_errors):
        raise EpicsError(result.diagnostics)
    return result.document


class Codec(Protocol):
    """One of the four serializations of a Clause4 document."""

    @property
    def name(self) -> str:
        """Canonical codec name for Clause4 serialization."""
        ...

    @property
    def extensions(self) -> tuple[str, ...]:
        """Filename extensions for Clause4 serialization inference."""
        ...

    @property
    def media_type(self) -> str:
        """Media type of the Clause4 serialization."""
        ...

    def parse(self, data: str | bytes, **opts: Any) -> ParseResult:
        """Collect Clause4 findings and an actual document when recoverable."""
        ...

    def loads(self, data: str | bytes, **opts: Any) -> EpicsDocument:
        """Deserialize a Clause4 document, raising collected errors by default."""
        ...

    def dumps(self, doc: EpicsDocument, **opts: Any) -> str | bytes:
        """Serialize the shared Clause4 document model."""
        ...

    def load(self, src: Any, **opts: Any) -> EpicsDocument:
        """Read a Clause4 document from a path or stream."""
        ...

    def dump(self, doc: EpicsDocument, dst: Any, **opts: Any) -> None:
        """Write a Clause4 document to a path or stream."""
        ...
