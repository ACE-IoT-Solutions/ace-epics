"""Declared BIBBs, services, object types, and special features (Clause 4.5)."""

import re
from typing import Annotated

from pydantic import AliasChoices, Field, model_validator

from ace_epics.diagnostics import Diagnostic

from .base import EpicsModel, warning
from .names import NamedToken

NonnegativeInt = Annotated[int, Field(strict=True, ge=0)]


class Bibb(NamedToken):
    """A BIBB name; unknown Annex K names remain representable (4.5.2.1)."""

    def warnings(self) -> list[Diagnostic]:
        """Warn about nonstandard name shapes without imposing Annex K (4.5.2.1)."""
        if not re.fullmatch(r"[A-Za-z]+(?:-[A-Za-z0-9]+)+-[AB]", self.canonical.upper()):
            return [
                warning(
                    "M-BIBB-NAME",
                    f"Unrecognized BIBB name shape: {self.raw or self.canonical}",
                    "4.5.2.1",
                )
            ]
        return []


class ServiceSupport(EpicsModel):
    """A service with at least one declared direction (4.5.3)."""

    name: NamedToken = Field(description="Service name (4.5.3).")
    initiate: bool = Field(
        default=False, alias="Initiate", description="Initiates service (4.5.3)."
    )
    execute: bool = Field(default=False, alias="Execute", description="Executes service (4.5.3).")

    @model_validator(mode="after")
    def direction_required(self):
        """Reject a service with neither direction (4.5.3)."""
        if not (self.initiate or self.execute):
            raise ValueError("a supported service requires Initiate or Execute")
        return self


class ObjectTypeSupport(EpicsModel):
    """An object-type declaration and dynamic creation flags (4.5.4)."""

    name: NamedToken = Field(description="Object type name (4.5.4).")
    createable: bool = Field(
        default=False,
        validation_alias=AliasChoices("Createable", "Creatable", "createable", "creatable"),
        serialization_alias="Createable",
        description="Dynamic creation (4.5.4, D18).",
    )
    deleteable: bool = Field(
        default=False, alias="Deleteable", description="Dynamic deletion (4.5.4)."
    )


class SpecialFunctionality(EpicsModel):
    """Optional numeric parameters and feature declarations (4.5.7)."""

    max_apdu_size: NonnegativeInt | None = Field(
        default=None,
        alias="Maximum APDU size in octets",
        description="Maximum APDU length (4.5.7).",
    )
    segmented_requests_window: NonnegativeInt | None = Field(
        default=None,
        alias="Segmented Requests Supported, window size",
        description="Request segmentation window (4.5.7).",
    )
    segmented_responses_window: NonnegativeInt | None = Field(
        default=None,
        alias="Segmented Responses Supported, window size",
        description="Response segmentation window (4.5.7).",
    )
    router: bool = Field(default=False, alias="Router", description="Routing support (4.5.7).")
    bacnet_ip_bbmd: bool = Field(
        default=False, alias="BACnet/IP BBMD", description="IPv4 BBMD (4.5.7)."
    )
    bacnet_ipv6_bbmd: bool = Field(
        default=False, alias="BACnet/IPV6 BBMD", description="IPv6 BBMD (4.5.7)."
    )
    bacnet_sc_hub: bool = Field(default=False, alias="BACnet/SC Hub", description="SC hub (4.5.7).")
    bacnet_sc_direct_connect: bool = Field(
        default=False,
        alias="BACnet/SC Direct Connect",
        description="SC direct connections (4.5.7).",
    )
    unknown: list[str] = Field(
        default_factory=list, description="Unrecognized lenient input (4.5.7)."
    )

    def warnings(self) -> list[Diagnostic]:
        """Advise about Clause 135 window ranges without rejecting EPICS (4.5.7)."""
        return [
            warning("M-WINDOW-RANGE", f"{field} outside BACnet window range 1..127", "4.5.7")
            for field in ("segmented_requests_window", "segmented_responses_window")
            if (value := getattr(self, field)) is not None and not 1 <= value <= 127
        ]
