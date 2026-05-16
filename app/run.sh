#!/usr/bin/env bash
set -euo pipefail

# Tests are mounted in /eval_assets by the validator script.
# Code under test lives in /app.
export PYTHONPATH="/app:${PYTHONPATH:-}"

APP_UNDER_TEST="${APP_UNDER_TEST:-/app}"
TESTS_DIR="${TESTS_DIR:-/eval_assets}"

cd "$APP_UNDER_TEST"
export PYTHONPATH="$APP_UNDER_TEST:${PYTHONPATH:-}"
# Use verbose pytest output so parsing.py can extract per-test statuses deterministically.
pytest -vv -rA "$TESTS_DIR"
