#!/bin/sh
set -e
# Minimal environment verification script for developers/CI
echo "Checking Python..."
python --version || { echo "Python not found"; exit 2; }

echo "Checking Node..."
node --version || { echo "Node not found"; exit 3; }

echo "Checking package manager..."
if command -v pnpm >/dev/null 2>&1; then
  pnpm --version
elif command -v npm >/dev/null 2>&1; then
  npm --version
else
  echo "No known Node package manager (pnpm/npm) found"; exit 4
fi

echo "Environment variables (masked)"
echo "POSTGRES_HOST=${POSTGRES_HOST:+set} POSTGRES_PORT=${POSTGRES_PORT:+set} DATABASE_URL=${DATABASE_URL:+set}"

if command -v nc >/dev/null 2>&1; then
  HOST=${POSTGRES_HOST:-localhost}
  PORT=${POSTGRES_PORT:-5432}
  echo "Testing TCP connectivity to ${HOST}:${PORT} (may fail if DB closed)"
  nc -zv "$HOST" "$PORT" || echo "TCP check failed (may be expected)"
fi

echo "verify_env completed"
