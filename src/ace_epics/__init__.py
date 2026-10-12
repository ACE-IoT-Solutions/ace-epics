"""BACnet EPICS tools implementing ASHRAE 135.1 Clauses 4 and 5."""

from typing import TYPE_CHECKING, Any

__version__ = "0.0.1"

if TYPE_CHECKING:
    from .api import convert, dump, load
    from .codecs.errors import MissingExtraError
    from .diagnostics import Diagnostic, EpicsError, Severity
    from .model import EpicsDocument
    from .validation import validate

__all__ = [
    "Diagnostic",
    "EpicsDocument",
    "EpicsError",
    "MissingExtraError",
    "Severity",
    "convert",
    "dump",
    "load",
    "validate",
]


def __getattr__(name: str) -> Any:
    """Load public Clause4/5 APIs without eager optional codec dependencies."""
    from importlib import import_module

    module = {
        "load": ".api",
        "dump": ".api",
        "convert": ".api",
        "validate": ".validation",
        "EpicsDocument": ".model",
        "Diagnostic": ".diagnostics",
        "Severity": ".diagnostics",
        "EpicsError": ".diagnostics",
        "MissingExtraError": ".codecs.errors",
    }.get(name)
    if module is None:
        raise AttributeError(name)
    value = getattr(import_module(module, __name__), name)
    globals()[name] = value
    return value
