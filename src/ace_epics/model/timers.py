"""Fail-time declarations and Clause 6 spelling aliases (4.5.9)."""

import math
from typing import Annotated

from pydantic import AliasChoices, Field, field_validator

from .base import EpicsModel

Seconds = Annotated[float, Field(ge=0, allow_inf_nan=False)]
TIMER_ALIASES = {
    "Acknowledgment Fail Time": "acknowledgement_fail_time",
    "Autonegotiation Fail Time": "auto_negotiation_fail_time",
    "Minimum ON/OFF Fail Time": "minimum_on_off_time",
}


class FailTimes(EpicsModel):
    """Optional nonnegative seconds; completeness belongs to parsing mode (4.5.9)."""

    notification_fail_time: Seconds | None = Field(
        default=None, alias="Notification Fail Time", description="Notification fail time (4.5.9)."
    )
    internal_processing_fail_time: Seconds | None = Field(
        default=None,
        alias="Internal Processing Fail Time",
        description="Internal processing fail time (4.5.9).",
    )
    minimum_on_off_time: Seconds | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "Minimum ON/OFF Time", "Minimum ON/OFF Fail Time", "minimum_on_off_time"
        ),
        serialization_alias="Minimum ON/OFF Time",
        description="Minimum on/off time (4.5.9).",
    )
    schedule_evaluation_fail_time: Seconds | None = Field(
        default=None,
        alias="Schedule Evaluation Fail Time",
        description="Schedule evaluation fail time (4.5.9).",
    )
    external_command_fail_time: Seconds | None = Field(
        default=None,
        alias="External Command Fail Time",
        description="External command fail time (4.5.9).",
    )
    program_object_state_change_fail_time: Seconds | None = Field(
        default=None,
        alias="Program Object State Change Fail Time",
        description="Program state change fail time (4.5.9).",
    )
    acknowledgement_fail_time: Seconds | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "Acknowledgement Fail Time",
            "Acknowledgment Fail Time",
            "acknowledgement_fail_time",
            "acknowledgment_fail_time",
        ),
        serialization_alias="Acknowledgement Fail Time",
        description="Acknowledgement fail time (4.5.9, 6.3).",
    )
    subordinate_proxy_confirm_interval: Seconds | None = Field(
        default=None,
        alias="Subordinate Proxy Confirm Interval",
        description="Subordinate proxy confirmation interval (4.5.9).",
    )
    unconfirmed_response_fail_time: Seconds | None = Field(
        default=None,
        alias="Unconfirmed Response Fail Time",
        description="Unconfirmed response fail time (4.5.9).",
    )
    channel_write_fail_time: Seconds | None = Field(
        default=None,
        alias="Channel Write Fail Time",
        description="Channel write fail time (4.5.9).",
    )
    auto_negotiation_fail_time: Seconds | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "Auto Negotiation Fail Time", "Autonegotiation Fail Time", "auto_negotiation_fail_time"
        ),
        serialization_alias="Auto Negotiation Fail Time",
        description="Autonegotiation fail time (4.5.9, 6.3).",
    )
    activate_changes_fail_time: Seconds | None = Field(
        default=None,
        alias="Activate Changes Fail Time",
        description="Activate changes fail time (4.5.9).",
    )
    foreign_device_registration_fail_time: Seconds | None = Field(
        default=None,
        alias="Foreign Device Registration Fail Time",
        description="Foreign device registration fail time (4.5.9).",
    )
    audit_notification_forwarder_fail_time: Seconds | None = Field(
        default=None,
        alias="Audit Notification Forwarder Fail Time",
        description="Audit notification forwarder fail time (6.3.14).",
    )
    extra: dict[str, float] = Field(
        default_factory=dict, description="Unrecognized lenient timers (4.5.9)."
    )

    @field_validator("extra")
    @classmethod
    def extra_nonnegative(cls, values: dict[str, float]) -> dict[str, float]:
        """Apply timer bounds also to lenient extension names (4.5.9)."""
        if any(not math.isfinite(value) or value < 0 for value in values.values()):
            raise ValueError("extra timer values must be finite and nonnegative")
        return values
