"""Extract release notes from a Keep a Changelog section for an explicit tag."""

import argparse
import re
from pathlib import Path


def release_notes(changelog: str, version: str) -> str:
    """Return the version's notes, rejecting missing or empty release sections."""
    heading = re.compile(r"^## \[" + re.escape(version) + r"\](?:[^\n]*)$", re.MULTILINE)
    match = heading.search(changelog)
    if match is None:
        raise ValueError(f"CHANGELOG.md has no [{version}] release section")
    remainder = changelog[match.end() :]
    next_heading = re.search(r"^## ", remainder, re.MULTILINE)
    notes = remainder[: next_heading.start()] if next_heading else remainder
    if not notes.strip():
        raise ValueError(f"CHANGELOG.md release [{version}] is empty")
    return notes.strip() + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", help="Release tag, including its v prefix")
    parser.add_argument("--changelog", type=Path, default=Path("CHANGELOG.md"))
    parser.add_argument("--output", type=Path, default=Path("release-notes.md"))
    args = parser.parse_args()
    if not args.tag.startswith("v"):
        parser.error("Release tags must start with v")
    try:
        notes = release_notes(args.changelog.read_text(encoding="utf-8"), args.tag[1:])
    except ValueError as exc:
        parser.error(str(exc))
    args.output.write_text(notes, encoding="utf-8")
