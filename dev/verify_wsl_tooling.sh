#!/usr/bin/env bash
# Verify basic Python and Node tooling in WSL for this project
set -euo pipefail
echo "=== dev/verify_wsl_tooling.sh ==="

echo "Checking OS..."
uname -a || true

echo "Checking python3..."
if command -v python3 >/dev/null 2>&1; then
  python3 --version
else
  echo "python3 not found" >&2
  exit 10
fi

echo "Checking pip3..."
if command -v pip3 >/dev/null 2>&1; then
  pip3 --version
else
  echo "pip3 not found" >&2
  exit 11
fi

echo "Testing virtualenv creation..."
TMP_VENV=".venv_verify_tmp"
python3 -m venv "$TMP_VENV"
if [ -d "$TMP_VENV" ]; then
  echo "Virtualenv created: $TMP_VENV"
  rm -rf "$TMP_VENV"
else
  echo "Failed to create virtualenv" >&2
  exit 12
fi

echo "Checking node..."
if command -v node >/dev/null 2>&1; then
  node --version
else
  echo "node not found" >&2
  exit 20
fi

echo "Checking npm (or pnpm/yarn)..."
if command -v npm >/dev/null 2>&1; then
  npm --version
elif command -v pnpm >/dev/null 2>&1; then
  pnpm --version
elif command -v yarn >/dev/null 2>&1; then
  yarn --version
else
  echo "no package manager (npm/pnpm/yarn) found" >&2
  exit 21
fi

echo "Optional: check project backend deps (requirements.txt)"
if [ -f requirements.txt ]; then
  echo "Found requirements.txt - performing pip check in isolated venv"
  python3 -m venv "$TMP_VENV"
  source "$TMP_VENV/bin/activate"
  pip install --upgrade pip >/dev/null
  pip install -r requirements.txt
  pip check || true
  deactivate
  rm -rf "$TMP_VENV"
else
  echo "requirements.txt not found - skipping backend dependency check"
fi

echo "Optional: check frontend deps (if frontend/ exists)"
if [ -d frontend ]; then
  if [ -f frontend/package-lock.json ] || [ -f frontend/package.json ]; then
    echo "Running npm ci in frontend/ (requires network)"
    (cd frontend && npm ci --silent) || echo "frontend npm ci failed (non-fatal)"
  fi
fi

echo "All checks completed"
exit 0
