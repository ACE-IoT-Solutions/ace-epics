# Phase 6: CLI, Documentation Site, and 1.0 Release

Goal: a usable command line, a complete documentation site, and a repeatable release to
PyPI. Depends on Phases 4 and 5. Estimated effort: 5 to 7 days.

## 6.1 CLI (`cli.py`, console script `ace-epics`)

Use `argparse` (no runtime dependency) unless the team prefers `typer` under the `cli`
extra; record the choice in `docs/decisions/0005-cli-framework.md`.

Commands:
- `ace-epics convert SRC DST [--from FMT] [--to FMT] [--strict] [--values text|tree]
  [--base-iri IRI]`: any codec to any codec; formats inferred from extensions.
- `ace-epics validate SRC [--strict] [--rules ID,...] [--knowledge PATH] [--format
  text|json|markdown] [--warnings-as-errors]`: parse diagnostics plus Clause 5 report;
  exit code 0/1/2 (clean, warnings with flag, errors).
- `ace-epics fmt SRC [-o DST | --in-place] [--preserve]`: canonical rewrite (Phase 3 writer).
- `ace-epics inspect SRC [--objects] [--object TYPE,INSTANCE] [--property NAME]`: human
  summary (counts per section, object table, one object's properties).
- `ace-epics schema` and `ace-epics ontology`: print the published artifacts.
- `--version`, `--quiet`, `--no-color`, `--log-level`.

Tests: `tests/cli/` run each command through `subprocess` against the synthetic corpus and
check exit codes and key output lines; `--format json` output validated against a small
schema.

## 6.2 Documentation site (mkdocs-material)

Structure (filled across phases, completed here):
- Home: what EPICS is, why this library, 30-second example for each format.
- Getting started: install (`uv add ace-epics[all]`), parse, validate, convert, CLI.
- Format guide: overview, encodings, sections, values, leniency, writer canonical form.
- Serialization: JSON, YAML, RDF, schema and ontology downloads.
- Validation: rules table (generated), knowledge tables, query API, writing a test tool.
- Reference: API (mkdocstrings, every public module), diagnostics catalogue (generated),
  conformance matrix (generated from `08-testing-and-compliance.md` data file).
- Project: changelog, contributing, decisions (ADR index), security, license, standard
  edition compatibility statement (135.1-2025; which Protocol_Revisions the knowledge
  tables cover).

Quality gates: `mkdocs build --strict`, link checker, every public symbol has a docstring
with a clause citation (ruff `D` rules plus a custom test that greps docstrings in
`src/ace_epics` for `Clause` or `4.` style references).

## 6.3 Packaging and release

- Versioning: SemVer; 0.x during Phases 1 to 5 (each phase merge bumps minor), 1.0.0 at
  the end of this phase. Document format version (`"format": "ace-epics/1"`) is independent.
- `uv build` sdist and wheel; `twine check`; install smoke test in a clean venv on CI
  (`uv run --isolated --with ace_epics-*.whl python -c "import ace_epics"`).
- Trusted publishing to PyPI from `release.yml` on `v*` tags; TestPyPI on `v*rc*`.
- GitHub release notes from CHANGELOG; signed tags recommended.
- PyPI metadata review: README renders, classifiers, project URLs (docs, source, issues,
  changelog), keywords include `bacnet` and `ashrae` so the physics EPICS crowd is not
  misled.
- Post-release checklist in `docs/site/contributing.md`: bump version, update CHANGELOG,
  tag, verify PyPI page, verify docs deploy, announce.

## 6.4 Tests and acceptance

- CLI tests green; `uv build` artifacts install and import on 3.13 and 3.14.
- Docs build strictly with no warnings; link check clean.
- `v1.0.0rc1` published to TestPyPI and installed from there in CI; `v1.0.0` published to
  PyPI after the 1.0 definition of done in `00-overview.md` is signed off.


## Local packaging verification (2026-10-11)

`uv build` rebuilt the local 0.0.1 wheel and source archive from the final source
and knowledge data used for this verification. Both archives passed `twine check` and the distribution audit:
all source JSON/TTL package data and the license are present; licensed PDFs,
resources, and private extracts are excluded. The data include the 15 scoped object
types with verified Protocol_Revision snapshots 14 through 30.

All eight final clean installation combinations passed: wheel and source archive,
base and all extras, and Python 3.13 and 3.14. Each ran outside the checkout and
verified installed knowledge, model/schema data, CLI entry points and schema/ontology
commands, native/JSON roundtrips, and the regenerated full fixture's zero-error
validation report. All-extras installations additionally passed YAML/RDF roundtrips.

Release CI requires metadata/archive checks and the same eight clean install cases
before publishing. A post-TestPyPI job installs the exact tag version from TestPyPI
with dependencies from PyPI and reruns the installed smoke checks outside the
checkout on both Python versions. Release builds also run the local site-link
checker. These jobs are configured but have not been executed on GitHub.
CI and release also require 90% overall statement coverage and
95% in each of lexer, values, model, codecs, and validation. Workflow configuration
is not evidence of a passing live run; coverage is verified separately by the final
integrated test run.

External acceptance gates remain pending: GitHub CI execution, trusted publisher
configuration, TestPyPI and PyPI publication/install verification, GitHub release,
Pages deployment, and w3id registration. No external publish or tag was performed.
