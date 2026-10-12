"""Recoverable ordered object/property parsing (Clause 4.5.10)."""

from __future__ import annotations

import re

from pydantic import ValidationError

from ace_epics.lexer import Token, tokenize
from ace_epics.lexer import TokenKind as K
from ace_epics.model import Access, ObjectIdentifier, PropertyEntry, PropertyMetadata, TestObject
from ace_epics.model.names import normalize_name
from ace_epics.values import (
    CharacterStringValue,
    EnumeratedValue,
    ObjectIdentifierValue,
    UnspecifiedValue,
    parse_value,
)

from .sections import Issues, restrictions


def _property_start(tokens: list[Token], i: int) -> bool:
    if i >= len(tokens) or tokens[i].kind != K.WORD or tokens[i].text[:1].isdigit():
        return False
    j = i
    while j < len(tokens) and tokens[j].kind == K.WORD:
        j += 1
    return j < len(tokens) and tokens[j].kind == K.COLON


def _object_start(tokens: list[Token], i: int) -> bool:
    i += 1
    while i < len(tokens) and tokens[i].kind in {K.NEWLINE, K.COMMENT}:
        i += 1
    return _property_start(tokens, i) and normalize_name(tokens[i].text) in {
        "object-identifier",
        "object-name",
        "object-type",
    }


def _properties(tokens: list[Token], issues: Issues) -> list[PropertyEntry]:
    result = []
    i = 0
    while i < len(tokens):
        if tokens[i].kind in {K.NEWLINE, K.COMMENT, K.COMMA, K.EOF}:
            i += 1
            continue
        if not _property_start(tokens, i):
            issues.add(
                "P-PROPERTY", "Expected a property name and colon.", tokens[i].line, error=True
            )
            while i < len(tokens) and tokens[i].kind != K.NEWLINE:
                i += 1
            continue
        head = tokens[i]
        name_words = []
        while i < len(tokens) and tokens[i].kind == K.WORD:
            name_words.append(tokens[i].text)
            i += 1
        name = " ".join(name_words)
        if name.startswith(("...", "…")):
            issues.add("P-ELLIPSIS", "Leading property ellipsis removed.", head.line)
            name = name[3:] if name.startswith("...") else name[1:]
        i += 1
        value_tokens = []
        stack = []
        comment = None
        while i < len(tokens):
            token = tokens[i]
            if token.kind == K.NEWLINE:
                j = i + 1
                while j < len(tokens) and tokens[j].kind in {K.NEWLINE, K.COMMENT}:
                    j += 1
                if not stack and value_tokens:
                    i += 1
                    break
                if not stack and not value_tokens and _property_start(tokens, j):
                    i = j
                    break
                if stack and _property_start(tokens, j):
                    issues.add(
                        "P-VALUE-UNBALANCED",
                        "Unbalanced property value recovered before the next property.",
                        head.line,
                        error=True,
                    )
                    value_tokens.extend(
                        Token(kind, "", token.line, token.column) for kind in reversed(stack)
                    )
                    i = j
                    break
                i += 1
                continue
            if token.kind == K.COMMENT:
                comment = (
                    token.value
                    if token.value is not None
                    else token.text.removeprefix("--").strip()
                )
                i += 1
                continue
            if token.kind in {K.LBRACE, K.LPAREN, K.LBRACK}:
                stack.append(
                    {K.LBRACE: K.RBRACE, K.LPAREN: K.RPAREN, K.LBRACK: K.RBRACK}[token.kind]
                )
            elif token.kind in {K.RBRACE, K.RPAREN, K.RBRACK}:
                if stack and stack[-1] == token.kind:
                    stack.pop()
                elif not stack:
                    issues.add(
                        "P-VALUE-CLOSER",
                        "Unexpected value closing delimiter.",
                        token.line,
                        error=True,
                    )
            value_tokens.append(token)
            i += 1
        restriction = None
        access = Access.R
        # Remove angle-bracket restrictions independently of marker placement.
        lt = next((j for j, t in enumerate(value_tokens) if t.kind == K.LT), None)
        if lt is not None:
            gt = next(
                (j for j in range(lt + 1, len(value_tokens)) if value_tokens[j].kind == K.GT),
                len(value_tokens) - 1,
            )
            text = " ".join(t.text for t in value_tokens[lt : gt + 1])
            restriction = restrictions(text, head.line, issues)
            value_tokens = value_tokens[:lt] + value_tokens[gt + 1 :]
        if (
            len(value_tokens) > 1
            and value_tokens[-1].kind == K.WORD
            and value_tokens[-1].text.upper() in {"R", "W", "C"}
        ):
            marker = value_tokens.pop()
            access = Access(marker.text.upper())
            if access == Access.R:
                issues.add(
                    "P-READONLY-MARKER",
                    "Explicit R marker accepted; native read-only has no marker.",
                    marker.line,
                )
        if not value_tokens:
            issues.add("P-PROPERTY-VALUE", "Missing property value.", head.line, error=True)
            value = UnspecifiedValue()
        else:
            value, diagnostics = parse_value(value_tokens, strict=issues.strict)
            issues.extend(diagnostics)
        if (
            name == "object-type"
            and isinstance(value, EnumeratedValue)
            and value.proprietary_number is None
        ):
            match = re.fullmatch(r"proprietary[-\s]+(?:object-type-)?(\d+)", value.name.canonical)
            if match:
                value = value.model_copy(update={"proprietary_number": int(match[1])})
        if comment is not None:
            comment = comment.strip()
        if comment and comment.startswith("--"):
            comment = comment[2:].strip()
        unreadable = bool(comment and re.search(r"(?:^|\s)@not-readable(?:\s|$)", comment))
        if unreadable and comment is not None:
            comment = re.sub(r"(?:^|\s)@not-readable(?:\s|$)", " ", comment).strip() or None
        result.append(
            PropertyEntry(
                name=name,
                value=value,
                access=access,
                restrictions=restriction,
                comment=comment,
                not_readable=unreadable,
            )
        )
    return result


def _object(tokens: list[Token], issues: Issues) -> TestObject | None:
    properties = _properties(tokens, issues)
    names = [entry.name.canonical for entry in properties[:3]]
    if names != ["object-identifier", "object-name", "object-type"]:
        issues.add(
            "P-OBJECT-HEADERS",
            "First object properties must be identifier, name, and type in that order.",
            tokens[0].line if tokens else None,
            error=True,
        )
        return None
    identifier, name, typ = (entry.value for entry in properties[:3])
    if not isinstance(identifier, ObjectIdentifierValue) or identifier.instance is None:
        issues.add(
            "P-OBJECT-IDENTIFIER",
            "Object identifier requires a type and instance.",
            tokens[0].line,
            error=True,
        )
        return None
    if not isinstance(name, CharacterStringValue) or not isinstance(typ, EnumeratedValue):
        issues.add(
            "P-OBJECT-HEADERS",
            "Object name must be a string and object type an enumeration.",
            tokens[0].line,
            error=True,
        )
        return None
    object_type = typ.proprietary_number if typ.proprietary_number is not None else typ.name
    try:
        return TestObject(
            identifier=ObjectIdentifier(
                object_type=identifier.object_type, instance=identifier.instance
            ),
            name=name.value,
            object_type=object_type,
            properties=properties[3:],
            header_metadata={
                entry.name.canonical: PropertyMetadata(
                    **entry.model_dump(exclude={"name", "value"})
                )
                for entry in properties[:3]
            },
        )
    except ValidationError as exc:
        issues.add(
            "P-OBJECT-MODEL",
            "Invalid object: " + str(exc.errors()[0]["msg"]),
            tokens[0].line,
            error=True,
        )
        return None


def parse_database(body: str, start: int, issues: Issues) -> list[TestObject]:
    """Parse balanced blocks, resynchronizing at a new object header (4.5.10)."""
    tokens, diagnostics = tokenize(body, strict=issues.strict)
    issues.extend(diagnostics, start - 1)
    tokens = [
        Token(
            t.kind, t.text, t.line + start - 1, t.column, t.value, t.terminated, t.quote, t.offset
        )
        for t in tokens
    ]
    starts = [
        i for i, token in enumerate(tokens) if token.kind == K.LBRACE and _object_start(tokens, i)
    ]
    result = []
    if not starts:
        significant = [t for t in tokens if t.kind not in {K.NEWLINE, K.COMMENT, K.COMMA, K.EOF}]
        if significant:
            issues.add(
                "P-DATABASE-ENTRY",
                "Expected a braced object block.",
                significant[0].line,
                error=True,
            )
        return result
    for token in tokens[: starts[0]]:
        if token.kind not in {K.NEWLINE, K.COMMENT, K.COMMA}:
            issues.add(
                "P-DATABASE-ENTRY", "Expected a braced object block.", token.line, error=True
            )
    for position, begin in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(tokens)
        region = tokens[begin + 1 : end]
        closers = [i for i, t in enumerate(region) if t.kind == K.RBRACE]
        if closers:
            closing = closers[-1]
            block = region[:closing]
            for token in region[closing + 1 :]:
                if token.kind not in {K.NEWLINE, K.COMMENT, K.COMMA, K.EOF}:
                    issues.add(
                        "P-DATABASE-ENTRY",
                        "Unexpected content after object.",
                        token.line,
                        error=True,
                    )
        else:
            issues.add(
                "P-OBJECT-BRACE", "Object block is not closed.", tokens[begin].line, error=True
            )
            block = region
        obj = _object(block, issues)
        if obj is not None:
            result.append(obj)
    return result
