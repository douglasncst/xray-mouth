"""Command-line interface for dataset and clinical-series workflows."""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .analysis import dataset_report
from .demo import create_demo
from .dicom import anonymize_file
from .exceptions import XRayMouthError
from .workflow import WorkflowConfig, run_workflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xray-mouth", description="Privacy-first dental imaging tools.")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect_parser = commands.add_parser("inspect", help="Generate a JSON dataset report")
    inspect_parser.add_argument("path", type=Path)
    inspect_parser.add_argument("--recursive", action="store_true")
    inspect_parser.add_argument("--output", type=Path)
    anonymize = commands.add_parser("anonymize", help="Write a de-identified DICOM copy")
    anonymize.add_argument("source", type=Path)
    anonymize.add_argument("destination", type=Path)
    demo = commands.add_parser("demo", help="Create synthetic images and an inspection report")
    demo.add_argument("directory", type=Path)
    series = commands.add_parser("series", help="Build a non-diagnostic 14-slot series")
    series.add_argument("--patient", required=True)
    series.add_argument("--input", type=Path, required=True)
    series.add_argument("--output-root", type=Path, default=Path("reports"))
    series.add_argument("--demo", action="store_true")
    series.add_argument("--open", action="store_true", dest="open_result")
    series.add_argument("--contrast", type=float, default=1.0)
    series.add_argument("--strict", action="store_true")
    series.add_argument("--clinic-name", default="XRay Mouth")
    series.add_argument("--clinic-subtitle", default="Clinical Radiograph Series")
    series.add_argument("--exam-label", default="Série periapical")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
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
    try:
        result = run_workflow(WorkflowConfig(
            input_directory=args.input, output_root=args.output_root,
            patient_name=args.patient, strict=args.strict, demo=args.demo,
            contrast=args.contrast, clinic_name=args.clinic_name,
            clinic_subtitle=args.clinic_subtitle, exam_label=args.exam_label,
        ))
    except XRayMouthError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Created export with {len(result.mapped_slots)} mapped slots.")
    if result.missing_slots:
        print(f"Warning: missing slots: {', '.join(f'{slot:02d}' for slot in result.missing_slots)}")
    if args.open_result and os.name == "nt":
        try:
            os.startfile(result.pdf_path)  # type: ignore[attr-defined]
        except OSError:
            print("Warning: PDF was saved but could not be opened.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
