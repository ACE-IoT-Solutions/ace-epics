"""Render the ASHRAE 135.1 conformance matrix without implying certification."""

from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "tests/conformance/matrix.yaml"
OUTPUT = ROOT / "docs/site/reference/conformance.md"


def read_matrix(path: Path = MATRIX) -> list[dict]:
    """Read authored traceability rows for ASHRAE 135.1 Clauses 4 and 5."""
    rows = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("The conformance matrix must be a list of rows")
    return rows


def render_matrix(rows: list[dict]) -> str:
    """Render exact matrix statuses and test references as Markdown."""
    statuses = Counter(row["status"] for row in rows)
    clauses = Counter(row["clause"] for row in rows)
    lines = [
        "# Conformance matrix",
        "",
        "Generated from `tests/conformance/matrix.yaml`; do not edit this page directly.",
        "",
        "This matrix records implementation and test traceability. Planned entries",
        "are unfinished work, and implemented entries do not imply product certification.",
        "",
        "## Status counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    lines.extend(f"| {status} | {count} |" for status, count in sorted(statuses.items()))
    lines.extend(["", "## Clause counts", "", "| Clause | Count |", "|---|---:|"])
    lines.extend(f"| {clause} | {count} |" for clause, count in sorted(clauses.items()))
    lines.extend(
        [
            "",
            "## Requirements",
            "",
            "| ID | Clause | Rule | Mode | Status | Tests |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in rows:
        rule = row["rule"].replace("|", "\\|").replace("\n", " ")
        tests = "<br>".join(f"`{test}`" for test in row["tests"]) or "—"
        lines.append(
            f"| {row['id']} | {row['clause']} | {rule} | {row['mode']} | "
            f"{row['status']} | {tests} |"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render_matrix(read_matrix()), encoding="utf-8")
