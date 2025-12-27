#!/bin/sh
set -euo pipefail

echo "Checking required binaries..."
command -v python >/dev/null 2>&1 || { echo "python not found"; exit 2; }
command -v node >/dev/null 2>&1 || { echo "node not found"; exit 3; }

if command -v pnpm >/dev/null 2>&1; then
  PNPM_VER=$(pnpm --version)
  echo "pnpm ${PNPM_VER}"
elif command -v npm >/dev/null 2>&1; then
  NPM_VER=$(npm --version)
  echo "npm ${NPM_VER}"
else
  echo "no node package manager found (pnpm/npm)"; exit 4
fi

echo "Python: $(python --version 2>&1)"
echo "Node: $(node --version 2>&1)"

POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5432}

echo "ENV VARS: POSTGRES_HOST=${POSTGRES_HOST} POSTGRES_PORT=${POSTGRES_PORT}"

# TCP check using nc or python socket
if command -v nc >/dev/null 2>&1; then
  echo "Attempting TCP connect with nc to ${POSTGRES_HOST}:${POSTGRES_PORT}..."
  if nc -z ${POSTGRES_HOST} ${POSTGRES_PORT}; then
    echo "TCP connect OK"
  else
    echo "TCP connect FAILED"; exit 5
  fi
elif command -v python >/dev/null 2>&1; then
  echo "Attempting TCP connect with python to ${POSTGRES_HOST}:${POSTGRES_PORT}..."
  python - <<PY
import socket,sys
s=socket.socket()
try:
    s.settimeout(3)
    s.connect(("${POSTGRES_HOST}", int(${POSTGRES_PORT})))
    print('TCP connect OK')
except Exception as e:
    print('TCP connect FAILED:', e)
    sys.exit(5)
finally:
    s.close()
PY
else
  echo "neither nc nor python available for TCP check"; exit 6
fi

# Optional Postgres auth check using psycopg
if [ "${VERIFY_PG_AUTH:-0}" = "1" ] || [ "${VERIFY_PG_AUTH:-0}" = "true" ]; then
  echo "VERIFY_PG_AUTH enabled — attempting Postgres authentication check"
  if ! command -v python >/dev/null 2>&1; then
    echo "python required for auth check"; exit 7
  fi
  python - <<PY
import os,sys
  try:
    import psycopg
    have_psycopg = True
except Exception as e:
    print('psycopg not installed:', e)
    have_psycopg = False
host=os.environ.get('POSTGRES_HOST','localhost')
port=int(os.environ.get('POSTGRES_PORT','5432'))
user=os.environ.get('POSTGRES_USER')
password=os.environ.get('POSTGRES_PASSWORD')
dbname=os.environ.get('POSTGRES_DB', 'postgres')
if not user or not password:
    print('POSTGRES_USER and POSTGRES_PASSWORD required for auth check')
    sys.exit(9)
if have_psycopg:
  try:
    conn=psycopg.connect(host=host, port=port, user=user, password=password, dbname=dbname, connect_timeout=5)
    conn.close()
    print('Postgres auth OK (psycopg)')
    sys.exit(0)
  except Exception as e:
    print('Postgres auth FAILED (psycopg):', e)
    sys.exit(10)
else:
  # fallback to psql if available
  import shutil, subprocess
  psql_path = shutil.which('psql')
  if not psql_path:
    print('neither psycopg nor psql available for auth check')
    sys.exit(8)
  # use PGPASSWORD env to avoid interactive prompt
  env = os.environ.copy()
  env['PGPASSWORD'] = password
  cmd = [psql_path, '-h', host, '-p', str(port), '-U', user, '-d', dbname, '-c', '\\q']
  try:
    subprocess.run(cmd, check=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    print('Postgres auth OK (psql)')
    sys.exit(0)
  except subprocess.CalledProcessError as e:
    print('Postgres auth FAILED (psql):', e.stderr.decode() if e.stderr else e)
    sys.exit(10)
  except Exception as e:
    print('Postgres auth FAILED (psql):', e)
    sys.exit(10)
PY
fi

echo "verify_env completed"
exit 0
#!/bin/sh
set -eu
# Enhanced environment verification script for developers/CI
# Exit codes:
# 0 = success
# 2 = missing python
# 3 = missing node
# 4 = missing node package manager
# 5 = missing nc (used for TCP checks)
# 6 = postgres TCP check failed
# 7 = verify_postgres_connection.py failure

echo "---- verify_env: starting checks ----"

check_cmd() {
  CMD=$1
  MSG=$2
  if command -v "$CMD" >/dev/null 2>&1; then
    echo "$MSG: $( $CMD --version 2>&1 | head -n1 )"
    return 0
  else
    echo "$MSG not found: $CMD" >&2
    return 1
  fi
}

echo "Checking Python..."
if ! check_cmd python "Python"; then
  exit 2
fi

echo "Checking Node..."
if ! check_cmd node "Node"; then
  exit 3
fi

echo "Checking package manager..."
if command -v pnpm >/dev/null 2>&1; then
  pnpm --version
elif command -v npm >/dev/null 2>&1; then
  npm --version
else
  echo "No known Node package manager (pnpm/npm) found" >&2
  exit 4
fi

echo "Environment variables (masked)"
echo "POSTGRES_HOST=${POSTGRES_HOST:+set} POSTGRES_PORT=${POSTGRES_PORT:+set} DATABASE_URL=${DATABASE_URL:+set}"

HOST=${POSTGRES_HOST:-localhost}
PORT=${POSTGRES_PORT:-5432}

if command -v nc >/dev/null 2>&1; then
  echo "Testing TCP connectivity to ${HOST}:${PORT}"
  if nc -zv "$HOST" "$PORT" >/dev/null 2>&1; then
    echo "TCP port ${PORT} on ${HOST} is reachable"
  else
    echo "TCP check failed for ${HOST}:${PORT}" >&2
    # return non-zero so CI can fail; Story may accept absence but script signals failure
    exit 6
  fi
else
  echo "nc not found; skipping TCP connectivity check" >&2
  echo "Install 'nc' (netcat) for full connectivity checks" >&2
  # don't treat as fatal for basic env verification
fi

# If a python-based Postgres verifier exists, run it and propagate its exit code
if [ -x ./dev/verify_postgres_connection.py ]; then
  echo "Running python-based Postgres connection verifier"
  ./dev/verify_postgres_connection.py || exit 7
else
  echo "No executable ./dev/verify_postgres_connection.py found; skipping DB auth check"
fi

echo "---- verify_env: completed successfully ----"
