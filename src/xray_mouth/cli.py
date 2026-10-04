"""Command-line interface."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .analysis import dataset_report
from .demo import create_demo
from .dicom import anonymize_file
from .report import main as report_main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xray-mouth",
        description="Generate Green Smile reports, inspect images and de-identify DICOM files.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    report_parser = subparsers.add_parser(
        "report", help="Generate the approved Green Smile montage"
    )
    report_parser.add_argument("directory", type=Path, nargs="?", default=Path.cwd())
    report_parser.add_argument("--no-open", action="store_true", help="Do not open PDFs or dialogs")

    inspect_parser = subparsers.add_parser("inspect", help="Generate a JSON dataset report")
    inspect_parser.add_argument("path", type=Path)
    inspect_parser.add_argument("--recursive", action="store_true")
    inspect_parser.add_argument("--output", type=Path)

    anonymize_parser = subparsers.add_parser("anonymize", help="Write a de-identified DICOM copy")
    anonymize_parser.add_argument("source", type=Path)
    anonymize_parser.add_argument("destination", type=Path)

    demo_parser = subparsers.add_parser(
        "demo", help="Create synthetic images and a reproducible example report"
    )
    demo_parser.add_argument("directory", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "report":
        return report_main(project=args.directory.resolve(), open_pdf=not args.no_open)
    if args.command == "inspect":
        report = dataset_report(args.path, recursive=args.recursive)
        payload = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload + "\n", encoding="utf-8")
        else:
            print(payload)
        return 1 if report["errors"] else 0
    if args.command == "anonymize":
        destination = anonymize_file(args.source, args.destination)
        print(f"Wrote de-identified copy to {destination}")
        return 0
    if args.command == "demo":
        report = create_demo(args.directory)
        print(f"Created {report['file_count']} synthetic images in {args.directory}")
        print(f"Report: {args.directory / 'report.json'}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
