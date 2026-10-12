"""Structured parser and validation diagnostics (135.1 Clauses 4, 5, 14)."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Severity(StrEnum):
    """Severity of a finding; SKIPPED denotes unavailable Clause 5 knowledge."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SKIPPED = "skipped"


class Diagnostic(BaseModel):
    """A located finding with a standard clause reference (Clause 14)."""

    model_config = ConfigDict(extra="forbid")
    code: str
    severity: Severity
    message: str
    clause: str | None = None
    line: int | None = Field(default=None, ge=1)
    column: int | None = Field(default=None, ge=1)
    section: str | None = None
    object_id: str | None = None
    property: str | None = None
    caused_by: list[str] = Field(default_factory=list)


class EpicsError(Exception):
    """Collected error diagnostics from parsing or validation (Clauses 4, 5)."""

    def __init__(self, diagnostics: list[Diagnostic]) -> None:
        self.diagnostics = diagnostics
        super().__init__("; ".join(d.message for d in diagnostics))


class DiagnosticSink:
    """Collect and order Clause 4/5 diagnostics without interrupting processing."""

    def __init__(self) -> None:
        self.diagnostics: list[Diagnostic] = []

    def add(self, diagnostic: Diagnostic) -> None:
        """Append a finding (Clause 14)."""
        self.diagnostics.append(diagnostic)

    def filtered(self, severity: Severity) -> list[Diagnostic]:
        """Return findings with a particular severity (Clause 14)."""
        return [d for d in self.diagnostics if d.severity == severity]

    def sorted(self) -> list[Diagnostic]:
        """Return source order, followed by unlocated findings (Clause 14)."""
        return sorted(self.diagnostics, key=lambda d: (d.line or float("inf"), d.column or 0))

    def has_errors(self) -> bool:
        """Whether any finding is an error (Clause 14)."""
        return bool(self.filtered(Severity.ERROR))

    def raise_if_errors(self) -> None:
        """Raise one exception containing all findings when errors exist (Clause 14)."""
        if self.has_errors():
            raise EpicsError(self.sorted())


class DiagnosticDefinition(BaseModel):
    """Documented diagnostic code and owning clause (Clauses 4, 5, 14)."""

    code: str
    clause: str
    description: str


DIAGNOSTIC_REGISTRY: dict[str, DiagnosticDefinition] = {}


def register_diagnostic(code: str, clause: str, description: str) -> None:
    """Register stable diagnostic metadata for generated reference pages (Clause 14)."""
    DIAGNOSTIC_REGISTRY[code] = DiagnosticDefinition(
        code=code, clause=clause, description=description
    )


for _clause, _codes in {
    "4.1": "E-HEADER E-HEADER-FORM E-CHARSET E-BOM E-ENDIAN E-WIDTH E-DBCS E-DECODE E-LINE-ENDINGS",
    "4.3": "L-UNTERMINATED-STRING",
    "4.4": (
        "V-DEPTH V-BARE-DATE V-DATE-NAME V-DATE-ABBREVIATION V-DATE V-DATE-RANGE V-MISSING "
        "V-UNBALANCED V-TAG V-OCTETS V-ODD-OCTETS V-TIME-PRECISION V-TIME-RANGE "
        "V-NUMBER V-REAL-NOTATION V-PROPRIETARY V-TOKEN V-CLOSER V-TRAILING-COMMA "
        "V-MISSING-COMMA V-NESTED-UNSPECIFIED V-INVALID V-TRAILING"
    ),
    "4.4.2": ("R-BRACKETS R-COLON R-NAME R-DUPLICATE R-VALUE R-SEPARATOR R-BARE-DATE R-LENGTH"),
    "4.5": (
        "M-DEVICE-COUNT M-DUPLICATE-DECLARATION M-DEFAULT-RESTRICTION "
        "M-BIBB-NAME M-MSTP-9600 M-WINDOW-RANGE"
    ),
}.items():
    for _code in _codes.split():
        register_diagnostic(_code, _clause, _code.split("-", 1)[1].replace("-", " ").capitalize())
