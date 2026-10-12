"""Canonical EPICS names with preserved source spelling (Clause 4.4i, D11)."""

import re
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


def normalize_name(value: str) -> str:
    """Normalize case, spaces, underscores, and repeated separators (Clause 4.4i)."""
    return re.sub(r"[-_\s]+", "-", value.strip().lower())


class NamedToken(BaseModel):
    """A hashable canonical name and its original spelling (Clause 4.4i)."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)
    canonical: str = Field(
        validation_alias=AliasChoices("canonical", "name"), description="Normalized token (4.4i)."
    )
    raw: str | None = Field(
        default=None,
        validation_alias=AliasChoices("raw", "original"),
        description="Source token spelling (4.4i).",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize(cls, value: Any) -> Any:
        """Accept a string or token mapping while preserving its spelling (4.4i)."""
        if isinstance(value, str):
            return {"canonical": normalize_name(value), "raw": value}
        if isinstance(value, dict):
            result = dict(value)
            key = "canonical" if "canonical" in result else "name"
            if key in result:
                original = result[key]
                result[key] = normalize_name(original)
                if "raw" not in result and "original" not in result:
                    result["raw"] = original
            return result
        return value

    @property
    def name(self) -> str:
        """Compatibility spelling for the canonical token (4.4i)."""
        return self.canonical

    @property
    def original(self) -> str | None:
        """Compatibility spelling for the source token (4.4i)."""
        return self.raw

    def __str__(self) -> str:
        return self.canonical

    def __hash__(self) -> int:
        return hash(self.canonical)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, NamedToken) and self.canonical == other.canonical
