"""Generate API, traceability, and shared project pages for the documentation build."""

import json
import re
import runpy
from pathlib import Path

import mkdocs_gen_files
from rdflib import RDF, RDFS, Graph, URIRef

from ace_epics.codecs.json import schema
from ace_epics.diagnostics import DIAGNOSTIC_REGISTRY
from ace_epics.validation.rules import RULES

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/ace_epics"

for destination, source in (
    ("changelog.md", "CHANGELOG.md"),
    ("contributing.md", "CONTRIBUTING.md"),
    ("security.md", "SECURITY.md"),
    ("license.md", "LICENSE"),
):
    with mkdocs_gen_files.open(destination, "w") as page:
        content = (ROOT / source).read_text(encoding="utf-8")
        if destination == "contributing.md":
            content = content.replace(
                "docs/site/validation/knowledge.md", "validation/knowledge.md"
            )
        if destination == "license.md":
            content = (
                "# License\n\nApache License 2.0. The full license follows.\n\n```text\n"
                + content
                + "\n```\n"
            )
        page.write(content)
    mkdocs_gen_files.set_edit_path(destination, "../../" + source)

# Publish the authored ADRs and derive their index from the same files.
# Existing ADRs have no relative file links; each page retains its source text,
# including standard clause references. The template is linked separately.
decision_lines = [
    "# Architecture decisions",
    "",
    "Generated from `docs/decisions`; each page preserves the authored decision.",
    "",
]
for source in sorted((ROOT / "docs/decisions").glob("*.md")):
    destination = "reference/decisions/" + source.name
    content = source.read_text(encoding="utf-8")
    with mkdocs_gen_files.open(destination, "w") as page:
        page.write(content)
    mkdocs_gen_files.set_edit_path(destination, "../../../decisions/" + source.name)
    if source.name == "0000-template.md":
        continue
    heading = re.search(r"^# (.+)$", content, re.MULTILINE)
    if heading is None:
        raise ValueError(f"ADR lacks a title: {source.name}")
    title = re.sub(r"^(?:ADR \d+|D[\d.]+):\s*", "", heading[1])
    # Retain the existing public anchors used by the format guide.
    if source.name == "0001-license.md":
        title = "License"
    decision_lines.extend(
        [
            "## " + title,
            "",
            f"[Read ADR {source.name[:4]}](decisions/{source.name}).",
            "",
        ]
    )
if (ROOT / "docs/decisions/0000-template.md").is_file():
    decision_lines.extend(
        [
            "## Writing a decision",
            "",
            "Use the [ADR template](decisions/0000-template.md) when proposing a decision.",
            "",
        ]
    )
with mkdocs_gen_files.open("reference/decisions.md", "w") as page:
    page.write("\n".join(decision_lines))
mkdocs_gen_files.set_edit_path("reference/decisions.md", "../../../scripts/gen_docs.py")

api_links = ["# API reference", "", "Generated from the current source package.", ""]
authored_modules = {}
for authored in (ROOT / "docs/site/api").rglob("*.md"):
    for module in re.findall(r"^::: ([\w.]+)", authored.read_text(), re.MULTILINE):
        authored_modules[module] = authored.relative_to(ROOT / "docs/site/api").as_posix()
for path in sorted(SOURCE.rglob("*.py")):
    relative = path.relative_to(SOURCE)
    if path.stem.startswith("_") or any(part.startswith("_") for part in relative.parts[:-1]):
        continue
    module = "ace_epics." + ".".join(relative.with_suffix("").parts)
    if module in authored_modules:
        api_links.append(f"- [{module}]({authored_modules[module]})")
        continue
    destination = "api/" + relative.with_suffix(".md").as_posix()
    with mkdocs_gen_files.open(destination, "w") as page:
        page.write(f"# {module}\n\n::: {module}\n")
    mkdocs_gen_files.set_edit_path(destination, "../../../" + path.relative_to(ROOT).as_posix())
    api_links.append(f"- [{module}]({relative.with_suffix('.md').as_posix()})")
with mkdocs_gen_files.open("api/index.md", "w") as page:
    page.write("\n".join(api_links) + "\n")

matrix = runpy.run_path(str(ROOT / "scripts/gen_conformance.py"))
with mkdocs_gen_files.open("reference/conformance.md", "w") as page:
    page.write(matrix["render_matrix"](matrix["read_matrix"]()))
mkdocs_gen_files.set_edit_path("reference/conformance.md", "../../../tests/conformance/matrix.yaml")

# Generate registry-backed diagnostics and rules so the prose cannot drift.

rule_lines = [
    "# Consistency rules",
    "",
    "Generated from the rule registry. Example messages below are illustrative;",
    "a finding includes the specific object, property, or claim that failed.",
    "",
    "| ID | Clause | Severity | Check | Knowledge | Example message |",
    "|---|---|---|---|---|---|",
]
for rule in RULES:
    needs = ", ".join(sorted(rule.requires)) or "None"
    rule_lines.append(
        f"| {rule.id} | {rule.clause} | {rule.severity.value} | {rule.description} | "
        f"{needs} | {rule.id}: {rule.description} |"
    )
with mkdocs_gen_files.open("validation/rules.md", "w") as page:
    page.write("\n".join(rule_lines) + "\n")

lines = [
    "# Diagnostics",
    "",
    "Generated from the diagnostic registry.",
    "",
    "| Code | Clause | Description |",
    "|---|---|---|",
]
for code, definition in sorted(DIAGNOSTIC_REGISTRY.items()):
    lines.append(f"| {code} | {definition.clause} | {definition.description} |")
with mkdocs_gen_files.open("reference/diagnostics.md", "w") as page:
    page.write("\n".join(lines) + "\n")


with mkdocs_gen_files.open("schema/epics-document.schema.json", "w") as artifact:
    artifact.write(json.dumps(schema(), indent=2) + "\n")
for source, destination in (("ontology.ttl", "epics.ttl"), ("shapes.ttl", "shapes.ttl")):
    with mkdocs_gen_files.open("ns/" + destination, "w") as artifact:
        artifact.write((SOURCE / "codecs/data" / source).read_text(encoding="utf-8"))


vocab = Graph().parse(SOURCE / "codecs/data/ontology.ttl", format="turtle")
terms = sorted(
    {str(s) for s in vocab.subjects() if str(s).startswith("https://w3id.org/ace-epics#")}
)
lines = [
    "# RDF vocabulary",
    "",
    "Generated from the shipped ontology.",
    "",
    "| Term | Kind | Description |",
    "|---|---|---|",
]
for term in terms:
    node = URIRef(term)
    types = [str(t).rsplit("#", 1)[-1] for t in vocab.objects(node, RDF.type)]
    label = str(vocab.value(node, RDFS.label) or vocab.value(node, RDFS.comment) or "")
    lines.append(f"| `{term.split('#')[-1]}` | {', '.join(types)} | {label} |")
with mkdocs_gen_files.open("serialization/vocabulary.md", "w") as page:
    page.write("\n".join(lines) + "\n")
