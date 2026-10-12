"""Per-property and datatype default restrictions (Clauses 4.4.2, 4.5.8)."""

from __future__ import annotations

from builtins import list as list_type
from typing import Annotated

from pydantic import Field

from ace_epics.diagnostics import Diagnostic
from ace_epics.values import ValueNode

from .base import EpicsModel, warning
from .names import NamedToken

Length = Annotated[int, Field(strict=True, ge=0)]


class Restrictions(EpicsModel):
    """Restriction values retain their precise value-node datatype (4.4.2)."""

    minimum: ValueNode | None = Field(default=None, description="Minimum writable value (4.4.2).")
    maximum: ValueNode | None = Field(default=None, description="Maximum writable value (4.4.2).")
    resolution: ValueNode | None = Field(default=None, description="Writable resolution (4.4.2).")
    maximum_length_string: Length | None = Field(
        default=None, alias="maximum length string", description="String length limit (4.4.2)."
    )
    maximum_length_list: Length | None = Field(
        default=None, alias="maximum length list", description="List length limit (4.4.2)."
    )
    maximum_length_array: Length | None = Field(
        default=None, alias="maximum length array", description="Array length limit (4.4.2)."
    )
    allowed_values: list[NamedToken] | None = Field(
        default=None, alias="allowed values", description="Allowed enumeration names (4.4.2)."
    )


def merge(default: Restrictions | None, override: Restrictions | None) -> Restrictions:
    """Merge defined override fields over datatype defaults (4.5.8)."""
    values = {name: getattr(default, name) for name in Restrictions.model_fields} if default else {}
    if override:
        values.update(
            {
                name: getattr(override, name)
                for name in Restrictions.model_fields
                if getattr(override, name) is not None
            }
        )
    return Restrictions(**values)


ALLOWED_DEFAULT_RESTRICTIONS = {
    "unsigned_integer": {"minimum", "maximum"},
    "signed_integer": {"minimum", "maximum"},
    "real": {"minimum", "maximum", "resolution"},
    "double": {"minimum", "maximum", "resolution"},
    "date": {"minimum", "maximum"},
    "octet_string": {"maximum_length_string"},
    "character_string": {"maximum_length_string"},
    "list": {"maximum_length_list"},
    "variable_length_array": {"maximum_length_array"},
}


class DefaultRestrictions(EpicsModel):
    """Defaults for the nine datatype keys in Clause 4.5.8."""

    unsigned_integer: Restrictions | None = Field(
        default=None, alias="unsigned-integer", description="Unsigned defaults (4.5.8)."
    )
    signed_integer: Restrictions | None = Field(
        default=None, alias="signed-integer", description="Signed defaults (4.5.8)."
    )
    real: Restrictions | None = Field(default=None, description="Real defaults (4.5.8).")
    double: Restrictions | None = Field(default=None, description="Double defaults (4.5.8).")
    date: Restrictions | None = Field(default=None, description="Date defaults (4.5.8).")
    octet_string: Restrictions | None = Field(
        default=None, alias="octet-string", description="Octet string defaults (4.5.8)."
    )
    character_string: Restrictions | None = Field(
        default=None, alias="character-string", description="Character string defaults (4.5.8)."
    )
    list: Restrictions | None = Field(default=None, description="List defaults (4.5.8).")
    variable_length_array: Restrictions | None = Field(
        default=None, alias="variable-length-array", description="Variable array defaults (4.5.8)."
    )
    extra: dict[str, Restrictions] = Field(
        default_factory=dict, description="Lenient unlisted datatype defaults (4.5.8)."
    )

    def warnings(self) -> list_type[Diagnostic]:
        """Warn about restriction names absent from a datatype's template (4.5.8)."""
        result = []
        for datatype, allowed in ALLOWED_DEFAULT_RESTRICTIONS.items():
            restriction = getattr(self, datatype)
            if restriction is None:
                continue
            for name in Restrictions.model_fields:
                if getattr(restriction, name) is not None and name not in allowed:
                    result.append(
                        warning(
                            "M-DEFAULT-RESTRICTION",
                            f"{datatype} does not list {name} in the standard template",
                            "4.5.8",
                        )
                    )
        return result
