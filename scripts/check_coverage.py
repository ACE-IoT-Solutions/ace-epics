"""Enforce overall and per-module statement coverage from coverage.py JSON."""

import argparse
import json
from pathlib import Path

SCOPES = {
    "lexer": "lexer.py",
    "values": "values/",
    "model": "model/",
    "codecs": "codecs/",
    "validation": "validation/",
}


def check(data: dict) -> bool:
    totals = [("overall", data["totals"], 90)]
    for name, prefix in SCOPES.items():
        selected = []
        for filename, details in data["files"].items():
            path = filename.replace("\\", "/")
            if "ace_epics/" in path:
                relative = path.split("ace_epics/", 1)[1]
                if relative == prefix or relative.startswith(prefix):
                    selected.append(details["summary"])
        if not selected:
            print(f"FAIL {name}: no measured source files")
            totals.append((name, {"num_statements": 0, "covered_lines": 0}, 95))
        else:
            totals.append(
                (
                    name,
                    {
                        "num_statements": sum(item["num_statements"] for item in selected),
                        "covered_lines": sum(item["covered_lines"] for item in selected),
                    },
                    95,
                )
            )
    passed = True
    for name, summary, threshold in totals:
        statements = summary["num_statements"]
        covered = summary["covered_lines"]
        valid = statements > 0 and covered * 100 >= statements * threshold
        percentage = covered * 100 / statements if statements else 0
        print(f"{'PASS' if valid else 'FAIL'} {name}: {percentage:.2f}% (required {threshold}%)")
        passed &= valid
    return passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", nargs="?", type=Path, default=Path("coverage.json"))
    args = parser.parse_args()
    raise SystemExit(0 if check(json.loads(args.report.read_text(encoding="utf-8"))) else 1)
