"""Smoke a built distribution in an isolated environment outside the checkout."""

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE = """
from importlib.resources import files
from ace_epics.api import load
from ace_epics.codecs import json
from ace_epics.knowledge import JsonKnowledgeProvider
from ace_epics.validation import validate
import sys
provider = JsonKnowledgeProvider()
assert provider.bibb("DS-RP-B") is not None
assert provider.object_definition("device", 30) is not None
assert json.schema()["$schema"].endswith("2020-12/schema")
assert files("ace_epics.codecs").joinpath("data/ontology.ttl").is_file()
doc = load(sys.argv[1])
assert validate(doc).exit_code() == 0
assert json.loads(json.dumps(doc)) == doc
if sys.argv[2] == "all":
    from ace_epics.codecs import yaml, rdf
    assert yaml.loads(yaml.dumps(doc)) == doc
    assert rdf.loads(rdf.dumps(doc)) == doc
print("Installed model, knowledge, schema, native/JSON and selected optional codecs passed")
"""


def run(command: list[str], cwd: Path) -> str:
    environment = dict(os.environ)
    environment.pop("VIRTUAL_ENV", None)
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(command, cwd=cwd, env=environment, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"Command failed: {command}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def smoke(
    archive: Path | None, python: str, extras: str, *, testpypi_version: str | None = None
) -> None:
    with tempfile.TemporaryDirectory(prefix="ace-epics-release-") as temporary:
        directory = Path(temporary)
        environment = directory / "venv"
        run(["uv", "venv", "--python", python, str(environment)], directory)
        binary = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        extra = "[all]" if extras == "all" else ""
        if testpypi_version is not None:
            version = testpypi_version.removeprefix("v")
            # Fetch dependencies from PyPI, then the exact project version from
            # TestPyPI alone. No index fallback can substitute another project build.
            dependencies = ["pydantic>=2.7"]
            if extras == "all":
                dependencies.extend(["pyyaml>=6", "rdflib>=7"])
            run(
                [
                    "uv",
                    "pip",
                    "install",
                    "--python",
                    str(binary),
                    "--default-index",
                    "https://pypi.org/simple",
                    *dependencies,
                ],
                directory,
            )
            run(
                [
                    "uv",
                    "pip",
                    "install",
                    "--python",
                    str(binary),
                    "--no-deps",
                    "--default-index",
                    "https://test.pypi.org/simple",
                    f"ace-epics{extra}=={version}",
                ],
                directory,
            )
            installed = run(
                [
                    str(binary),
                    "-c",
                    "from importlib.metadata import version; print(version('ace-epics'))",
                ],
                directory,
            ).strip()
            assert installed == version, f"Expected {version}, installed {installed}"
            label = f"TestPyPI ace-epics=={version}"
        else:
            assert archive is not None
            target = str(archive.resolve()) + extra
            run(["uv", "pip", "install", "--python", str(binary), target], directory)
            label = archive.name
        fixture = ROOT / "tests/fixtures/epics/full.tpi"
        print(run([str(binary), "-c", SMOKE, str(fixture), extras], directory).strip())
        print(run([str(binary), "-m", "ace_epics.cli", "--version"], directory).strip())
        cli = environment / ("Scripts/ace-epics.exe" if os.name == "nt" else "bin/ace-epics")
        run([str(cli), "--help"], directory)
        schema = json.loads(run([str(cli), "schema"], directory))
        assert schema["$schema"].endswith("2020-12/schema")
        run([str(cli), "ontology"], directory)
        run([str(cli), "validate", str(fixture)], directory)
        print(f"PASS clean {python} {extras} install: {label}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", nargs="?", type=Path)
    parser.add_argument(
        "--testpypi-version", help="Exact release tag/version to install from TestPyPI"
    )
    parser.add_argument("--python", required=True)
    parser.add_argument("--extras", choices=["base", "all"], default="base")
    args = parser.parse_args()
    if (args.archive is None) == (args.testpypi_version is None):
        parser.error("choose an archive or --testpypi-version")
    smoke(args.archive, args.python, args.extras, testpypi_version=args.testpypi_version)
