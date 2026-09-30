# Architecture

XRay Mouth uses a deliberately small local pipeline:

```text
Image source -> validation -> protocol mapping -> non-destructive imaging -> layout -> preview / PDF / report
```

`FolderImageSource` provides candidate paths. Validation filters supported extensions, parses two-digit prefixes, rejects duplicate slots, and verifies image integrity. `Protocol` and `RadiographSlot` are the single source of truth for expected positions, so future 16- or 18-image protocols can supply their own slot data.

The imaging layer loads a copy, normalizes EXIF orientation, optionally applies configured contrast, and preserves aspect ratio with black padding. It never writes source images. The layout engine owns named normalized rectangles and renders images, missing markers, and discreet exam information. Workflow orchestration creates a patient-slugged timestamped export directory and writes the PNGs, A4 landscape PDF, and report. The 7016x4960 PNG is an A4 600-DPI render canvas; it does not increase source resolution or clinical detail.

## Future acquisition adapters

`devices.base.ImageSource` is the extension point for a later acquisition source. A tested `TwainImageSource` or `VendorSdkImageSource` could be added after real hardware validation, but neither is present today. Device drivers, calibration, and vendor documentation remain authoritative.
