# Architecture

XRay Mouth uses a deliberately small local pipeline:

```text
Image source -> validation -> protocol mapping -> non-destructive imaging -> layout -> preview / PDF / report
```

`FolderImageSource` provides candidate paths. Validation filters supported extensions, parses two-digit prefixes, rejects duplicate slots, and verifies image integrity. `Protocol` and `RadiographSlot` are the single source of truth for expected positions, so future 16- or 18-image protocols can supply their own slot data.

The current workflow explicitly rejects protocols other than exactly slots 01–14 before writing files; extending the domain model alone is not enough to support another layout. Slot mapping uses filenames only and does not classify exam types or infer anatomical identity from pixels. Validation decodes the entire image, rejects unsupported content, multiple frames and high-bit-depth data, and checks SHA-256 for byte-identical files in different slots. Visually similar or re-encoded duplicates remain outside this check.

The imaging layer loads a copy, normalizes EXIF orientation, optionally applies configured contrast, and preserves aspect ratio with black padding. It never writes source images. The layout engine owns named normalized rectangles and renders images, missing markers, and discreet exam information. Workflow orchestration creates a patient-slugged timestamped export directory and writes the PNGs, A4 landscape PDF, and report. The 7016x4960 PNG is an A4 600-DPI render canvas; it does not increase source resolution or clinical detail.

Transparency is composited on black. Display text is bounded to each region; the report preserves full patient and metadata text and escapes non-printable filename/metadata characters. The workflow reserves its own output directory with owner-only POSIX access, retries creation collisions, and removes that directory on ordinary export errors. Filesystem errors become application errors that the CLI renders without a traceback or underlying filesystem path. This is not a crash-atomic transaction: forced termination or a failure during cleanup can leave partial files. Existing exports and original images are preserved. Input folders should not be modified concurrently while an export is running.

## Future acquisition adapters

`devices.base.ImageSource` is the extension point for a later acquisition source. A tested `TwainImageSource` or `VendorSdkImageSource` could be added after real hardware validation, but neither is present today. Device drivers, calibration, and vendor documentation remain authoritative.
