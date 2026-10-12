"""Command-line conversion, formatting, queries, and validation (Clauses 4, 5, 14)."""

import argparse
import json
import logging
import os
import sys
import tempfile
from pathlib import Path

from ace_epics import __version__
from ace_epics.api import convert, dump, load
from ace_epics.codecs import registry
from ace_epics.diagnostics import EpicsError, Severity
from ace_epics.knowledge import JsonKnowledgeProvider
from ace_epics.validation import validate


def parser() -> argparse.ArgumentParser:
    """Build the complete Clause4/5 CLI without additional runtime dependencies."""
    root = argparse.ArgumentParser(
        prog="ace-epics", description="BACnet EPICS tools (ASHRAE 135.1)"
    )
    root.add_argument("--version", action="version", version=f"ace-epics {__version__}")
    root.add_argument("--quiet", action="store_true")
    root.add_argument("--no-color", action="store_true")
    root.add_argument(
        "--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="WARNING"
    )
    commands = root.add_subparsers(dest="command", required=True)
    change = commands.add_parser("convert", help="Convert between EPICS, JSON, YAML, and Turtle")
    change.add_argument("src", type=Path)
    change.add_argument("dst", type=Path)
    change.add_argument("--from", dest="from_format")
    change.add_argument("--to", dest="to_format")
    change.add_argument("--strict", action="store_true")
    change.add_argument("--values", choices=["text", "tree"])
    change.add_argument("--base-iri")
    check = commands.add_parser("validate", help="Run Clause5 consistency rules")
    check.add_argument("src", type=Path)
    check.add_argument("--strict", action="store_true")
    check.add_argument("--rules", help="Comma-separated rule identifiers")
    check.add_argument("--knowledge", type=Path)
    check.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    check.add_argument("--warnings-as-errors", action="store_true")
    fmt = commands.add_parser("fmt", help="Write canonical native EPICS text")
    fmt.add_argument("src", type=Path)
    destination = fmt.add_mutually_exclusive_group()
    destination.add_argument("-o", dest="dst", type=Path)
    destination.add_argument("--in-place", action="store_true")
    fmt.add_argument("--preserve", action="store_true")
    inspect = commands.add_parser("inspect", help="Show section counts and object properties")
    inspect.add_argument("src", type=Path)
    inspect.add_argument("--objects", action="store_true")
    inspect.add_argument("--object", dest="object_id", help="TYPE,INSTANCE")
    inspect.add_argument("--property", dest="property_name")
    commands.add_parser("schema", help="Print the published JSON Schema")
    commands.add_parser("ontology", help="Print the published RDF vocabulary")
    return root


def read_options(path: Path, format: str | None, strict: bool) -> dict:
    """Strict syntax checks belong to the native Clause4 reader."""
    codec = registry.get(format) if format else registry.for_path(path)
    return {"strict": strict} if codec.name == "epics" else {}


def inspect_document(args: argparse.Namespace) -> str:
    """Render the explicitly requested object/property subset (Clause7 queries)."""
    from ace_epics.model import ObjectIdentifier
    from ace_epics.model.names import NamedToken
    from ace_epics.values import render

    doc = load(args.src)
    objects = doc.objects
    if args.object_id:
        object_type, instance = args.object_id.rsplit(",", 1)
        type_value = (
            int(object_type)
            if object_type.strip().isdigit()
            else NamedToken.model_validate(object_type)
        )
        identifier = ObjectIdentifier(object_type=type_value, instance=int(instance))
        found = doc.get_object(identifier)
        if found is None:
            raise ValueError(f"Object {identifier} absent")
        objects = [found]
    lines = [
        f"{doc.general.vendor_name}: {doc.general.product_name} "
        f"({doc.general.product_model_number})",
        f"Objects: {len(doc.objects)}; BIBBs: {len(doc.bibbs)}; services: {len(doc.services)}; "
        f"object types: {len(doc.object_types)}",
    ]
    if args.objects or args.object_id or args.property_name:
        for obj in objects:
            lines.append(f"{obj.identifier} {obj.name} ({len(obj.properties)} listed properties)")
            if args.object_id or args.property_name:
                entries = (
                    [obj.property(args.property_name)] if args.property_name else obj.properties
                )
                for entry in entries:
                    if entry is not None:
                        lines.append(f"  {entry.name}: {render(entry.value)} [{entry.access}]")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Execute a command; return0clean,1warnings-as-errors,2errors (Clause14)."""
    args = parser().parse_args(argv)
    logging.basicConfig(level=args.log_level)
    try:
        if args.command == "convert":
            destination = (
                registry.get(args.to_format) if args.to_format else registry.for_path(args.dst)
            )
            options = {}
            if args.values and destination.name in {"json", "yaml"}:
                options["values"] = args.values
            if args.base_iri and destination.name == "rdf":
                options["base_iri"] = args.base_iri
            convert(
                args.src,
                args.dst,
                from_format=args.from_format,
                to_format=args.to_format,
                read_options=read_options(args.src, args.from_format, args.strict),
                write_options=options,
            )
            return 0
        if args.command == "validate":
            doc = load(args.src, **read_options(args.src, None, args.strict))
            selected = [r.strip() for r in args.rules.split(",")] if args.rules else None
            report = validate(
                doc, JsonKnowledgeProvider(args.knowledge), rules=selected, strict=args.strict
            )
            parse_findings = doc.diagnostics
            if args.format == "json":
                content = report.model_dump(mode="json")
                content["parse_diagnostics"] = [d.model_dump(mode="json") for d in parse_findings]
                print(json.dumps(content, indent=2))
            elif args.format == "markdown":
                print(report.to_markdown(), end="")
                if parse_findings:
                    print("\nParse diagnostics:\n")
                    for finding in parse_findings:
                        print(f"- {finding.severity}: {finding.code}: {finding.message}")
            elif not args.quiet:
                for result in report.results:
                    print(f"{result.rule_id}: {result.outcome}")
                for finding in [*parse_findings, *report.diagnostics]:
                    print(f"{finding.severity}: {finding.code}: {finding.message}")
            findings = [*parse_findings, *report.diagnostics]
            if any(d.severity == Severity.ERROR for d in findings):
                return 2
            return int(
                args.warnings_as_errors and any(d.severity == Severity.WARNING for d in findings)
            )
        if args.command == "fmt":
            from ace_epics.values import Canonical, Preserving

            doc = load(args.src)
            style = Preserving if args.preserve else Canonical
            if args.in_place:
                # Validate and serialize before replacing the source, preserving file permissions.
                output = registry.get("epics").dumps(doc, style=style)
                temporary = None
                try:
                    with tempfile.NamedTemporaryFile(dir=args.src.parent, delete=False) as stream:
                        temporary = Path(stream.name)
                        from ace_epics.encoding import encode

                        stream.write(
                            encode(output, doc.header.charset_code)
                            if isinstance(output, str)
                            else output
                        )
                    temporary.chmod(args.src.stat().st_mode)
                    os.replace(temporary, args.src)
                finally:
                    if temporary is not None:
                        temporary.unlink(missing_ok=True)
            elif args.dst:
                dump(doc, args.dst, format="epics", style=style)
            else:
                output = registry.get("epics").dumps(doc, style=style)
                sys.stdout.write(output if isinstance(output, str) else output.decode("utf-8"))
            return 0
        if args.command == "inspect":
            content = inspect_document(args)
            if not args.quiet:
                print(content)
            return 0
        if args.command == "schema":
            from ace_epics.codecs.json import schema

            print(json.dumps(schema(), indent=2))
            return 0
        if args.command == "ontology":
            from importlib.resources import files

            print(
                files("ace_epics.codecs").joinpath("data/ontology.ttl").read_text(encoding="utf-8"),
                end="",
            )
            return 0
    except (EpicsError, ValueError, OSError, ImportError, KeyError) as exc:
        if isinstance(exc, EpicsError) and args.command == "validate" and args.format == "json":
            print(
                json.dumps(
                    {
                        "parse_diagnostics": [d.model_dump(mode="json") for d in exc.diagnostics],
                        "results": [],
                    },
                    indent=2,
                )
            )
        elif not args.quiet:
            print(f"ace-epics: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
