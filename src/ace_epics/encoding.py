"""EPICS byte encoding detection and conversion (135.1 Clause 4.1)."""

from __future__ import annotations

import codecs
import os
import re
from dataclasses import dataclass

from ace_epics.diagnostics import Diagnostic, Severity

_CODECS = {
    0: "utf-8",
    1: "mbcs" if os.name == "nt" else "cp932",
    2: "iso2022_jp",
    3: "utf-32-be",
    4: "utf-16-be",
    5: "latin-1",
}


@dataclass(frozen=True)
class Detected:
    """Header charset, stream width, BOM and selected Python codec (135.1 Clause 4.1)."""

    charset_code: int
    width: int
    bom: bytes
    python_codec: str


def detect(data: bytes) -> Detected:
    """Identify the header width, endian order and charset digit without raising. (135.1 Clause
    4.1).
    """
    bom = b""
    codec = "utf-8"
    width = 1
    for prefix, candidate, candidate_width in (
        (codecs.BOM_UTF32_BE, "utf-32-be", 4),
        (codecs.BOM_UTF32_LE, "utf-32-le", 4),
        (codecs.BOM_UTF8, "utf-8", 1),
        (codecs.BOM_UTF16_BE, "utf-16-be", 2),
        (codecs.BOM_UTF16_LE, "utf-16-le", 2),
    ):
        if data.startswith(prefix):
            bom, codec, width = prefix, candidate, candidate_width
            break
    raw = data[len(bom) :]
    if not bom:
        for candidate, candidate_width in (
            ("utf-32-be", 4),
            ("utf-32-le", 4),
            ("utf-16-be", 2),
            ("utf-16-le", 2),
        ):
            if raw[: 4 * candidate_width].lower() == "PICS".lower().encode(candidate):
                codec, width = candidate, candidate_width
                break
    try:
        header = raw[:32].decode(codec, errors="ignore")
    except UnicodeError:
        header = ""
    match = re.match(r"pics[ \t]+([0-9])(?:[ \t]*(?:--[^\r\n]*)?)?(?:\r\n|\r|\n|$)", header, re.I)
    code = int(match[1]) if match else -1
    if width == 1:
        codec = _CODECS.get(code, "utf-8")
    return Detected(code, width, bom, codec)


def decode(data: bytes, *, strict: bool = False) -> tuple[str, Detected, list[Diagnostic]]:
    """Decode with located diagnostics, preserving original line endings. (135.1 Clause 4.1)."""
    found = detect(data)
    diagnostics: list[Diagnostic] = []

    def issue(code, message, *, error=False):
        diagnostics.append(
            Diagnostic(
                code=code,
                message=message,
                clause="4.1",
                severity=Severity.ERROR if error or strict else Severity.WARNING,
                line=1,
                column=1,
            )
        )

    if found.charset_code == -1:
        issue("E-HEADER", "Missing PICS character-set digit.", error=True)
    elif found.charset_code not in _CODECS:
        issue("E-CHARSET", "Unknown PICS character-set code; decoding as UTF-8.", error=True)
    if found.bom:
        issue("E-BOM", "A byte-order mark precedes the PICS header.")
    if found.python_codec.endswith("-le"):
        issue("E-ENDIAN", "Little-endian wide encoding is accepted as an extension.")
    expected = {3: 4, 4: 2}.get(found.charset_code, 1)
    if found.charset_code in _CODECS and found.width != expected:
        issue("E-WIDTH", "Header character-set code disagrees with the detected width.", error=True)
    if found.charset_code == 1 and os.name != "nt":
        issue("E-DBCS", "DBCS code page is ambiguous; using Microsoft CP932.")
    try:
        text = data[len(found.bom) :].decode(found.python_codec)
    except UnicodeError:
        issue("E-DECODE", "Invalid encoded characters replaced for continued parsing.", error=True)
        text = data[len(found.bom) :].decode(found.python_codec, errors="replace")
    if (
        found.charset_code in _CODECS
        and text.splitlines()
        and text.splitlines()[0] != f"PICS {found.charset_code}"
    ):
        issue("E-HEADER-FORM", "Header case or spacing differs from the canonical PICS header.")
    if re.search(r"(?<!\r)\n|\r(?!\n)", text):
        issue("E-LINE-ENDINGS", "EPICS lines must use CRLF terminators.")
    return text, found, diagnostics


def encode(text: str, charset_code: int = 0) -> bytes:
    """Encode canonical big-endian, BOM-free EPICS text; JIS uses ISO-2022-JP. (135.1 Clause
    4.1).
    """
    if charset_code not in _CODECS:
        raise ValueError(f"Unknown character-set code: {charset_code}")
    return text.encode(_CODECS[charset_code])
