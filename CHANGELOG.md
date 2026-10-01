# Changelog

## Unreleased — 0.2.0.dev0

- Combine dataset/DICOM and clinical-series capabilities behind explicit subcommands.
- Remove patient identity from export directory names and PDF metadata.
- Refuse DICOM destination overwrite and use atomic destination publication.
- Enforce 3:4 slot geometry across supported canvas aspect ratios.
- Add cross-platform CI/format coverage and document the true DICOM privacy boundary.

All notable changes will be documented here.

## [Unreleased]

## [0.1.0] - 2026-10-01

### Added

- Dataset inspection CLI with JSON output and provenance hashes
- Raster quality and filename privacy warnings
- DICOM de-identification command that preserves source files
- Automated tests and GitHub Actions CI
- Contributor, security, conduct, and roadmap documentation

[Unreleased]: https://github.com/douglasncst/xray-mouth/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/douglasncst/xray-mouth/releases/tag/v0.1.0
