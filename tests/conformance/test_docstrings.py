"""Public source documentation must cite its governing standard provision."""

import ast
import re
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[2] / "src/ace_epics"
CITATION = re.compile(
    r"\b(?:Clauses?\s*\d+(?:\.\d+)*|[4-7]\.\d+(?:\.\d+)*[a-z]?"
    r"|[4-7]\([a-z]\)|C5-\d{2}|Annex\s+[A-Z])",
    re.IGNORECASE,
)


def public_symbols(tree: ast.Module):
    """Visit public definitions without descending into private or function scopes."""
    yield "<module>", tree

    def walk(nodes, prefix=""):
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name.startswith("_"):
                    continue
                name = prefix + node.name
                yield name, node
                if isinstance(node, ast.ClassDef):
                    yield from walk(node.body, name + ".")
            elif isinstance(node, (ast.If, ast.Try)):
                # TYPE_CHECKING and platform guards can contain public declarations.
                yield from walk(node.body, prefix)
                yield from walk(node.orelse, prefix)
                if isinstance(node, ast.Try):
                    yield from walk(node.finalbody, prefix)
                    for handler in node.handlers:
                        yield from walk(handler.body, prefix)

    yield from walk(tree.body)


def public_modules():
    for path in sorted(SOURCE.rglob("*.py")):
        relative = path.relative_to(SOURCE)
        if any(part.startswith("_") for part in relative.parts[:-1]):
            continue
        if path.stem.startswith("_") and path.stem != "__init__":
            continue
        yield path


@pytest.mark.parametrize(
    "path", list(public_modules()), ids=lambda path: str(path.relative_to(SOURCE))
)
def test_public_docstrings_have_clause_citations(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    failures = []
    for name, node in public_symbols(tree):
        docstring = ast.get_docstring(node)
        if not docstring:
            failures.append(f"{name}: missing docstring")
        elif not CITATION.search(docstring):
            failures.append(f"{name}: missing Clause, numeric subsection, or Annex citation")
    assert not failures, "\n".join(failures)


def test_audit_excludes_private_and_local_definitions_and_includes_public_classes():
    tree = ast.parse('''"""Clause 4."""
class _Private:
    def exposed(self): pass
class Public:
    """Clause 4.5."""
    def method(self):
        """Annex A."""
        def local(): pass
    def _hidden(self): pass
    class Nested:
        """Clause 4.4."""
async def public_async():
    """4.5.10."""
if True:
    def guarded():
        """Clause 5."""
''')
    assert [name for name, _ in public_symbols(tree)] == [
        "<module>",
        "Public",
        "Public.method",
        "Public.Nested",
        "public_async",
        "guarded",
    ]
    for text in [
        "Clause4",
        "Clauses 4 and 5",
        "135.1 Clause 4.5.10",
        "4.4(j)",
        "4.4i",
        "5(n)",
        "C5-05",
        "Annex K.2",
    ]:
        assert CITATION.search(text)
    assert not CITATION.search("No citation here")
