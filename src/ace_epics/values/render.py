"""Native EPICS value rendering (135.1 Clauses 4.3-4.4.1)."""

from __future__ import annotations

import calendar
from enum import StrEnum

from ace_epics.values.nodes import (
    BooleanValue,
    CharacterStringValue,
    ContextTaggedValue,
    DateRangeValue,
    DateValue,
    EmptyElement,
    EnumeratedValue,
    GroupValue,
    IntegerValue,
    NullValue,
    ObjectIdentifierValue,
    OctetStringValue,
    RealValue,
    TimeValue,
    UnspecifiedValue,
    WildcardValue,
)


class Style(StrEnum):
    """Canonical or spelling-preserving rendering of EPICS values (135.1 Clause 4.4 and 4.4.1)."""

    CANONICAL = "canonical"
    PRESERVING = "preserving"


Canonical = Style.CANONICAL
Preserving = Style.PRESERVING


def render(node, style: Style | str = Canonical) -> str:
    """Render an AST value; preserving style retains cosmetic lexical choices. (135.1 Clause
    4.4 and 4.4.1).
    """
    preserving = style == Preserving
    if isinstance(node, NullValue):
        return "NULL"
    if isinstance(node, BooleanValue):
        return (
            ("T" if node.value else "F")
            if preserving and node.short
            else ("TRUE" if node.value else "FALSE")
        )
    if isinstance(node, IntegerValue):
        return str(node.value)
    if isinstance(node, RealValue):
        if preserving and node.text:
            return node.text
        text = format(node.value, "f")
        return text if "." in text else text + ".0"
    if isinstance(node, OctetStringValue):
        digits = node.value.hex().upper()
        if preserving and node.odd_length and digits.startswith("0"):
            digits = digits[1:]
        return "X'" + digits + "'"
    if isinstance(node, CharacterStringValue):
        quote = node.quote if preserving else ('"' if '"' not in node.value else "'")
        closer = '"' if quote == '"' else "'"
        if closer in node.value or "\n" in node.value or "\r" in node.value:
            raise ValueError(
                "EPICS character strings cannot contain their closing quote or a newline"
            )
        return quote + node.value + closer
    if isinstance(node, EnumeratedValue):
        return node.name.original if preserving and node.name.original else node.name.name
    if isinstance(node, WildcardValue):
        return "*"
    if isinstance(node, UnspecifiedValue):
        return "?"
    if isinstance(node, EmptyElement):
        return ""
    if isinstance(node, DateValue):

        def field(value, names=None):
            if isinstance(value, WildcardValue) or value is None:
                return "*"
            return names[value] if names else str(value)

        date = (
            f"{field(node.day)}-{field(node.month, list(calendar.month_name))}-{field(node.year)}"
        )
        if node.weekday is not None:
            date = field(node.weekday, ["", *list(calendar.day_name)]) + ", " + date
        return date if preserving and not node.parenthesised else "(" + date + ")"
    if isinstance(node, TimeValue):

        def part(value):
            return "*" if isinstance(value, WildcardValue) or value is None else f"{value:02d}"

        text = part(node.hour) + ":" + part(node.minute)
        if preserving and node.precision == -1:
            return text
        text += ":" + part(node.second)
        if preserving and node.precision == 0:
            return text
        text += "." + (
            str(node.hundredth // 10)
            if preserving and node.precision == 1 and isinstance(node.hundredth, int)
            else part(node.hundredth)
        )
        return text
    if isinstance(node, DateRangeValue):
        return render(node.start, style) + "-" + render(node.end, style)
    if isinstance(node, ObjectIdentifierValue):
        object_type = (
            f"proprietary {node.object_type}"
            if isinstance(node.object_type, int)
            else node.object_type.name
        )
        return f"({object_type}, {node.instance if node.instance is not None else '?'})"
    if isinstance(node, ContextTaggedValue):
        return f"[{node.tag}] " + render(node.value, style)
    if isinstance(node, GroupValue):
        contents = ", ".join(render(n, style) for n in node.elements)
        if (node.elements and isinstance(node.elements[-1], EmptyElement)) or (
            preserving and node.trailing_comma
        ):
            contents += ","
        return node.delimiter + contents + ("}" if node.delimiter == "{" else ")")
    raise TypeError(f"Unsupported value node: {type(node).__name__}")
