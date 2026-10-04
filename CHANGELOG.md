# Changelog

All notable changes will be documented here.

## [Unreleased]

## [0.2.0] - 2026-10-03

### Changed

- Process every immediate patient folder under `xray` and use its folder name in the report.
- Generate the displayed report date at runtime instead of embedding a fixed patient and date.
- Updated the report mount from 16 to 14 radiographs.
- Locked the approved Green Smile canvas to 1672 x 941 pixels with measured film coordinates.
- Arranged four landscape films on each side and three portrait films in each central row.
- Included the approved green/orange clinic artwork with white labels and orange identification.
- Matched the numbered filenames to their anatomical groups and preserved the approved rounded corners.
- Unified the Windows script and installed `xray-mouth report` command under one report generator.
- Packaged the approved header with the wheel so installed reports keep the same appearance.
- Fixed initial Python environment creation in the Windows runner.
- Added rendered PNG/PDF regression checks and browser installation to CI.
- Updated tests, documentation, and the Windows runner for the 14-image workflow.

## [0.1.0] - 2026-10-01

### Added

- Dataset inspection CLI with JSON output and provenance hashes
- Raster quality and filename privacy warnings
- DICOM de-identification command that preserves source files
- Automated tests and GitHub Actions CI
- Contributor, security, conduct, and roadmap documentation

[Unreleased]: https://github.com/douglasncst/xray-mouth/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/douglasncst/xray-mouth/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/douglasncst/xray-mouth/releases/tag/v0.1.0
