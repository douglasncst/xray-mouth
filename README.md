# XRay Mouth

XRay Mouth is a small, local Python utility for organizing individual intraoral radiographs into a standardized periapical-series PDF. It is an early alpha (0.1.0); the name is provisional.

It exists for clinics that receive individual digital images and need a clean, consistent document without changing the original files. XRay Mouth does not interpret radiographs and does not provide medical or dental diagnosis.

## Current capabilities

- Reads PNG, JPG/JPEG, TIFF, and BMP files from a folder.
- Maps two-digit filename prefixes `01` through `14` to a configurable protocol.
- Detects duplicate slots and unreadable images before rendering.
- Applies EXIF orientation only to an in-memory render copy; original files are never modified.
- Builds a black-background layout with clear missing-slot markers.
- Generates a preview PNG, an A4-targeted `600dpi` raster render, an A4 landscape PDF, and a text report in a timestamped directory.
- Includes a synthetic, explicitly non-diagnostic demo mode.

The high-resolution raster is sized for 600 DPI at A4 landscape (7016x4960 pixels). This describes the render target only: pixel count cannot establish source resolution or increase clinical detail.

## Install

```bash
python -m venv .venv
.venv\\Scripts\\activate  # Windows
python -m pip install -e ".[dev]"
```

## Usage

```bash
xray-mouth --patient "Patient Name" --input ./input_images --output-root ./reports
```

Use `--strict` to require all protocol positions. `--contrast 1.0` leaves contrast unchanged; a different positive value affects rendered copies only. On Windows, `--open` opens the resulting PDF.

Run a synthetic demo without patient data:

```bash
xray-mouth --patient "Demo Patient" --input ./demo_images --output-root ./reports --demo
```

On Windows, `run_windows.bat` runs the local source tree using an existing `.venv` when available (or Python 3 from the launcher). It never installs Python or dependencies; it explains what is missing and keeps the terminal open on errors.

## File naming

Prefix each image with its two-digit slot number, for example:

```text
01_radiograph.png
02_upper_right.tif
14_lower_left.tiff
```

The default 14-position protocol is: superior posterior right, superior anterior right, superior incisors, superior anterior left, superior posterior left, lateral upper/lower right, lateral upper/lower left, lower posterior right, lower anterior right, lower incisors, lower anterior left, and lower posterior left. Missing positions are allowed unless `--strict` is used. Duplicate prefixes are errors.

## Outputs

Every run writes a new directory such as `reports/Patient_Name_2026-09-30_15-30-12/` containing:

- `periapical_series_preview.png`
- `periapical_series_600dpi.png`
- `periapical_series.pdf`
- `report.txt`

## Privacy and limitations

XRay Mouth has no telemetry, cloud integration, or network transfer of images. Healthcare data carries privacy obligations; users are responsible for their applicable laws and organizational policies. Do not commit real patient images to this repository.

This project is not clinical software, is not certified or approved for diagnostic use, and makes no claim of diagnostic accuracy or compatibility with a particular sensor.

## Future hardware integration

The code exposes an `ImageSource` abstraction. Today it includes only `FolderImageSource`. Future adapters may support TWAIN or vendor SDK acquisition after physical hardware testing. No direct device integration is currently shipped.

## Development

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest
```

See [architecture](docs/architecture.md), [hardware integration](docs/hardware-integration.md), and [contributing](CONTRIBUTING.md).

XRay Mouth is released under the [MIT License](LICENSE).

## Roadmap

- Validate acquisition workflows with physical hardware and vendor drivers.
- Add optional, tested acquisition adapters.
- Support additional configurable protocols such as 16- and 18-image series.
- Keep the core local, non-diagnostic, and privacy-minded.
