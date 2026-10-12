"""EPICS data models (Clause 4.5); lazy exports keep value/name dependencies acyclic."""

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .conformance import Bibb, ObjectTypeSupport, ServiceSupport, SpecialFunctionality
    from .database import Access, ObjectIdentifier, PropertyEntry, PropertyMetadata, TestObject
    from .datalink import (
        Arcnet,
        BacnetIp,
        BacnetIpv6,
        BacnetSc,
        DataLinkOption,
        Iso8802_3,
        MsTp,
        Other,
        PointToPoint,
        Zigbee,
    )
    from .document import EpicsDocument, SourceInfo
    from .enums import CharacterSet, CharacterSetCode
    from .general import GeneralInformation, PicsHeader
    from .names import NamedToken, normalize_name
    from .restrictions import DefaultRestrictions, Restrictions, merge
    from .timers import FailTimes

_EXPORTS = {
    **dict.fromkeys(
        ["Bibb", "ObjectTypeSupport", "ServiceSupport", "SpecialFunctionality"], "conformance"
    ),
    **dict.fromkeys(
        ["Access", "ObjectIdentifier", "PropertyEntry", "PropertyMetadata", "TestObject"],
        "database",
    ),
    **dict.fromkeys(
        [
            "Arcnet",
            "BacnetIp",
            "BacnetIpv6",
            "BacnetSc",
            "DataLinkOption",
            "Iso8802_3",
            "MsTp",
            "Other",
            "PointToPoint",
            "Zigbee",
        ],
        "datalink",
    ),
    **dict.fromkeys(["EpicsDocument", "SourceInfo"], "document"),
    **dict.fromkeys(["CharacterSet", "CharacterSetCode"], "enums"),
    **dict.fromkeys(["GeneralInformation", "PicsHeader"], "general"),
    **dict.fromkeys(["NamedToken", "normalize_name"], "names"),
    **dict.fromkeys(["DefaultRestrictions", "Restrictions", "merge"], "restrictions"),
    "FailTimes": "timers",
}
__all__ = [
    "Access",
    "Arcnet",
    "BacnetIp",
    "BacnetIpv6",
    "BacnetSc",
    "Bibb",
    "CharacterSet",
    "CharacterSetCode",
    "DataLinkOption",
    "DefaultRestrictions",
    "EpicsDocument",
    "FailTimes",
    "GeneralInformation",
    "Iso8802_3",
    "MsTp",
    "NamedToken",
    "ObjectIdentifier",
    "ObjectTypeSupport",
    "Other",
    "PicsHeader",
    "PointToPoint",
    "PropertyEntry",
    "PropertyMetadata",
    "Restrictions",
    "ServiceSupport",
    "SourceInfo",
    "SpecialFunctionality",
    "TestObject",
    "Zigbee",
    "merge",
    "normalize_name",
]


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(name)
    value = getattr(import_module(f"{__name__}.{_EXPORTS[name]}"), name)
    globals()[name] = value
    return value
