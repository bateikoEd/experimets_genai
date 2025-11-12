# Running tests

This project includes unit and integration tests under `tests/` and some tests under `src/`.

Quick ways to run tests locally:

1. Activate your virtual environment (recommended):

   ```bash
   source .venv-311/bin/activate
   ```

2. Run all tests (uses `pytest.ini`):

   ```bash
   python -m pytest
   # or use the helper script
   scripts/run_tests.sh
   ```

3. Run a single test file:

   ```bash
   python -m pytest src/evaluation/test_evaluator.py::test_perfect_prediction_has_zero_errors_and_r2_one -q
   ```

Notes:
- `tests/conftest.py` ensures the project `src/` directory is on `sys.path` when pytest runs, so imports like `from evaluation.evaluator import ModelEvaluator` work.
- Some test files include a small bootstrap to make them runnable directly (e.g., `src/evaluation/test_evaluator.py`). Prefer running via `pytest` for consistency.
