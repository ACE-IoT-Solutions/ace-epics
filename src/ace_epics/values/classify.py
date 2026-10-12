"""Pure syntactic shape recognition for Clause 4.4 (decision D7)."""

from ace_epics.values.nodes import (
    BooleanValue,
    DateValue,
    EnumeratedValue,
    GroupValue,
    IntegerValue,
    ObjectIdentifierValue,
    TimeValue,
    UnspecifiedValue,
)


def as_bitstring(group: GroupValue) -> list[bool | None] | None:
    """Recognize Boolean or unspecified elements as supported-bit positions (135.1 Clause 4.4
    and 4.4.1).
    """
    if all(isinstance(n, (BooleanValue, UnspecifiedValue)) for n in group.elements):
        return [n.value if isinstance(n, BooleanValue) else None for n in group.elements]
    return None


def as_datetime(group: GroupValue) -> tuple[DateValue, TimeValue] | None:
    """Recognize an ordered date-and-time pair in either group delimiter (135.1 Clause 4.4 and
    4.4.1).
    """
    if (
        len(group.elements) == 2
        and isinstance(group.elements[0], DateValue)
        and isinstance(group.elements[1], TimeValue)
    ):
        return group.elements[0], group.elements[1]
    return None


def as_object_identifier(group: GroupValue) -> ObjectIdentifierValue | None:
    """Recognize a parenthesis pair containing an object type and instance (135.1 Clause 4.4
    and 4.4.1).
    """
    if group.delimiter == "(" and len(group.elements) == 2:
        first, second = group.elements
        if isinstance(first, EnumeratedValue) and isinstance(
            second, (IntegerValue, UnspecifiedValue)
        ):
            return ObjectIdentifierValue(
                object_type=first.proprietary_number
                if first.proprietary_number is not None
                else first.name,
                instance=second.value if isinstance(second, IntegerValue) else None,
            )
    return None


def as_date(value) -> DateValue | None:
    """Recognize an existing date or a singleton date group (135.1 Clause 4.4 and 4.4.1)."""
    if isinstance(value, DateValue):
        return value
    if (
        isinstance(value, GroupValue)
        and len(value.elements) == 1
        and isinstance(value.elements[0], DateValue)
    ):
        return value.elements[0]
    return None


def as_list_of(group: GroupValue, kind: str | type) -> list | None:
    """Return group elements only when all match the requested kind or node class (135.1 Clause
    4.4 and 4.4.1).
    """
    if all(
        n.kind == kind if isinstance(kind, str) else isinstance(n, kind) for n in group.elements
    ):
        return list(group.elements)
    return None
