"""Canonical and preserving native EPICS serialization (Clause 4)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import BinaryIO

from ace_epics.encoding import encode
from ace_epics.model import Access, EpicsDocument, PropertyMetadata, Restrictions
from ace_epics.model.restrictions import ALLOWED_DEFAULT_RESTRICTIONS
from ace_epics.model.timers import FailTimes
from ace_epics.values import Canonical, CharacterStringValue, GroupValue, Style, render

from .sections import END, FIELDS, HEADINGS, SIGNATURE


def render_bounds(restrictions: Restrictions, style: Style | str = Canonical) -> str:
    """Render the model's typed bounds and named enumeration choices (4.4.2)."""
    items = []
    for name in Restrictions.model_fields:
        value = getattr(restrictions, name)
        if value is None:
            continue
        if name == "allowed_values":
            text = ", ".join(str(n) for n in value)
        elif isinstance(value, int):
            text = str(value)
        else:
            text = render(value, style)
        items.append(name.replace("_", " ") + ": " + text)
    return "<" + "; ".join(items) + ">"


def _string(value: str, style: Style | str = Canonical) -> str:
    return render(CharacterStringValue(value=value), style)


def _metadata_suffix(metadata, style: Style | str) -> str:
    suffix = (" " + str(metadata.access)) if metadata.access != Access.R else ""
    if metadata.restrictions is not None:
        suffix += " " + render_bounds(metadata.restrictions, style)
    comment = " ".join(
        (["@not-readable"] if metadata.not_readable else [])
        + ([metadata.comment] if metadata.comment else [])
    )
    if comment:
        if "\n" in comment or "\r" in comment:
            raise ValueError("EPICS property comments cannot contain newlines")
        suffix += " -- " + comment
    return suffix


def dumps(
    doc: EpicsDocument,
    *,
    style: Style | str = Canonical,
    line_ending="\r\n",
    charset_code: int | None = None,
) -> str:
    """Render all sections in printed order; unsupported strings raise (Clause 4)."""
    code = doc.header.charset_code if charset_code is None else charset_code
    if code not in range(6):
        raise ValueError("charset_code must be 0 through 5")
    if line_ending not in {"\r\n", "\n", "\r"}:
        raise ValueError("unsupported line ending")
    lines = [f"PICS {code}", SIGNATURE]
    for heading, field in zip(HEADINGS[:4], FIELDS[:4], strict=True):
        lines.append(heading + ": " + _string(getattr(doc.general, field), style))
    bodies = {}
    bodies["bibbs"] = [
        b.raw if style == "preserving" and b.raw else b.canonical.upper() for b in doc.bibbs
    ]
    width = max((len(s.name.canonical) for s in doc.services), default=0)
    bodies["services"] = [
        s.name.canonical.ljust(width)
        + " "
        + ("Initiate " if s.initiate else "")
        + ("Execute" if s.execute else "")
        for s in doc.services
    ]
    bodies["object_types"] = [
        str(o.name)
        + (" Createable" if o.createable else "")
        + (" Deleteable" if o.deleteable else "")
        for o in doc.object_types
    ]
    bodies["data_links"] = [option.canonical_text() for option in doc.data_links]
    bodies["character_sets"] = [str(c) for c in doc.character_sets]
    special = []
    for name, field in type(doc.special).model_fields.items():
        value = getattr(doc.special, name)
        if name == "unknown":
            continue
        if value is None or value is False:
            continue
        special.append((field.alias or name) + ((": " + str(value)) if type(value) is int else ""))
    special.extend(doc.special.unknown)
    bodies["special"] = special
    defaults = []
    for name in ALLOWED_DEFAULT_RESTRICTIONS:
        restriction = getattr(doc.default_restrictions, name)
        if restriction is not None:
            defaults.append(name.replace("_", "-") + ": " + render_bounds(restriction, style))
    defaults.extend(
        name + ": " + render_bounds(value, style)
        for name, value in doc.default_restrictions.extra.items()
    )
    bodies["default_restrictions"] = defaults
    timers = []
    for name, field in FailTimes.model_fields.items():
        if name == "extra":
            continue
        value = getattr(doc.fail_times, name)
        if value is None:
            continue
        text = format(Decimal(str(value)), "f")
        if "." not in text:
            text += ".0"
        timers.append((field.serialization_alias or field.alias or name) + ": " + text)
    for name, value in doc.fail_times.extra.items():
        text = format(Decimal(str(value)), "f")
        timers.append(name + ": " + (text if "." in text else text + ".0"))
    bodies["fail_times"] = timers
    objects = []
    for obj in doc.objects:
        typ = (
            "proprietary " + str(obj.object_type)
            if isinstance(obj.object_type, int)
            else str(obj.object_type)
        )
        objects.append("{")
        for name, text in [
            ("object-identifier", str(obj.identifier)),
            ("object-name", _string(obj.name, style)),
            ("object-type", typ),
        ]:
            metadata = obj.header_metadata.get(name, PropertyMetadata())
            objects.append("  " + name + ": " + text + _metadata_suffix(metadata, style))
        for prop in obj.properties:
            text = render(prop.value, style)
            if len(text) > 100 and isinstance(prop.value, GroupValue):
                closer = "}" if prop.value.delimiter == "{" else ")"
                text = (
                    prop.value.delimiter
                    + "\n"
                    + ",\n".join("    " + render(n, style) for n in prop.value.elements)
                    + "\n  "
                    + closer
                )
            suffix = _metadata_suffix(prop, style)
            objects.extend(("  " + str(prop.name) + ": " + text + suffix).splitlines())
        objects.append("}")
    bodies["objects"] = objects
    for heading, field in zip(HEADINGS[4:], FIELDS[4:], strict=True):
        lines.append(heading + ": {")
        lines.extend("  " + entry.rstrip() for entry in bodies[field])
        lines.append("}")
    lines.append(END)
    return line_ending.join(lines) + line_ending


def dump(doc: EpicsDocument, path_or_binary_io: str | Path | BinaryIO, **kwargs) -> None:
    """Encode BOM-free native EPICS to a binary path/stream (Clause 4.1)."""
    text = dumps(doc, **kwargs)
    code = kwargs.get("charset_code", doc.header.charset_code)
    content = encode(text, doc.header.charset_code if code is None else code)
    if isinstance(path_or_binary_io, (str, Path)):
        Path(path_or_binary_io).write_bytes(content)
    else:
        path_or_binary_io.write(content)
