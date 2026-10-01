# XRay Mouth

XRay Mouth is a small, local Python utility for organizing individual intraoral radiographs into a standardized periapical-series PDF. It is an early alpha (0.1.0); the name is provisional.

It exists for clinics that receive individual digital images and need a clean, consistent document without changing the original files. XRay Mouth does not interpret radiographs and does not provide medical or dental diagnosis.

## Current capabilities

- Reads PNG, JPG/JPEG, TIFF, and BMP files from a folder.
- Maps two-digit filename prefixes `01` through `14` to a configurable protocol.
- Detects duplicate slots, byte-identical files in different slots, and unreadable images before rendering.
- Applies EXIF orientation only to an in-memory render copy; original files are never modified.
- Builds a black-background layout with clear missing-slot markers.
- Generates a preview PNG, an A4-targeted `600dpi` raster render, an A4 landscape PDF, and a text report in a timestamped directory.
- Includes a synthetic, explicitly non-diagnostic demo mode.

The high-resolution raster is sized for 600 DPI at A4 landscape (7016x4960 pixels). This describes the render target only: pixel count cannot establish source resolution or increase clinical detail.

## Install

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell (instead of the command above):
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Usage

```bash
xray-mouth --patient "Patient Name" --input ./input_images --output-root ./reports
```

Use `--strict` to require all protocol positions. `--contrast 1.0` leaves contrast unchanged; a different positive value affects rendered copies only. On Windows, `--open` opens the resulting PDF.

Contrast must be finite and greater than zero. Patient names must contain 1–200 characters (with non-whitespace content) and no control characters. Long display text is shortened to fit the layout; the text report retains the full name. Exit codes are `0` for a completed export, `1` for an input/export error, and `2` for argument errors. Failure to open an already-saved PDF produces a warning.

Run a synthetic demo without patient data:

```bash
xray-mouth --patient "Demo Patient" --input ./demo_images --output-root ./reports --demo
```

Demo requires a new or empty input folder and refuses to reuse existing images or other files. Use a fresh folder for each demo run; this prevents patient images from being included in an export labeled synthetic.

On Windows, `run_windows.bat` runs the local source tree using an existing `.venv` when available (or Python 3 from the launcher). It never installs Python or dependencies; it explains what is missing and keeps the terminal open on errors.

## File naming

Prefix each image with its two-digit slot number, for example:

```text
01_radiograph.png
02_upper_right.tif
14_lower_left.tiff
```

The default 14-position protocol is: superior posterior right, superior anterior right, superior incisors, superior anterior left, superior posterior left, lateral upper/lower right, lateral upper/lower left, lower posterior right, lower anterior right, lower incisors, lower anterior left, and lower posterior left. Missing positions are allowed unless `--strict` is used. Duplicate prefixes are errors.

Slots are assigned **only by filename**, not by image content. There is no automatic exam-type classification, tooth recognition, or check that a radiograph actually belongs in its labeled position. The shipped renderer supports exactly the 14-position protocol. Files without an ASCII two-digit prefix and unsupported extensions are ignored; subfolders are not scanned. Byte-identical files assigned to different slots are rejected, but re-encoded or visually similar duplicates are not detected.

Supported image content is single-frame PNG, JPEG, TIFF, or BMP. Multipage/animated files, symlinked images, oversized images detected by Pillow, and high-bit-depth (`I`, `I;16`, `F`) inputs are rejected. Export individual pages and explicitly convert high-bit-depth images to 8-bit using your acquisition software before importing; XRay Mouth does not perform clinical windowing. EXIF orientation is applied, transparency is composited onto black, and copies are converted to grayscale without modifying originals.

## Outputs

Every run writes a new directory such as `reports/Patient_Name_2026-09-30_15-30-12/` containing:

- `periapical_series_preview.png`
- `periapical_series_600dpi.png`
- `periapical_series.pdf`
- `report.txt`

The detail PNG includes 600-DPI metadata. Small source images are scaled to fit their slots with aspect ratio preserved, which does not add detail. Ordinary export failures remove the newly created partial result directory and preserve earlier exports; a process crash or forced termination can still leave partial files.

## Privacy and limitations

XRay Mouth has no telemetry, cloud integration, or network transfer of images. Healthcare data carries privacy obligations; users are responsible for their applicable laws and organizational policies. Do not commit real patient images to this repository.

Patient names appear in directory names, the rendered documents, the text report, and the CLI's output path. Use a pseudonymous identifier when appropriate and treat terminal logs and exports as sensitive. New export directories use owner-only permissions on POSIX; Windows permissions depend on the folder ACL. Files are not encrypted, and existing output-root permissions are not changed. Source EXIF metadata is not copied into rendered outputs, but identifying text already visible in source pixels remains visible. In Codex Cloud, local processing occurs on the cloud machine: do not upload patient data without authorization and suitable organizational controls. Audit tests use synthetic images only.

This project is not clinical software, is not certified or approved for diagnostic use, and makes no claim of diagnostic accuracy or compatibility with a particular sensor.

## Future hardware integration

The code exposes an `ImageSource` abstraction. Today it includes only `FolderImageSource`. Future adapters may support TWAIN or vendor SDK acquisition after physical hardware testing. No direct device integration is currently shipped.

## Development

```bash
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest
pytest --cov=xray_mouth --cov-report=term-missing
```

CI runs lint, formatting, and tests on Python 3.11 and 3.12. No static type checker is configured as a project dependency; the audit additionally checked source with `mypy` and `types-reportlab` installed only in the development environment. Windows launcher/device behavior still requires native Windows and hardware validation.

See [architecture](docs/architecture.md), [hardware integration](docs/hardware-integration.md), and [contributing](CONTRIBUTING.md).

XRay Mouth is released under the [MIT License](LICENSE).

## Roadmap

- Validate acquisition workflows with physical hardware and vendor drivers.
- Add optional, tested acquisition adapters.
- Support additional configurable protocols such as 16- and 18-image series.
- Keep the core local, non-diagnostic, and privacy-minded.
