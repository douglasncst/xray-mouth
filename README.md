# xray-mouth

[![CI](https://github.com/douglasncst/xray-mouth/actions/workflows/ci.yml/badge.svg)](https://github.com/douglasncst/xray-mouth/actions/workflows/ci.yml)
[![CodeQL](https://github.com/douglasncst/xray-mouth/actions/workflows/codeql.yml/badge.svg)](https://github.com/douglasncst/xray-mouth/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Local, privacy-aware Python tools for dental imaging research: dataset inspection, limited DICOM identifier removal, and non-diagnostic organization of a 14-image periapical series.

> [!CAUTION]
> Alpha research software—not a medical device, diagnostic system, PACS, certified anonymizer, or substitute for institutional review. Outputs can contain protected health information. The DICOM command removes a limited set of metadata and private tags; it does **not** inspect or redact burned-in pixel annotations and does not claim conformance with the complete DICOM PS3.15 confidentiality profile.

## Capabilities

- `inspect`: deterministic JSON inventory, SHA-256 hashes, basic raster statistics, and filename privacy warnings.
- `anonymize`: writes a new DICOM file, clears common direct identifiers and private tags, and regenerates principal instance UIDs. It refuses to overwrite either the source or an existing destination.
- `demo`: produces synthetic raster fixtures and an inspection report.
- `series`: validates slot-prefixed raster files, preserves source files, and exports a 14-slot 3:4 layout as preview PNG, 600-DPI-sized PNG, PDF, and text report.

No command uploads data. Network isolation, access control, backups, retention, consent, and final disclosure review remain the operator's responsibility.

## Install

```bash
git clone https://github.com/douglasncst/xray-mouth.git
cd xray-mouth
python -m venv .venv
python -m pip install -e .
```

Python 3.10+ is supported. Runtime dependencies are Pillow, pydicom, and ReportLab.

## Examples

```bash
xray-mouth inspect data/ --recursive --output report.json
xray-mouth anonymize input.dcm output/anonymous.dcm
xray-mouth demo demo-output
xray-mouth series --patient "Synthetic Demo" --input demo-series --output-root reports --demo --strict
```

The clinical export places the patient name inside the sensitive artifacts but not in the export directory name. Filenames must begin with slots `01` through `14`. The renderer normalizes EXIF orientation, preserves image aspect ratio with black padding, rejects corrupt, disguised, multi-frame, oversized, symlinked, and high-bit-depth raster inputs, and never edits source images.

## What this project does not do

- diagnose, segment, classify, or recommend treatment;
- acquire images from hardware or provide a tested TWAIN/vendor SDK adapter;
- infer anatomy from pixels or validate that a file is assigned to the correct slot;
- guarantee DICOM anonymization or remove burned-in annotations;
- increase clinical detail by producing a 600-DPI-sized canvas.

## Development

```bash
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest
python -m build
python -m twine check dist/*
```

Use synthetic fixtures only in issues and pull requests. See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), [docs/architecture.md](docs/architecture.md), and the [deep audit](docs/deep-audit-2026-10-01.md).

## Release status

The published `v0.1.0` release contains the original dataset-inspection/DICOM tool. The combined command structure on this audit branch is unreleased development work (`0.2.0.dev0`). Do not describe it as a published or clinically validated release.

MIT © Douglas Casty. No patient datasets or clinical images are included.
