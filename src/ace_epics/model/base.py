"""Common model policy and warning collection (Clause 4.5)."""

from pydantic import BaseModel, ConfigDict

from ace_epics.diagnostics import Diagnostic, Severity


class EpicsModel(BaseModel):
    """Mutable, closed model preserving string content (Clause 4.5)."""

    model_config = ConfigDict(
        extra="forbid", frozen=False, populate_by_name=True, str_strip_whitespace=False
    )

    def warnings(self) -> list[Diagnostic]:
        """Return model-level advisory findings (Clause 4.5)."""
        return []


def warning(code: str, message: str, clause: str) -> Diagnostic:
    """Build a nonfatal model diagnostic (Clause 4.5)."""
    return Diagnostic(code=code, severity=Severity.WARNING, message=message, clause=clause)
