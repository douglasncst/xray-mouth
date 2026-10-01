# Deep pre-release audit — 2026-10-01

## Executive verdict

`xray-mouth` has a credible small OSS foundation, but the public repository had two materially different products under one name. `main` (`40e958d`) was a privacy-oriented dataset/DICOM utility; `codex/audit-xray-mouth` (`a48792c`) was a raster-only clinical-series exporter; `feat/uniform-3x4-clinical-layout` (`0f48b2a`) was already fully merged into the latter by PR #7. Treating those branches as interchangeable would misstate the released product and its privacy properties.

This branch combines them only behind explicit command boundaries (`inspect`, `anonymize`, `demo`, `series`), labels the combined version `0.2.0.dev0`, and does not publish a release. The architecture is reasonable for an alpha research tool after the corrections below, but it is not ready for clinical deployment or claims of standards-compliant anonymization.

## Scope and evidence

- Compared commit graphs, trees, diffs, packaging, docs, tests, workflows, issues, PRs, release metadata, and public repository metadata.
- Baseline `main`: 8 tests passed on Python 3.13/Windows, 92% measured coverage, Ruff clean, sdist/wheel built.
- Baseline clinical branch: 59 tests passed and 1 failed on Windows. The failure was a non-portable test that attempted a filename containing a newline; Ruff passed and distributions built with a setuptools license deprecation warning.
- Public state at audit time: MIT, 0 stars, 1 fork, three open issues, PR #6 plus two Dependabot PRs open, PR #7 merged, and release `v0.1.0` with wheel/sdist assets. Latest `main`, clinical branch, and layout PR CI runs were green. CodeQL was green on `main`; external PR checks showed `action_required`, not a code failure.

## Findings and dispositions

| Severity | Finding | Evidence / risk | Disposition |
|---|---|---|---|
| P0 | Product identity diverged across branches | Same package/version/CLI name described unrelated DICOM and clinical export contracts. A future merge could silently replace released behavior. | Fixed: explicit subcommands, combined `0.2.0.dev0`, unified dependencies/docs; no release. |
| P0 | DICOM helper overstated its scope as a “basic profile” | It clears a short list and private tags but does not implement the DICOM PS3.15 Basic Application Confidentiality Profile, inspect burned-in pixels, or apply a configurable attribute policy. | Fixed claim: method now says “limited direct-identifier removal”; README has an unambiguous warning. Full profile remains deferred. |
| P1 | Existing DICOM destination could be overwritten | `save_as(destination)` replaced an unrelated prior artifact. | Fixed: refuse existing/symlink destinations, write a temporary sibling, then replace atomically. |
| P1 | Patient identity leaked through export directory names and CLI output | Patient slug was part of every result path. Directory listings, backups, and terminal logs could expose PHI. | Fixed: generic `xray-mouth_<timestamp>` directories and non-path CLI success output. Patient identity remains inside sensitive export content by design. |
| P1 | Cleanup had a filesystem race surface | Broad `rmtree` ran after any export exception. | Hardened: cleanup only when the created path remains a direct child of the configured root and is not a symlink. Forced termination can still leave partial output. |
| P1 | PDF metadata was uncontrolled | ReportLab defaults did not express a stable, non-patient metadata policy. | Fixed: deterministic generic author/creator/title/subject; no patient data in PDF metadata. |
| P1 | Clinical tests were Linux-specific | A control-character filename cannot be created on Windows. | Fixed: platform guard; the sanitizer behavior remains tested where the filesystem supports the fixture. |
| P1 | 3:4 film geometry depended on canvas aspect ratio | Normalized width and height only produced 3:4 on A4 landscape sizes. | Fixed: slot rectangles carry an explicit 3:4 pixel ratio; regression coverage includes 4:3, 16:9, preview, and 600-DPI canvases. |
| P1 | Branch pushes could bypass CI | Workflow only ran pushes to `main`; the clinical branch had its own broader workflow history. | Fixed: CI runs for `codex/**`, `feat/**`, and `fix/**`, plus pull requests, and checks formatting. |
| P2 | Packaging backend/license metadata diverged | Hatchling vs setuptools and a deprecated license table generated warnings. | Fixed: one Hatchling configuration, SPDX license expression, Python 3.10+, unified runtime/dev dependencies. |
| P2 | Public release and branch claims were easy to conflate | `v0.1.0` contains only the original toolkit. | Fixed in README/release-status text; no invented adoption, validation, or performance claims. |

## Privacy and DICOM boundary

The anonymizer is a conservative metadata helper, not a disclosure authorization system. It does not detect names, labels, dates, or other identifiers burned into `PixelData`; it does not implement every conditional action in DICOM PS3.15; it does not guarantee referential consistency for arbitrary nested UID graphs; and it cannot decide whether dates, device identifiers, geography, or free text are identifying in a particular jurisdiction or study.

Before external disclosure, use an institution-approved de-identification pipeline and human review, validate a declared PS3.15 option set against representative synthetic fixtures, scan rendered pixels for annotations, inspect all sequences/private creators, and document the policy/version applied. Real patient files must never be committed or attached to public issues.

## Renderer and export invariants

- Protocol is exactly slots `01`–`14`; no anatomical inference is performed.
- Every slot is portrait 3:4 in pixel space for all tested canvases.
- Source aspect ratio is preserved with black padding; EXIF orientation is applied only to an in-memory render copy.
- Missing slots remain explicit; strict mode rejects incomplete series.
- Corrupt, disguised, multi-frame, high-bit-depth, oversized, symlinked, duplicate-slot, and byte-identical cross-slot inputs are rejected.
- Preview and high-resolution renders use the same geometry. A 600-DPI-sized canvas does not create source detail.
- Export artifacts intentionally contain patient/exam text and must be treated as sensitive. The source files are not modified.

## Architecture recommendation

Keep one repository while the shared surface is small, with four stable command groups and modules separated by responsibility. Dataset inspection/DICOM logic must not import the clinical renderer. The raster validator/layout/export path may share only generic file and safety helpers. If hardware acquisition or a standards-conformant DICOM de-identification engine becomes a real roadmap item, split it into an optional package or separately versioned component before adding vendor SDKs or regulatory claims.

Do not merge new clinical behavior directly into a released privacy command, do not reuse `demo` for two meanings, and do not add “AI”, diagnostic, validated, or compliant language without evidence.

## Deferred work

1. Implement a policy-driven PS3.15 de-identification engine or integrate a maintained specialist library, with recursive sequence handling, UID mapping, burned-in annotation controls, conformance fixtures, and documented option selections.
2. Add Linux/macOS/Windows CI and artifact smoke-install tests from the built wheel; current GitHub CI is Ubuntu-only.
3. Pin third-party GitHub Actions to immutable commit SHAs and add dependency review, SBOM, artifact attestations/provenance, and Trusted Publishing before the next release.
4. Make exports fully transactional with a staging directory and final rename; define retention/deletion behavior and Windows ACL expectations.
5. Add PDF inspection tests for page size, metadata, image fit, absence of source EXIF/text leakage, and deterministic synthetic output.
6. Decide whether PR #6 should be rebased or superseded; its duplicate-detection feature overlaps the clinical path but targets the dataset report.
7. Add maintainership metadata (`CODEOWNERS`, support policy, governance/maintainer succession) when a second maintainer exists. Do not fabricate community adoption.

## Release gate

A future release should require: green matrix CI, Ruff check/format, full tests, sdist/wheel build, Twine validation, clean install/smoke test from the wheel, CodeQL, reviewed changelog, exact CLI/docs agreement, synthetic-only fixtures, and an explicit decision on whether limited DICOM removal remains exposed. Clinical or compliance claims require separate domain validation and are not satisfied by this software test suite.
