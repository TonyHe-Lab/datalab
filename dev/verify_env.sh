#!/usr/bin/env sh
set -eu

# dev/verify_env.sh
# Purpose: quick deterministic environment verification for local dev and CI.
# Exit codes (high level):
# 0 = success
# 2 = missing python
# 3 = missing node
# 4 = missing node package manager (pnpm/npm)
# 5 = tcp connectivity failed
# 6 = postgres verifier failed (propagates verifier exit codes)
#
# Usage:
#   ./dev/verify_env.sh
#   POSTGRES_HOST=localhost POSTGRES_PORT=5432 ./dev/verify_env.sh
#   VERIFY_PG_AUTH=1 POSTGRES_USER=... POSTGRES_PASSWORD=... ./dev/verify_env.sh
#
# In CI: see .github/workflows/env-verify.yml (GitHub Actions workflow_dispatch)

echo "---- verify_env: starting checks ----"

check_has() {
  command -v "$1" >/dev/null 2>&1
}

# Prefer python3, fallback to python
if check_has python3; then
  PYTHON_CMD=python3
elif check_has python; then
  PYTHON_CMD=python
else
  echo "ERROR: neither python nor python3 found" >&2
  exit 2
fi
echo "Python: $($PYTHON_CMD --version 2>&1 | head -n1)"

if ! check_has node; then
  echo "ERROR: node not found" >&2
  exit 3
fi
echo "Node: $(node --version 2>&1 | head -n1)"

if check_has pnpm; then
  echo "pnpm: $(pnpm --version)"
elif check_has npm; then
  echo "npm: $(npm --version)"
else
  echo "ERROR: no Node package manager (pnpm/npm) found" >&2
  exit 4
fi

HOST=${POSTGRES_HOST:-localhost}
PORT=${POSTGRES_PORT:-5432}

echo "ENV VARS: POSTGRES_HOST=${POSTGRES_HOST:+set} POSTGRES_PORT=${POSTGRES_PORT:+set} DATABASE_URL=${DATABASE_URL:+set}"

# TCP check
if check_has nc; then
  echo "Testing TCP connectivity to ${HOST}:${PORT} using nc..."
  if nc -zv "${HOST}" "${PORT}" >/dev/null 2>&1; then
    echo "TCP connect OK"
  else
    echo "ERROR: TCP connect FAILED to ${HOST}:${PORT}" >&2
    exit 5
  fi
else
  echo "nc not found; attempting TCP connect with python socket fallback"
  $PYTHON_CMD - <<PY
import socket,os,sys
host=os.getenv('POSTGRES_HOST','localhost')
port=int(os.getenv('POSTGRES_PORT','5432'))
s=socket.socket()
try:
    s.settimeout(3)
    s.connect((host, port))
    print('TCP connect OK')
except Exception as e:
    print('TCP connect FAILED:', e)
    sys.exit(5)
finally:
    s.close()
PY
fi

# If postgres verifier exists, run it and propagate its exit code
if [ -f ./dev/verify_postgres_connection.py ]; then
  echo "Running ./dev/verify_postgres_connection.py to validate DB auth/connectivity"
  $PYTHON_CMD ./dev/verify_postgres_connection.py || {
    RC=$?
    echo "Postgres verifier exited with code ${RC}" >&2
    exit 6
  }
else
  echo "No ./dev/verify_postgres_connection.py found; skipping DB auth check"
fi

echo "---- verify_env: completed successfully ----"
exit 0
