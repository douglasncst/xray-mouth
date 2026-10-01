# Synthetic demo

The demo is designed so anyone can evaluate `xray-mouth` without finding, downloading, or handling clinical data.

## Run it

```bash
python -m pip install -e .
xray-mouth demo demo-output
```

Expected output:

```text
Created 3 synthetic images in demo-output
Report: demo-output/report.json
```

The generated directory contains:

- `synthetic_dental_xray.png`: a deterministic, X-ray-like illustration generated in code;
- `synthetic_underexposed.png`: triggers the mostly-dark and low-contrast checks;
- `synthetic_overexposed.png`: triggers the mostly-bright and low-contrast checks;
- `report.json`: hashes, dimensions, intensity metrics, edge energy, and warnings.

## What this proves

The demo verifies installation, file discovery, deterministic hashing, image decoding, quality indicators, privacy-safe filenames, and JSON serialization. It does not measure diagnostic accuracy and must not be described as clinical validation.

## Next experiment

Run the inspector separately and compare the report:

```bash
xray-mouth inspect demo-output --output second-report.json
```

The image hashes and metrics should match the original report. The report file itself is intentionally ignored because it is not a supported image format.
