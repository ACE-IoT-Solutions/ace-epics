"""Serializable consistency-validation reports (135.1 Clause 14)."""

from collections import Counter
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ace_epics import __version__
from ace_epics.diagnostics import Diagnostic, Severity


class RuleResult(BaseModel):
    """Outcome and findings for one Clause 5 consistency check."""

    model_config = ConfigDict(extra="forbid")
    rule_id: str
    clause: str
    outcome: Literal["pass", "fail", "skipped", "not_applicable"]
    diagnostics: list[Diagnostic] = Field(default_factory=list)


class ValidationReport(BaseModel):
    """Document identity, tool provenance, and executed findings (Clause 14)."""

    model_config = ConfigDict(extra="forbid")
    document_id: dict[str, str] = Field(default_factory=dict)
    tool_version: str = __version__
    run_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    results: list[RuleResult] = Field(default_factory=list)

    @property
    def diagnostics(self) -> list[Diagnostic]:
        """Flatten rule findings in execution order (Clause 14)."""
        return [finding for result in self.results for finding in result.diagnostics]

    def summary(self) -> dict[str, int]:
        """Count all possible rule outcomes, including zero counts (Clause 14)."""
        counts = Counter(result.outcome for result in self.results)
        return {key: counts[key] for key in ("pass", "fail", "skipped", "not_applicable")}

    def exit_code(self, *, warnings_as_errors: bool = False) -> int:
        """Error findings fail; warning-only findings fail when requested (Clause 14)."""
        return int(
            any(
                d.severity == Severity.ERROR
                or (warnings_as_errors and d.severity == Severity.WARNING)
                for d in self.diagnostics
            )
        )

    def to_json(self) -> str:
        """Serialize a machine-readable Clause 14 report."""
        return self.model_dump_json(indent=2)

    def to_markdown(self) -> str:
        """Render all outcomes and findings as a portable Clause 14 report."""

        def escape(value: str) -> str:
            return value.replace("|", "\\|").replace("\n", "<br>")

        lines = [
            "# EPICS consistency report",
            "",
            f"Tool version: {self.tool_version}",
            f"Run at: {self.run_at.isoformat()}",
            "",
            "| Rule | Clause | Outcome | Findings |",
            "|---|---|---|---|",
        ]
        for result in self.results:
            findings = "<br>".join(escape(d.message) for d in result.diagnostics)
            lines.append(f"| {result.rule_id} | {result.clause} | {result.outcome} | {findings} |")
        return "\n".join(lines) + "\n"
