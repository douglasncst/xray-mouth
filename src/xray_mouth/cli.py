from __future__ import annotations

import argparse
import os
import sys
from math import isfinite
from pathlib import Path

from xray_mouth.exceptions import XRayMouthError
from xray_mouth.workflow import WorkflowConfig, run_workflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a non-diagnostic periapical radiograph PDF series."
    )
    parser.add_argument(
        "--patient", required=True, help="Patient name shown in the central exam area."
    )
    parser.add_argument(
        "--input", type=Path, required=True, help="Directory containing slot-prefixed radiographs."
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports"),
        help="Directory for timestamped results.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Create and use synthetic non-diagnostic images in --input.",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        dest="open_result",
        help="Open the generated PDF on supported platforms.",
    )
    parser.add_argument(
        "--contrast",
        type=float,
        default=1.0,
        help="Rendered-output contrast multiplier (default: 1.0).",
    )
    parser.add_argument(
        "--strict", action="store_true", help="Fail when any expected protocol slot is missing."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not isfinite(args.contrast) or args.contrast <= 0:
        print("error: --contrast must be finite and greater than zero", file=sys.stderr)
        return 2
    try:
        result = run_workflow(
            WorkflowConfig(
                args.input, args.output_root, args.patient, args.strict, args.demo, args.contrast
            )
        )
    except XRayMouthError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Created: {result.directory}")
    print(f"Mapped slots: {', '.join(f'{slot:02d}' for slot in result.mapped_slots)}")
    if result.missing_slots:
        print(
            f"Warning: missing slots: {', '.join(f'{slot:02d}' for slot in result.missing_slots)}"
        )
    if args.open_result and os.name == "nt":
        try:
            os.startfile(result.pdf_path)  # type: ignore[attr-defined]
        except OSError:
            print("Warning: PDF was saved but could not be opened.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
