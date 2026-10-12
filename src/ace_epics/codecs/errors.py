"""Errors for optional Clause 4 interchange codecs."""


class MissingExtraError(ImportError):
    """An optional codec dependency is not installed (Clause 4 interchange)."""

    def __init__(self, extra: str) -> None:
        super().__init__(f"Install the optional codec dependency: pip install ace-epics[{extra}]")
        self.extra = extra
