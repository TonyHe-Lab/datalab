#!/usr/bin/env bash
set -euo pipefail

echo "Install Node.js LTS (20.x) and pnpm on Debian/Ubuntu WSL"

if command -v node >/dev/null 2>&1; then
  echo "Node already installed: $(node --version)"
fi

curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs build-essential

if ! command -v pnpm >/dev/null 2>&1; then
  corepack enable
  corepack prepare pnpm@latest --activate
fi

echo "Node: $(node --version)"
echo "pnpm: $(pnpm --version)"
