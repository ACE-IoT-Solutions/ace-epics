"""Every data-link literal in Clause 4.5.5 and its parameters."""

from typing import Annotated, ClassVar, Literal

from pydantic import Field, model_validator

from ace_epics.diagnostics import Diagnostic

from .base import EpicsModel, warning

BaudList = Annotated[list[Annotated[int, Field(strict=True)]], Field(min_length=1)]


def _bauds(values: list[int]) -> str:
    return ", ".join(map(str, values))


class Iso8802_3(EpicsModel):
    """ISO 8802-3 media literals (4.5.5)."""

    kind: Literal["iso8802-3"] = Field(default="iso8802-3", description="Kind (4.5.5).")
    media: Literal["10BASE5", "10BASE2", "10BASET", "fiber"] = Field(description="Media (4.5.5).")
    regex: ClassVar[str] = r"^ISO 8802-3, (?P<media>10BASE5|10BASE2|10BASET|fiber)$"

    def canonical_text(self) -> str:
        """Render the standard literal (4.5.5)."""
        return f"ISO 8802-3, {self.media}"


class Arcnet(EpicsModel):
    """ARCNET media; EIA-485 additionally requires baud rates (4.5.5)."""

    kind: Literal["arcnet"] = Field(default="arcnet", description="Kind (4.5.5).")
    media: Literal[
        "coax star",
        "coax bus",
        "twisted pair star",
        "twisted pair bus",
        "fiber star",
        "twisted pair, EIA-485",
    ] = Field(description="Media (4.5.5).")
    baud_rates: BaudList | None = Field(default=None, description="Baud rates (4.5.5).")
    regex: ClassVar[str] = (
        r"^ARCNET, (?P<media>coax star|coax bus|twisted pair star|twisted pair bus|"
        r"fiber star|twisted pair, EIA-485)(?:, Baud rate\(s\): "
        r"(?P<baud_rates>\d+(?:, \d+)*))?$"
    )

    @model_validator(mode="after")
    def rates_match_media(self):
        """Only EIA-485 has a baud-rate parameter (4.5.5)."""
        if (self.media == "twisted pair, EIA-485") != (self.baud_rates is not None):
            raise ValueError("ARCNET EIA-485 requires baud rates; other media forbid them")
        return self

    def canonical_text(self) -> str:
        """Render the standard literal and optional rates (4.5.5)."""
        suffix = f", Baud rate(s): {_bauds(self.baud_rates)}" if self.baud_rates else ""
        return f"ARCNET, {self.media}{suffix}"


class MsTp(EpicsModel):
    """MS/TP manager or subordinate with supported baud rates (4.5.5)."""

    kind: Literal["ms-tp"] = Field(default="ms-tp", description="Kind (4.5.5).")
    role: Literal["manager", "subordinate"] = Field(description="Role (4.5.5).")
    baud_rates: BaudList = Field(description="Baud rates (4.5.5).")
    regex: ClassVar[str] = (
        r"^MS/TP (?P<role>manager|subordinate)\. Baud rate\(s\): (?P<baud_rates>\d+(?:, \d+)*)$"
    )

    def canonical_text(self) -> str:
        """Preserve the period in the standard's literal (4.5.5)."""
        return f"MS/TP {self.role}. Baud rate(s): {_bauds(self.baud_rates)}"

    def warnings(self) -> list[Diagnostic]:
        """Warn if the template's 9600 rate is absent (4.5.5)."""
        return (
            []
            if 9600 in self.baud_rates
            else [warning("M-MSTP-9600", "MS/TP baud rates omit template rate 9600", "4.5.5")]
        )


class PointToPoint(EpicsModel):
    """Point-To-Point with one baud-rate declaration form (4.5.5)."""

    kind: Literal["point-to-point"] = Field(default="point-to-point", description="Kind (4.5.5).")
    medium: Literal["EIA 232", "Modem"] = Field(description="Medium (4.5.5).")
    baud_rates: BaudList | None = Field(default=None, description="Baud rates (4.5.5).")
    autobaud: (
        tuple[Annotated[int, Field(strict=True)], Annotated[int, Field(strict=True)]] | None
    ) = Field(default=None, description="Autobaud (4.5.5).")
    regex: ClassVar[str] = (
        r"^Point-To-Point\. (?P<medium>EIA 232|Modem), (?:Baud rate\(s\): "
        r"(?P<baud_rates>\d+(?:, \d+)*)|Autobaud range: (?P<low>\d+) to (?P<high>\d+))$"
    )

    @model_validator(mode="after")
    def one_rate_form(self):
        """Require exactly one form; autobaud belongs only to modems (4.5.5)."""
        if (self.baud_rates is None) == (self.autobaud is None):
            raise ValueError("exactly one of baud_rates or autobaud is required")
        if self.autobaud is not None:
            if self.medium != "Modem":
                raise ValueError("autobaud is only valid for Modem")
            if self.autobaud[0] > self.autobaud[1]:
                raise ValueError("autobaud minimum exceeds maximum")
        return self

    def canonical_text(self) -> str:
        """Render explicit rates or the modem range (4.5.5)."""
        if self.autobaud is not None:
            rates = f"Autobaud range: {self.autobaud[0]} to {self.autobaud[1]}"
        else:
            rates = f"Baud rate(s): {_bauds(self.baud_rates or [])}"
        return f"Point-To-Point. {self.medium}, {rates}"


class BacnetIp(EpicsModel):
    """BACnet/IP media variant (4.5.5)."""

    kind: Literal["bacnet-ip"] = Field(default="bacnet-ip", description="Kind (4.5.5).")
    variant: Literal["'DIX' Ethernet", "Other"] = Field(description="Variant (4.5.5).")
    regex: ClassVar[str] = r"^BACnet/IP, (?P<variant>'DIX' Ethernet|Other)$"

    def canonical_text(self) -> str:
        """Render the literal (4.5.5)."""
        return f"BACnet/IP, {self.variant}"


class BacnetIpv6(EpicsModel):
    """BACnet/IPv6's single media variant (4.5.5)."""

    kind: Literal["bacnet-ipv6"] = Field(default="bacnet-ipv6", description="Kind (4.5.5).")
    variant: Literal["'DIX' Ethernet"] = Field(
        default="'DIX' Ethernet", description="Variant (4.5.5)."
    )
    regex: ClassVar[str] = r"^BACnet/IPv6, (?P<variant>'DIX' Ethernet)$"

    def canonical_text(self) -> str:
        """Render the literal (4.5.5)."""
        return f"BACnet/IPv6, {self.variant}"


class BacnetSc(EpicsModel):
    """BACnet/SC literal (4.5.5)."""

    kind: Literal["bacnet-sc"] = Field(default="bacnet-sc", description="Kind (4.5.5).")
    regex: ClassVar[str] = r"^BACnet/SC$"

    def canonical_text(self) -> str:
        """Render the literal (4.5.5)."""
        return "BACnet/SC"


class Zigbee(EpicsModel):
    """Zigbee literal (4.5.5)."""

    kind: Literal["zigbee"] = Field(default="zigbee", description="Kind (4.5.5).")
    regex: ClassVar[str] = r"^Zigbee$"

    def canonical_text(self) -> str:
        """Render the literal (4.5.5)."""
        return "Zigbee"


class Other(EpicsModel):
    """Other media with optional lenient descriptive text (4.5.5)."""

    kind: Literal["other"] = Field(default="other", description="Kind (4.5.5).")
    text: str | None = Field(default=None, description="Text (4.5.5).")
    regex: ClassVar[str] = r"^Other(?: (?P<text>.*))?$"

    def canonical_text(self) -> str:
        """Render the literal and captured descriptive text (4.5.5)."""
        return "Other" + (f" {self.text}" if self.text else "")


DataLinkOption = Annotated[
    Iso8802_3 | Arcnet | MsTp | PointToPoint | BacnetIp | BacnetIpv6 | BacnetSc | Zigbee | Other,
    Field(discriminator="kind"),
]
DATA_LINK_CLASSES = (
    Iso8802_3,
    Arcnet,
    MsTp,
    PointToPoint,
    BacnetIp,
    BacnetIpv6,
    BacnetSc,
    Zigbee,
    Other,
)
