"""Check that Clause 4/5 traceability does not overstate implementation evidence."""

import ast
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "tests/conformance/matrix.yaml"


def test_matrix_ids_statuses_and_test_references(request) -> None:
    rows = yaml.safe_load(MATRIX.read_text())
    collected = {item.nodeid for item in request.session.items}
    collected_files = {node.split("::")[0] for node in collected}
    assert isinstance(rows, list) and rows
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids))
    for row in rows:
        assert row["status"] in {"implemented", "planned", "not-applicable"}
        assert row["mode"] in {"both", "strict-only", "lenient-only"}
        assert row["clause"] and row["rule"]
        assert (ROOT / row["digest"].split("#")[0]).is_file()
        assert isinstance(row["tests"], list)
        if row["status"] == "implemented":
            assert row["tests"], f"{row['id']} claims implementation without tests"
        for node_id in row["tests"]:
            if node_id.split("::")[0] in collected_files:
                assert any(
                    node == node_id or node.startswith(node_id + "[") for node in collected
                ), f"Test reference was not collected: {node_id}"
            parts = node_id.split("::")
            path = ROOT / parts[0]
            assert path.is_file(), f"Missing test file: {node_id}"
            nodes = ast.parse(path.read_text()).body
            for part in parts[1:]:
                name = part.split("[")[0]
                matching = [node for node in nodes if getattr(node, "name", None) == name]
                assert matching, f"Missing test node: {node_id}"
                nodes = getattr(matching[0], "body", [])


def test_conformance_markers_are_registered_in_matrix() -> None:
    rows = yaml.safe_load(MATRIX.read_text())
    ids = {row["id"] for row in rows}
    for path in (ROOT / "tests").rglob("test_*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr != "conformance":
                continue
            assert node.args, f"Conformance marker without rule ID: {path}"
            for argument in node.args:
                assert isinstance(argument, ast.Constant) and isinstance(argument.value, str)
                assert argument.value in ids, f"Unregistered conformance ID: {argument.value}"
