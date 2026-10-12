"""Complete I/O-free EPICS document and convenience queries (Clause 4.5)."""

from pydantic import AliasChoices, Field, model_validator

from ace_epics.diagnostics import Diagnostic

from .base import EpicsModel, warning
from .conformance import Bibb, ObjectTypeSupport, ServiceSupport, SpecialFunctionality
from .database import ObjectIdentifier, TestObject
from .datalink import DataLinkOption
from .enums import CharacterSet
from .general import GeneralInformation, PicsHeader
from .names import NamedToken, normalize_name
from .restrictions import DefaultRestrictions
from .timers import FailTimes


class SourceInfo(EpicsModel):
    """Optional origin metadata; reading files is outside the model (Clause 4)."""

    path: str | None = Field(default=None, description="Input location (Clause 4).")
    encoding: str | None = Field(default=None, description="Decoded input encoding (4.1).")
    mode: str | None = Field(default=None, description="Parser mode (D1).")
    raw: dict[str, list[str]] = Field(
        default_factory=dict, description="Unrecognized lenient source entries (4.5)."
    )


class EpicsDocument(EpicsModel):
    """Every section in printed order with nonserialized diagnostics (Clause 4.5)."""

    header: PicsHeader = Field(default_factory=PicsHeader, description="PICS header (4.1).")
    general: GeneralInformation = Field(
        alias="General Information", description="Product information (4.5.1)."
    )
    bibbs: list[Bibb] = Field(
        default_factory=list, alias="BIBBs Supported", description="BIBB declarations (4.5.2)."
    )
    services: list[ServiceSupport] = Field(
        default_factory=list,
        validation_alias=AliasChoices(
            "BACnet Standard Application Services Supported",
            "Standard Application Services Supported",
            "services",
        ),
        serialization_alias="BACnet Standard Application Services Supported",
        description="Services (4.5.3).",
    )
    object_types: list[ObjectTypeSupport] = Field(
        default_factory=list,
        alias="Standard Object Types Supported",
        description="Object types (4.5.4).",
    )
    data_links: list[DataLinkOption] = Field(
        default_factory=list, alias="Data Link Layer Option", description="Data links (4.5.5)."
    )
    character_sets: list[CharacterSet] = Field(
        default_factory=list,
        alias="Character Sets Supported",
        description="Supported character sets (4.5.6).",
    )
    special: SpecialFunctionality = Field(
        default_factory=SpecialFunctionality,
        alias="Special Functionality",
        description="Special features (4.5.7).",
    )
    default_restrictions: DefaultRestrictions = Field(
        default_factory=DefaultRestrictions,
        alias="Default Property Value Restrictions",
        description="Datatype defaults (4.5.8).",
    )
    fail_times: FailTimes = Field(
        default_factory=FailTimes, alias="Fail Times", description="Timer declarations (4.5.9)."
    )
    objects: list[TestObject] = Field(
        default_factory=list,
        alias="List of Objects in Test Device",
        description="Test database (4.5.10).",
    )
    diagnostics: list[Diagnostic] = Field(
        default_factory=list, exclude=True, description="Nonserialized warnings and errors (14)."
    )
    source: SourceInfo | None = Field(default=None, description="Input origin metadata (Clause 4).")

    @model_validator(mode="after")
    def consistency_and_warnings(self):
        """Reject duplicate identifiers and collect model advisories (4.5)."""
        ids = [str(obj.identifier) for obj in self.objects]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate object identifier")
        findings = []
        devices = self.objects_of_type("device")
        if len(devices) != 1:
            findings.append(
                warning(
                    "M-DEVICE-COUNT", f"Expected one Device object; found {len(devices)}", "4.5.10"
                )
            )
        for section in ("bibbs", "services", "object_types", "character_sets"):
            entries = getattr(self, section)
            names = [
                entry.canonical
                if isinstance(entry, NamedToken)
                else entry.name.canonical
                if isinstance(entry, (ServiceSupport, ObjectTypeSupport))
                else str(entry)
                for entry in entries
            ]
            if len(names) != len(set(names)):
                findings.append(
                    warning("M-DUPLICATE-DECLARATION", f"Duplicate declaration in {section}", "4.5")
                )
        for component in [*self.bibbs, *self.data_links, self.special, self.default_restrictions]:
            findings.extend(component.warnings())
        existing = {(d.code, d.message) for d in self.diagnostics}
        self.diagnostics.extend(d for d in findings if (d.code, d.message) not in existing)
        return self

    @property
    def device(self) -> TestObject | None:
        """Return the first Device object, without external knowledge (4.5.10)."""
        return next(iter(self.objects_of_type("device")), None)

    def get_object(self, identifier: ObjectIdentifier) -> TestObject | None:
        """Find an object with the given identifier (4.5.10)."""
        return next((obj for obj in self.objects if obj.identifier == identifier), None)

    def objects_of_type(self, name: str | NamedToken | int) -> list[TestObject]:
        """Return all objects of a normalized type (4.5.10)."""
        canonical = (
            name
            if isinstance(name, int)
            else name.canonical
            if isinstance(name, NamedToken)
            else normalize_name(name)
        )
        return [
            obj
            for obj in self.objects
            if (obj.object_type if isinstance(obj.object_type, int) else obj.object_type.canonical)
            == canonical
        ]

    def supports_service(
        self, name: str, *, initiate: bool | None = None, execute: bool | None = None
    ) -> bool:
        """Whether a service declaration matches the requested directions (4.5.3)."""
        canonical = normalize_name(name)
        return any(
            s.name.canonical == canonical
            and (initiate is None or s.initiate == initiate)
            and (execute is None or s.execute == execute)
            for s in self.services
        )

    def supports_bibb(self, name: str) -> bool:
        """Whether a normalized BIBB is declared (4.5.2)."""
        return any(b.canonical == normalize_name(name) for b in self.bibbs)

    def supports_object_type(self, name: str) -> bool:
        """Whether a normalized object type is declared (4.5.4)."""
        return any(t.name.canonical == normalize_name(name) for t in self.object_types)

    def __eq__(self, other: object) -> bool:
        """Compare semantic content, excluding source and diagnostic metadata (D7)."""
        if not isinstance(other, EpicsDocument):
            return False
        left = {k: v for k, v in self.__dict__.items() if k not in {"source", "diagnostics"}}
        right = {k: v for k, v in other.__dict__.items() if k not in {"source", "diagnostics"}}
        return left == right
