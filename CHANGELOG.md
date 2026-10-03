# Changelog

All notable changes will be documented here.

## [Unreleased]

### Changed

- Updated the report mount from 16 to 14 radiographs.
- Rebuilt the canvas as a 1600 x 1278 black clinical layout based on the new reference geometry.
- Arranged four landscape films on each side and three portrait films in each central row.
- Simplified the header to match the reference's black-background presentation while retaining Green Smile branding.
- Updated tests, documentation, and the Windows runner for the 14-image workflow.

## [0.1.0] - 2026-10-01

### Added

- Dataset inspection CLI with JSON output and provenance hashes
- Raster quality and filename privacy warnings
- DICOM de-identification command that preserves source files
- Automated tests and GitHub Actions CI
- Contributor, security, conduct, and roadmap documentation

[Unreleased]: https://github.com/douglasncst/xray-mouth/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/douglasncst/xray-mouth/releases/tag/v0.1.0
