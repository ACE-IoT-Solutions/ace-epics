"""Lazy codec registry and extension inference for Clause4 documents."""

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

from ace_epics.model import EpicsDocument

from .base import Codec, ParseResult


@dataclass(frozen=True)
class ModuleCodec:
    """Adapt module-level codec functions to the Clause4 codec protocol."""

    name: str
    extensions: tuple[str, ...]
    media_type: str
    module: str

    def parse(self, data: str | bytes, **opts: Any) -> ParseResult:
        """Collect Clause4 diagnostics without inventing a document on failure."""
        return import_module(self.module).parse(data, **opts)

    def loads(self, data: str | bytes, **opts: Any) -> EpicsDocument:
        """Deserialize a document using the registered module (Clause4)."""
        return import_module(self.module).loads(data, **opts)

    def dumps(self, doc: EpicsDocument, **opts: Any) -> str | bytes:
        """Serialize a document using the registered module (Clause4)."""
        return import_module(self.module).dumps(doc, **opts)

    def load(self, src: Any, **opts: Any) -> EpicsDocument:
        """Read a document from a path or stream (Clause4)."""
        return import_module(self.module).load(src, **opts)

    def dump(self, doc: EpicsDocument, dst: Any, **opts: Any) -> None:
        """Write a document to a path or stream (Clause4)."""
        import_module(self.module).dump(doc, dst, **opts)


_CODECS: dict[str, Codec] = {
    name: ModuleCodec(name, extensions, media, f"ace_epics.codecs.{name}")
    for name, extensions, media in (
        ("epics", (".tpi", ".epics"), "text/plain"),
        ("json", (".json",), "application/json"),
        ("yaml", (".yaml", ".yml"), "application/yaml"),
        ("rdf", (".ttl",), "text/turtle"),
    )
}


def register(codec: Codec) -> None:
    """Register an external Clause4 codec; names and extensions must be unique."""
    if codec.name in _CODECS:
        raise ValueError(f"Codec already registered: {codec.name}")
    existing = {ext.lower() for c in _CODECS.values() for ext in c.extensions}
    if existing.intersection(ext.lower() for ext in codec.extensions):
        raise ValueError("Codec extension already registered")
    _CODECS[codec.name] = codec


def get(name: str) -> Codec:
    """Resolve a codec name, accepting native/turtle aliases (Clause4)."""
    normalized = {"native": "epics", "turtle": "rdf", "ttl": "rdf"}.get(name.lower(), name.lower())
    try:
        return _CODECS[normalized]
    except KeyError as exc:
        raise ValueError(f"Unknown codec {name!r}; choose {', '.join(_CODECS)}") from exc


def for_path(path: str | Path) -> Codec:
    """Infer a Clause4 serialization from a filename extension."""
    extension = Path(path).suffix.lower()
    for codec in _CODECS.values():
        if extension in codec.extensions:
            return codec
    raise ValueError(f"Cannot infer format from {path!s}; specify a codec")


def codecs() -> tuple[Codec, ...]:
    """Return the registered codecs for shared conformance tests (Clause4)."""
    return tuple(_CODECS.values())
