# Contributing

Create a virtual environment and install development dependencies:

```bash
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest
pytest --cov=xray_mouth --cov-report=term-missing
```

Keep changes focused, typed, and covered by synthetic tests. Submit pull requests with a clear description and verification results. Never submit real patient data, identifiable radiographs, or credentials.

CI uses Python 3.11 and 3.12. Validate both for compatibility changes. Use temporary input/output folders and synthetic fixtures for CLI and regression tests, including failure paths. Static source checking can be run separately with `mypy src/xray_mouth` after installing `mypy` and `types-reportlab`; these are optional audit tools, not runtime dependencies.
