"""PICS header and general product information (Clauses 4.1, 4.5.1)."""

from typing import Literal

from pydantic import Field

from .base import EpicsModel
from .enums import CharacterSetCode


class PicsHeader(EpicsModel):
    """The PICS encoding selector (Clause 4.1)."""

    charset_code: Literal[0, 1, 2, 3, 4, 5] = Field(
        default=0, alias="PICS", description="Encoding selector (4.1)."
    )

    @property
    def charset(self) -> CharacterSetCode:
        """Return the named encoding selector (Clause 4.1)."""
        return CharacterSetCode(self.charset_code)


class GeneralInformation(EpicsModel):
    """Unbounded vendor and product strings (Clause 4.5.1)."""

    vendor_name: str = Field(alias="Vendor Name", description="Vendor name (4.5.1).")
    product_name: str = Field(alias="Product Name", description="Product name (4.5.1).")
    product_model_number: str = Field(
        alias="Product Model Number", description="Product model (4.5.1)."
    )
    product_description: str = Field(
        alias="Product Description", description="Description (4.5.1)."
    )
