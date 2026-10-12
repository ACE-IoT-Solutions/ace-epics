"""Recoverable parsers for the Clause 4.5 conformance sections."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any, get_args

from pydantic import ValidationError

from ace_epics.diagnostics import Diagnostic, Severity
from ace_epics.model import (
    Bibb,
    CharacterSet,
    DefaultRestrictions,
    FailTimes,
    ObjectTypeSupport,
    Restrictions,
    ServiceSupport,
    SpecialFunctionality,
)
from ace_epics.model.datalink import DATA_LINK_CLASSES, Other
from ace_epics.model.names import normalize_name
from ace_epics.values import CharacterStringValue, EnumeratedValue, parse_restrictions, parse_value

HEADINGS = [
    "Vendor Name",
    "Product Name",
    "Product Model Number",
    "Product Description",
    "BIBBs Supported",
    "BACnet Standard Application Services Supported",
    "Standard Object Types Supported",
    "Data Link Layer Option",
    "Character Sets Supported",
    "Special Functionality",
    "Default Property Value Restrictions",
    "Fail Times",
    "List of Objects in Test Device",
]
FIELDS = [
    "vendor_name",
    "product_name",
    "product_model_number",
    "product_description",
    "bibbs",
    "services",
    "object_types",
    "data_links",
    "character_sets",
    "special",
    "default_restrictions",
    "fail_times",
    "objects",
]
HEADING_FIELDS = dict(zip(map(normalize_name, HEADINGS), FIELDS, strict=True))
HEADING_FIELDS["standard-application-services-supported"] = "services"
SIGNATURE = "BACnet Protocol Implementation Conformance Statement"
END = "End of " + SIGNATURE


class Issues:
    """Collect located reader diagnostics with consistent strictness (Clause 4)."""

    def __init__(self, strict: bool, diagnostics: list[Diagnostic] | None = None):
        self.strict = strict
        self.raw: dict[str, list[str]] = {}
        self.diagnostics = diagnostics if diagnostics is not None else []

    def add(self, code: str, message: str, line: int | None = None, *, error=False, clause="4.5"):
        """Record a section diagnostic (135.1 Clause 4.5)."""
        self.diagnostics.append(
            Diagnostic(
                code=code,
                message=message,
                clause=clause,
                severity=Severity.ERROR if error or self.strict else Severity.WARNING,
                line=line,
            )
        )

    def extend(self, diagnostics: list[Diagnostic], offset=0):
        """Locate nested value diagnostics in the document (135.1 Clause 4.4)."""
        self.diagnostics.extend(
            d.model_copy(update={"line": d.line + offset if d.line else None}) for d in diagnostics
        )


def uncomment(line: str) -> tuple[str, str | None]:
    """Find comments outside strings, without interpreting section prose (4.2)."""
    quote = None
    for i, char in enumerate(line):
        if quote:
            if char == quote:
                quote = None
        elif char in {'"', "'", "`"}:
            quote = "'" if char == "`" else char
        elif line[i : i + 2] == "--":
            return line[:i], line[i + 2 :].strip()
    return line, None


def records(body: str, start: int):
    """Yield nonempty physical section entries with original line numbers (4.5)."""
    for offset, line in enumerate(body.splitlines()):
        value = uncomment(line)[0].strip()
        if value:
            yield start + offset, value


def quoted_string(text: str, line: int, issues: Issues) -> str:
    """Parse general information without discarding unquoted lenient input (4.5.1)."""
    value, diagnostics = parse_value(text, strict=issues.strict)
    if isinstance(value, CharacterStringValue):
        issues.extend(diagnostics, line - 1)
        return value.value
    issues.add("P-UNQUOTED-STRING", "General information requires a quoted string.", line)
    return uncomment(text)[0].strip()


# Clause titles use CamelCase; normalization also accepts enumeration-style hyphens.
_SERVICE_NAMES = [
    "AcknowledgeAlarm",
    "ConfirmedCOVNotification",
    "ConfirmedEventNotification",
    "GetAlarmSummary",
    "GetEnrollmentSummary",
    "SubscribeCOV",
    "AtomicReadFile",
    "AtomicWriteFile",
    "AddListElement",
    "RemoveListElement",
    "CreateObject",
    "DeleteObject",
    "ReadProperty",
    "ReadPropertyConditional",
    "ReadPropertyMultiple",
    "WriteProperty",
    "WritePropertyMultiple",
    "DeviceCommunicationControl",
    "ConfirmedPrivateTransfer",
    "ConfirmedTextMessage",
    "ReinitializeDevice",
    "VTOpen",
    "VTClose",
    "VTData",
    "Authenticate",
    "RequestKey",
    "I-Am",
    "I-Have",
    "UnconfirmedCOVNotification",
    "UnconfirmedEventNotification",
    "UnconfirmedPrivateTransfer",
    "UnconfirmedTextMessage",
    "TimeSynchronization",
    "Who-Has",
    "Who-Is",
    "ReadRange",
    "UTCTimeSynchronization",
    "LifeSafetyOperation",
    "SubscribeCOVProperty",
    "GetEventInformation",
    "WriteGroup",
    "SubscribeCOVPropertyMultiple",
    "ConfirmedCOVNotificationMultiple",
    "UnconfirmedCOVNotificationMultiple",
    "ConfirmedAuditNotification",
    "UnconfirmedAuditNotification",
    "AuditLogQuery",
    "Who-Am-I",
    "You-Are",
    "AuthRequest",
]


def service_name(name: str) -> str:
    """Recognize conventional service names without a knowledge provider (4.5.3)."""
    words = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", name)
    words = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", words)
    canonical = normalize_name(words)
    aliases = {
        re.sub(r"[-_\s]", "", name).lower(): service_name_direct(name) for name in _SERVICE_NAMES
    }
    return aliases.get(re.sub(r"[-_\s]", "", name).lower(), canonical)


def service_name_direct(name: str) -> str:
    """Parse service name direct declarations (135.1 Clause 4.5.3)."""
    words = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", name)
    words = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", words)
    return normalize_name(words)


def bibbs(body: str, start: int, issues: Issues) -> list[Bibb]:
    """Parse bibbs declarations (135.1 Clause 4.5.2)."""
    result = []
    for line, record in records(body, start):
        words = record.split()
        if len(words) > 1:
            issues.add("P-BIBB-LAYOUT", "Several BIBBs occur on one line.", line)
        result.extend(Bibb.model_validate(word) for word in words)
    return result


def services(body: str, start: int, issues: Issues) -> list[ServiceSupport]:
    """Parse services declarations (135.1 Clause 4.5.3)."""
    result = []
    for line, record in records(body, start):
        words = record.split()
        name, flags = words[0], [s.lower() for s in words[1:]]
        if not flags or any(flag not in {"initiate", "execute"} for flag in flags):
            issues.add(
                "P-SERVICE-FLAGS",
                "A service requires only Initiate and/or Execute flags.",
                line,
                error=True,
            )
            continue
        result.append(
            ServiceSupport(
                name=service_name(name), initiate="initiate" in flags, execute="execute" in flags
            )
        )
    return result


def object_types(body: str, start: int, issues: Issues) -> list[ObjectTypeSupport]:
    """Parse object types declarations (135.1 Clause 4.5.4)."""
    result = []
    for line, record in records(body, start):
        words = record.split()
        index = next(
            (
                i
                for i, w in enumerate(words)
                if w.lower() in {"createable", "creatable", "deleteable"}
            ),
            len(words),
        )
        name = " ".join(words[:index])
        flags = [w.lower() for w in words[index:]]
        if not name or any(flag not in {"createable", "creatable", "deleteable"} for flag in flags):
            issues.add("P-OBJECT-TYPE", "Malformed object-type declaration.", line, error=True)
            continue
        result.append(
            ObjectTypeSupport(
                name=name,
                createable=bool({"createable", "creatable"} & set(flags)),
                deleteable="deleteable" in flags,
            )
        )
    return result


def data_links(body: str, start: int, issues: Issues) -> list[Any]:
    """Parse data links declarations (135.1 Clause 4.5.5)."""
    result = []
    for line, record in records(body, start):
        if re.search(r"\d+(?:\.\d+)?k\b", record, re.I):
            record = re.sub(
                r"(\d+(?:\.\d+)?)k\b", lambda m: str(int(float(m[1]) * 1000)), record, flags=re.I
            )
            issues.add("P-BAUD-K", "Baud-rate k suffix normalized to integer.", line)
        matched = False
        for model in DATA_LINK_CLASSES:
            m = re.fullmatch(model.regex, record, re.I)
            if not m:
                continue
            args = {k: v for k, v in m.groupdict().items() if v is not None}
            # Regex recognition is case-insensitive; restore enum literal spellings.
            for field in ("media", "role", "medium", "variant"):
                if field in args:
                    literals = get_args(model.model_fields[field].annotation)
                    args[field] = next(
                        (x for x in literals if x.casefold() == args[field].casefold()), args[field]
                    )
            if "baud_rates" in args:
                args["baud_rates"] = [int(v) for v in args["baud_rates"].split(",")]
            if "low" in args:
                args["autobaud"] = (int(args.pop("low")), int(args.pop("high")))
            try:
                result.append(model.model_validate(args))
            except ValidationError:
                issues.add("P-DATA-LINK", "Invalid data-link parameters.", line, error=True)
            matched = True
            break
        if not matched:
            missing = (
                record.lower().startswith(("ms/tp", "point-to-point"))
                or "eia-485" in record.lower()
            )
            issues.add(
                "P-DATA-LINK" if missing else "P-UNKNOWN-DATA-LINK",
                "Unrecognized or incomplete data-link declaration.",
                line,
                error=missing and issues.strict,
            )
            result.append(Other(text=record))
    return result


def character_sets(body: str, start: int, issues: Issues) -> list[CharacterSet]:
    """Parse character sets declarations (135.1 Clause 4.5.6)."""
    result = []
    for line, record in records(body, start):
        try:
            result.append(CharacterSet(record))
        except ValueError:
            issues.raw.setdefault("character_sets", []).append(record)
            issues.add("P-CHARACTER-SET", "Unknown character-set declaration: " + record, line)
    return result


def special(body: str, start: int, issues: Issues) -> SpecialFunctionality:
    """Parse special declarations (135.1 Clause 4.5.7)."""
    data: dict[str, Any] = {"unknown": []}
    literals = {
        normalize_name(field.alias or name): name
        for name, field in SpecialFunctionality.model_fields.items()
        if name != "unknown"
    }
    for line, record in records(body, start):
        key, sep, value = record.partition(":")
        field = literals.get(normalize_name(key))
        if field is None:
            issues.add("P-SPECIAL-UNKNOWN", "Unknown special-functionality entry.", line)
            data["unknown"].append(record)
            continue
        if field in {"max_apdu_size", "segmented_requests_window", "segmented_responses_window"}:
            if not sep or not re.fullmatch(r"\d+", value.strip()):
                issues.add(
                    "P-SPECIAL-INTEGER",
                    "Special numeric parameters require nonnegative integers.",
                    line,
                    error=True,
                )
                continue
            data[field] = int(value)
        elif sep:
            issues.add(
                "P-SPECIAL-FLAG", "Special feature flags take no parameter.", line, error=True
            )
        else:
            data[field] = True
    return SpecialFunctionality.model_validate(data)


def restrictions(text: str, line: int, issues: Issues) -> Restrictions:
    """Parse restrictions declarations (135.1 Clause 4.4.2)."""
    value, diags = parse_restrictions(text, strict=issues.strict)
    issues.extend(diags, line - 1)
    data = {
        name: getattr(value, name) for name in type(value).model_fields if name != "allowed_values"
    }
    if value.allowed_values is not None:
        named = []
        for node in value.allowed_values:
            if isinstance(node, EnumeratedValue):
                named.append(node.name)
            else:
                issues.add(
                    "P-ALLOWED-VALUES",
                    "Allowed values require enumeration names.",
                    line,
                    error=True,
                )
        data["allowed_values"] = named
    return Restrictions.model_validate(data)


def defaults(body: str, start: int, issues: Issues) -> DefaultRestrictions:
    """Parse defaults declarations (135.1 Clause 4.5.8)."""
    data: dict[str, Any] = {"extra": {}}
    for line, record in records(body, start):
        match = re.fullmatch(r"(.*?)\s*:?\s*(<.*>)", record)
        if not match:
            issues.add("P-DEFAULT-RESTRICTION", "Malformed default restriction.", line, error=True)
            continue
        name = normalize_name(match[1].rstrip(":").strip()).replace("-", "_")
        value = restrictions(match[2], line, issues)
        if name in DefaultRestrictions.model_fields and name != "extra":
            data[name] = value
        else:
            issues.add("P-DEFAULT-TYPE", "Unknown default restriction datatype.", line)
            data["extra"][name] = value
    return DefaultRestrictions.model_validate(data)


def timers(body: str, start: int, issues: Issues) -> FailTimes:
    """Parse timers declarations (135.1 Clause 4.5.9)."""
    data: dict[str, Any] = {"extra": {}}
    aliases = {
        normalize_name(field.alias or field.serialization_alias or name): name
        for name, field in FailTimes.model_fields.items()
        if name != "extra"
    }
    aliases.update(
        {
            "acknowledgment-fail-time": "acknowledgement_fail_time",
            "autonegotiation-fail-time": "auto_negotiation_fail_time",
            "minimum-on/off-fail-time": "minimum_on_off_time",
        }
    )
    for line, record in records(body, start):
        key, sep, value = record.partition(":")
        name = aliases.get(normalize_name(key))
        value = value.strip()
        if not sep or not re.fullmatch(r"\d+(?:\.\d+)?", value):
            issues.add(
                "P-TIMER-VALUE", "Timers require nonnegative real seconds.", line, error=True
            )
            continue
        if "." not in value:
            issues.add("P-TIMER-INTEGER", "Integer timer coerced to real seconds.", line)
        if name:
            data[name] = float(value)
        else:
            issues.add("P-TIMER-UNKNOWN", "Unknown timer name.", line)
            data["extra"][key.strip()] = float(value)
    missing = (
        set(FailTimes.model_fields)
        - {"extra", "audit_notification_forwarder_fail_time"}
        - set(data)
    )
    if missing:
        issues.add(
            "P-TIMERS-INCOMPLETE", "Missing template timers: " + ", ".join(sorted(missing)), start
        )
    return FailTimes.model_validate(data)


PARSERS: dict[str, Callable[..., Any]] = {
    "bibbs": bibbs,
    "services": services,
    "object_types": object_types,
    "data_links": data_links,
    "character_sets": character_sets,
    "special": special,
    "default_restrictions": defaults,
    "fail_times": timers,
}
