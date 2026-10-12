# Contributing

Use Python 3.13 or newer and uv. Create a branch named `feature/<topic>`,
`fix/<topic>`, or `docs/<topic>`; submit a focused pull request. Maintainers use
squash merges and review the resulting commit message.

```sh
uv sync --all-extras --group dev
uv run pre-commit install
uv run ruff check .
uv run ruff format --check .
uv run pyrefly check
uv run pytest
uv run mkdocs build --strict
uv build
```

CI tests Python 3.13 and 3.14 on Linux and Windows. Overall line coverage must remain
at least 90 percent, with at least 95 percent in each of lexer, values, model,
codecs, and validation. Tests and documentation must explain both accepted inputs and
failure diagnostics. Public API docstrings use Google style and cite the owning
ASHRAE 135.1 clause; add a decision record when changing an architectural decision.

For a conformance test, add or update `tests/conformance/matrix.yaml`. Each row has
an ID, clause, paraphrased rule, digest link, pytest node IDs, mode, and status.
Mark the test `@pytest.mark.conformance("R-...")`. A row can become `implemented`
only when its tests exist and pass. Planned rows must identify their missing work.
Run `uv run python scripts/gen_conformance.py` after changes; the matrix integrity
test detects missing test references and unregistered conformance markers.

Knowledge tables cite their source edition. Consult
[the knowledge guide](docs/site/validation/knowledge.md) before modifying them.
Never commit licensed PDFs, private extracts, or copied Annex A examples. Build
fixtures using invented devices and values. The repository ignores `*.pdf`,
`resources/`, and `docs/spec/private/`.

Release maintainers update CHANGELOG, verify the package version matches the tag,
and run all local checks. Tags trigger the release workflow: prerelease tags use
TestPyPI; stable tags use PyPI. Both require a configured trusted publisher and
GitHub environment. Pages hosting and publishing setup are external configuration;
a workflow file alone does not prove deployment or publication. After Pages is
configured with the intended visibility, set the repository variable
`ENABLE_PAGES_DEPLOY=true` to enable deployment from `main`. Docs builds and link
checks run without that variable.

## Licensed local Annex A smoke test

With a licensed private `annex-a.tpi` reconstructed from the standard, run:

```sh
ACE_EPICS_PRIVATE_FIXTURES=docs/spec/private uv run pytest tests/codecs/epics/test_private.py
```

This optional test verifies the example's 25 objects, 491 property lines, and known
consistency failures. Private fixtures and extracts remain outside version control
and are never required by CI.


## Release checklist

1. Update the package version and add its dated entry to CHANGELOG. Verify the
   tag and package version agree; prereleases use the `rc` suffix.
2. Run the local checks, strict documentation build and link checker, distribution
   build and audit, and clean installation smoke tests.
3. Verify trusted publishing is configured for the intended GitHub repository,
   workflow, and TestPyPI/PyPI environment before pushing a release tag.
4. Publish a release candidate to TestPyPI, then verify the workflow installs that
   exact version from TestPyPI. Review the 1.0 definition of done before a stable tag.
5. After publication, verify the PyPI project page, distributions, and installation;
   verify Pages deployment and the schema/ontology namespace redirects.
6. Review the GitHub release notes and downloadable archives. Announce the release
   through the project's chosen channels, then start the next Unreleased entry.

External deployment and publication checks require the repository and hosting
configuration. Local checks do not prove those outcomes.
