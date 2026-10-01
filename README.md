# xray-mouth

[![CI](https://github.com/douglasncst/xray-mouth/actions/workflows/ci.yml/badge.svg)](https://github.com/douglasncst/xray-mouth/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

Privacy-first, reproducible tooling for dental X-ray dataset preparation.

`xray-mouth` helps researchers and developers inspect raster image collections, detect basic quality and filename-privacy risks, create machine-readable dataset reports, and write de-identified DICOM copies before collaboration.

> [!IMPORTANT]
> This project is research software. It is **not a medical device**, does not provide diagnoses, and must not be used to make clinical decisions. De-identification is context-dependent; review outputs against your institution's policies before sharing data.

## Why this project exists

Oral-imaging experiments often begin with one-off notebooks and undocumented preprocessing. That makes results difficult to reproduce and increases the risk of accidentally sharing identifiers. This project starts with the less glamorous but essential foundation: inspection, provenance, privacy checks, and documented workflows.

## Features

- Deterministic JSON inventory for PNG, JPEG, TIFF, BMP, and DICOM datasets
- SHA-256 provenance hashes for every discovered file
- Basic contrast, saturation, and edge-energy metrics for raster images
- Warnings for filenames that may contain patient identifiers
- Conservative DICOM de-identification that writes a new file and removes private tags
- No image or patient data is uploaded anywhere

## Installation

```bash
git clone https://github.com/douglasncst/xray-mouth.git
cd xray-mouth
python -m venv .venv
python -m pip install -e .
```

## Quick start

Inspect one image or a directory:

```bash
xray-mouth inspect samples/example.png
xray-mouth inspect data/ --recursive --output report.json
```

Write a de-identified DICOM copy:

```bash
xray-mouth anonymize input.dcm output/anonymous.dcm
```

The source file is never overwritten.

## Example report

```json
{
  "schema_version": "1.0",
  "file_count": 1,
  "privacy_warning_count": 0,
  "items": [
    {
      "path": "example.png",
      "format": "PNG",
      "width": 1024,
      "height": 512,
      "mean_intensity": 91.7,
      "warnings": []
    }
  ]
}
```

## Development

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md), the [roadmap](ROADMAP.md), and the [security policy](SECURITY.md).

## Privacy and responsible use

- Work only with data you are authorized to use.
- Keep raw clinical data outside the repository.
- Treat automated de-identification as one control in a broader review process.
- Do not use repository outputs for diagnosis, treatment, or emergency decisions.
- Report security or privacy concerns through the process in [SECURITY.md](SECURITY.md).

## License

MIT © Douglas Casty. Third-party datasets and images retain their own licenses and are not included.
