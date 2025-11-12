#!/usr/bin/env bash
set -euo pipefail

# Run pytest for the project. This script uses the active Python interpreter
# (so activate your venv first) or you can call it with an explicit Python:
#   /path/to/.venv/bin/python scripts/run_tests.sh

PYTEST_OPTS="${@:-}" 

PYTHON_CMD=${PYTHON:-}
if [ -z "$PYTHON_CMD" ]; then
	if [ -x "./.venv-311/bin/python" ]; then
		PYTHON_CMD="./.venv-311/bin/python"
	elif command -v python3 >/dev/null 2>&1; then
		PYTHON_CMD="python3"
	elif command -v python >/dev/null 2>&1; then
		PYTHON_CMD="python"
	else
		echo "Error: no python interpreter found. Activate a venv or set PYTHON env var." >&2
		exit 1
	fi
fi

echo "Running tests with: $($PYTHON_CMD -V 2>&1)"
$PYTHON_CMD -m pytest $PYTEST_OPTS
