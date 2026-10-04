"""Windows-compatible entry point for the approved Green Smile report."""

from pathlib import Path

from xray_mouth.report import main

if __name__ == "__main__":
    raise SystemExit(main(project=Path(__file__).resolve().parent))
