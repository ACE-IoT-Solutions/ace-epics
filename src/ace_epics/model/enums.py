"""Header encodings and supported character-set literals (Clauses 4.1, 4.5.6)."""

from enum import IntEnum, StrEnum


class CharacterSetCode(IntEnum):
    """Numeric PICS encoding selectors from Table 4-1 (Clause 4.1)."""

    UTF8 = 0
    DBCS = 1
    JIS_X_0208 = 2
    UCS4 = 3
    UCS2 = 4
    ISO_8859_1 = 5

    @property
    def octet_width(self) -> int:
        """Code-unit width used by the PICS header (Clause 4.1)."""
        return {self.UCS4: 4, self.UCS2: 2}.get(self, 1)


class CharacterSet(StrEnum):
    """Supported character-set literals from Clause 4.5.6."""

    UTF8 = "ISO 10646 (UTF-8)"
    DBCS = "IBM/Microsoft DBCS"
    JIS_X_0208 = "JIS X 0208"
    ISO_8859_1 = "ISO 8859-1"
    UCS4 = "ISO 10646 (UCS-4)"
    UCS2 = "ISO 10646 (UCS2)"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            key = " ".join(value.replace("™", "").split()).casefold()
            key = key.replace("(ucs-2)", "(ucs2)")
            return next((member for member in cls if member.value.casefold() == key), None)
        return None


CHARACTER_SET_ALIASES = {
    "ISO 10646 (UCS-2)": CharacterSet.UCS2,
    "IBM™/Microsoft™ DBCS": CharacterSet.DBCS,
}
