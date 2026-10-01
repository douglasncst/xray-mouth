# Contributing

Thank you for helping make dental-imaging research workflows safer and more reproducible.

## Before opening a pull request

1. Open or comment on an issue for substantial changes.
2. Never commit clinical data, patient identifiers, credentials, or proprietary datasets.
3. Add tests for behavior changes.
4. Run `ruff check .` and `pytest` locally.
5. Explain privacy, compatibility, and reproducibility implications in the pull request.

## Development setup

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
ruff check .
pytest
```

## Scope

Good first contributions include format support, documentation, test fixtures made from synthetic data, accessibility improvements, and reproducibility tooling. Diagnostic claims and patient-derived samples are out of scope.

Issues labeled `good first issue` are intentionally small and include acceptance criteria. Maintainers
aim to acknowledge contributions within seven days. Project decisions and maintainer responsibilities
are described in [GOVERNANCE.md](GOVERNANCE.md).

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
