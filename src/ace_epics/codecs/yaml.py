"""Safe YAML interchange for the EPICS document model (135.1 Clause 4)."""

from pathlib import Path
from typing import IO, Any

from ace_epics.diagnostics import EpicsError
from ace_epics.model.document import EpicsDocument

from ._interchange import ValueMode, decode_document, document_data, failure
from .base import ParseResult, document_from_result
from .errors import MissingExtraError

name = "yaml"
extensions = (".yaml", ".yml")
media_type = "application/yaml"


def _yaml():
    try:
        import yaml
    except ImportError as exc:
        raise MissingExtraError("yaml") from exc
    return yaml


def _check_expansion(data: Any, *, max_nodes: int, max_depth: int) -> None:
    """Count expanded alias references without recursively expanding them (Clause 4)."""
    budget = 0
    stack = [(data, 0, frozenset())]
    while stack:
        node, depth, ancestors = stack.pop()
        budget += 1
        if budget > max_nodes or depth > max_depth:
            raise failure("YAML aliases exceed the configured expansion limit", "YAML-LIMIT")
        if isinstance(node, (dict, list)):
            identity = id(node)
            if identity in ancestors:
                raise failure("Recursive YAML aliases are not supported", "YAML-ALIAS")
            children = list(node.values()) if isinstance(node, dict) else node
            stack.extend((child, depth + 1, ancestors | {identity}) for child in children)


def parse(
    data: str | bytes, *, max_nodes: int = 1_000_000, max_depth: int = 100, **opts: Any
) -> ParseResult:
    """Read SafeLoader input as a document or collected diagnostics (Clause 4)."""
    yaml = _yaml()
    try:
        try:
            decoded = yaml.safe_load(data)
        except (yaml.YAMLError, UnicodeError, RecursionError) as exc:
            raise failure(f"Invalid YAML: {exc}") from exc
        _check_expansion(decoded, max_nodes=max_nodes, max_depth=max_depth)
        doc = decode_document(decoded)
        return ParseResult(doc, doc.diagnostics)
    except EpicsError as exc:
        return ParseResult(None, exc.diagnostics)


def loads(data: str | bytes, *, raise_on_error: bool = True, **opts: Any) -> EpicsDocument:
    """Read a YAML document, raising collected failures by default (Clause 4)."""
    return document_from_result(parse(data, **opts), raise_on_error=raise_on_error)


def dumps(
    doc: EpicsDocument, *, values: ValueMode = "text", preserve_raw: bool = False, **opts: Any
) -> str:
    """Write block YAML; exact reals remain strings instead of YAML floats (4.4)."""
    return _yaml().safe_dump(
        document_data(doc, values=values, preserve_raw=preserve_raw),
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    )


def load(src: Path | str | IO[str] | IO[bytes], **opts: Any) -> EpicsDocument:
    """Read YAML from a path or file object (Clause 4 interchange)."""
    data = Path(src).read_bytes() if isinstance(src, (str, Path)) else src.read()
    return loads(data, **opts)


def dump(doc: EpicsDocument, dst: Path | str | IO[str], **opts: Any) -> None:
    """Write YAML to a path or text file object (Clause 4 interchange)."""
    text = dumps(doc, **opts)
    if isinstance(dst, (str, Path)):
        Path(dst).write_text(text, encoding="utf-8")
    else:
        dst.write(text)
