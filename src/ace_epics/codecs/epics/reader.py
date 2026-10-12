"""Whole-file EPICS decoding, section recovery, and public read APIs (Clause 4)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, BinaryIO

from pydantic import ValidationError

from ace_epics.codecs.base import ParseResult, document_from_result
from ace_epics.diagnostics import Diagnostic, Severity
from ace_epics.encoding import decode
from ace_epics.lexer import TokenKind as K
from ace_epics.lexer import tokenize
from ace_epics.model import EpicsDocument, GeneralInformation, SourceInfo
from ace_epics.model.names import normalize_name

from .database import parse_database
from .sections import (
    END,
    FIELDS,
    HEADING_FIELDS,
    PARSERS,
    SIGNATURE,
    Issues,
    quoted_string,
    uncomment,
)


def _split(text: str, issues: Issues) -> dict[str, tuple[str, int]]:
    lines = text.splitlines()
    sections = {}
    order = []
    i = 0
    while i < len(lines):
        plain = uncomment(lines[i])[0].strip()
        match = re.match(r"([^:]+):\s*(.*)", plain)
        if not match:
            i += 1
            continue
        key = normalize_name(match[1])
        field = HEADING_FIELDS.get(key)
        start = i + 1
        rest = match[2]
        if field in FIELDS[:4]:
            body = rest
            i += 1
        else:
            if not field:
                issues.add("P-UNKNOWN-SECTION", "Unknown section heading: " + match[1], start)
            pieces = []
            depth = 0
            opened = False
            while i < len(lines):
                current = rest if i + 1 == start else lines[i]
                clean = uncomment(current)[0].strip()
                heading = re.match(r"([^:]+):", clean)
                if i + 1 != start and (
                    clean.casefold() == END.casefold()
                    or (
                        heading
                        and " ".join(heading[1].split()).casefold()
                        in {" ".join(k.split("-")).casefold() for k in HEADING_FIELDS}
                    )
                ):
                    if opened and depth:
                        issues.add(
                            "P-SECTION-BRACE",
                            "Unclosed section recovered at following heading.",
                            start,
                            error=True,
                        )
                    break
                tokens, _ = tokenize(current)
                for token in tokens:
                    if token.kind == K.LBRACE:
                        depth += 1
                        opened = True
                    elif token.kind == K.RBRACE:
                        depth -= 1
                pieces.append(current)
                i += 1
                if opened and depth <= 0 and field != "objects":
                    break
                if not opened and clean:
                    issues.add(
                        "P-SECTION-BRACE", "Section requires an opening brace.", start, error=True
                    )
                    break
            if not opened:
                issues.add("P-SECTION-BRACE", "Missing braced section body.", start, error=True)
            elif depth > 0 and i >= len(lines):
                issues.add("P-SECTION-BRACE", "Unclosed section at end of file.", start, error=True)
            body = "\n".join(pieces)
            if not field:
                issues.raw.setdefault(match[1], []).append(body)
            first = body.find("{")
            last = body.rfind("}")
            if first >= 0:
                body = body[
                    first + 1 : last
                    if last > first and (depth <= 0 or field == "objects")
                    else len(body)
                ]
        if field:
            if field in sections:
                issues.add("P-DUPLICATE-SECTION", "Duplicate section: " + field, start, error=True)
            else:
                sections[field] = (body, start)
                order.append(field)
    expected = [FIELDS.index(field) for field in order]
    if expected != sorted(expected):
        issues.add("P-SECTION-ORDER", "Sections differ from the printed order.", 1)
    if "objects" in order and order[-1] != "objects":
        issues.add("P-DATABASE-LAST", "Test database must be the last section.", error=True)
    missing = set(FIELDS) - sections.keys()
    if missing:
        issues.add("P-SECTIONS-INCOMPLETE", "Missing sections: " + ", ".join(sorted(missing)), 1)
    return sections


def _parse(input: str | bytes, strict: bool, source: SourceInfo | str | None) -> ParseResult:
    issues = Issues(strict)
    if isinstance(input, bytes):
        text, found, diags = decode(input, strict=strict)
        issues.extend(diags)
        encoding = found.python_codec
    else:
        text = input
        encoding = None
    if re.search(r"(?<!\r)\n|\r(?!\n)", text) and not any(
        d.code == "E-LINE-ENDINGS" for d in issues.diagnostics
    ):
        issues.add("E-LINE-ENDINGS", "EPICS lines must use CRLF terminators.", 1, clause="4.1")
    lines = text.splitlines()
    header = uncomment(lines[0])[0].strip() if lines else ""
    m = re.fullmatch(r"PICS\s+([0-5])", header, re.I)
    if not m:
        issues.add("P-HEADER", "Missing or invalid PICS header.", 1, error=True, clause="4.1")
    code = int(m[1]) if m else 0
    meaningful = [
        (i + 1, uncomment(line)[0].strip())
        for i, line in enumerate(lines[1:])
        if uncomment(line)[0].strip()
    ]
    signature = next(
        (
            (line + 1, value)
            for line, value in meaningful
            if value.casefold() == SIGNATURE.casefold()
        ),
        None,
    )
    if signature is None:
        issues.add(
            "P-SIGNATURE", "Missing protocol conformance signature.", 2, error=True, clause="4.2"
        )
    elif signature[0] != 2:
        issues.add(
            "P-SIGNATURE-POSITION",
            "Signature must immediately follow the header.",
            signature[0],
            clause="4.2",
        )
    ending = next(
        (
            i
            for i, line in enumerate(lines)
            if uncomment(line)[0].strip().casefold() == END.casefold()
        ),
        None,
    )
    if ending is None:
        issues.add(
            "P-END", "Missing end-of-conformance line.", len(lines) or 1, error=True, clause="4.2"
        )
    elif any(uncomment(line)[0].strip() for line in lines[ending + 1 :]):
        issues.add(
            "P-END-POSITION",
            "Content follows the end-of-conformance line.",
            ending + 1,
            error=True,
            clause="4.2",
        )
    sections = _split(text, issues)
    general = {
        field: quoted_string(*sections[field], issues) if field in sections else ""
        for field in FIELDS[:4]
    }
    data: dict[str, Any] = {
        "header": {"charset_code": code},
        "general": GeneralInformation.model_validate(general),
    }
    for field in FIELDS[4:]:
        if field in sections:
            body, start = sections[field]
            data[field] = (
                parse_database(body, start, issues)
                if field == "objects"
                else PARSERS[field](body, start, issues)
            )
    if isinstance(source, SourceInfo):
        data["source"] = source.model_copy(update={"raw": source.raw | issues.raw})
    else:
        data["source"] = SourceInfo(
            path=source, encoding=encoding, mode="strict" if strict else "lenient", raw=issues.raw
        )
    try:
        doc = EpicsDocument.model_validate(data)
    except ValidationError as exc:
        issues.add(
            "P-DOCUMENT-MODEL",
            "Document model rejected: " + str(exc.errors()[0]["msg"]),
            error=True,
        )
        # Duplicate identifiers are retained as errors while later valid objects survive.
        objects = data.get("objects", [])
        seen = set()
        unique = []
        for obj in objects:
            ident = str(obj.identifier)
            if ident not in seen:
                unique.append(obj)
                seen.add(ident)
        data["objects"] = unique
        doc = EpicsDocument.model_validate(data)
    issues.diagnostics.extend(doc.diagnostics)
    doc.diagnostics = issues.diagnostics
    return ParseResult(doc, issues.diagnostics)


def parse(
    text_or_bytes: str | bytes, *, strict=False, source: SourceInfo | str | None = None
) -> ParseResult:
    """Parse recoverably without raising for arbitrary input (Clause 4)."""
    try:
        return _parse(text_or_bytes, strict, source)
    except (
        ValueError,
        TypeError,
        OverflowError,
        RecursionError,
        IndexError,
        KeyError,
        AttributeError,
    ) as exc:
        return ParseResult(
            None,
            [
                Diagnostic(
                    code="P-RECOVERY",
                    severity=Severity.ERROR,
                    message="Input could not be recovered: " + str(exc),
                    clause="4",
                )
            ],
        )


def loads(
    text_or_bytes: str | bytes,
    *,
    strict=False,
    raise_on_error=True,
    source: SourceInfo | str | None = None,
) -> EpicsDocument:
    """Read EPICS text/bytes; raise collected errors by default (Clause 4)."""
    result = parse(text_or_bytes, strict=strict, source=source)
    return document_from_result(result, raise_on_error=raise_on_error)


def load(path_or_binary_io: str | Path | BinaryIO, **kwargs) -> EpicsDocument:
    """Read bytes from a path or binary stream (Clause 4.1)."""
    if isinstance(path_or_binary_io, (str, Path)):
        path = Path(path_or_binary_io)
        kwargs.setdefault("source", str(path))
        return loads(path.read_bytes(), **kwargs)
    return loads(path_or_binary_io.read(), **kwargs)
