#!/usr/bin/env bash
set -euo pipefail

echo "Guide: install Python 3.12 on Debian/Ubuntu WSL"
echo "This script attempts to install python3.12 using deadsnakes PPA if available."

if [ -f /etc/os-release ]; then
  . /etc/os-release
fi

if command -v python3.12 >/dev/null 2>&1; then
  echo "Python 3.12 already installed: $(python3.12 --version)"
  exit 0
fi

if [ "${ID:-}" = "ubuntu" ] || [ "${ID_LIKE:-}" = "debian" ]; then
  sudo apt-get update
  sudo apt-get install -y software-properties-common
  sudo add-apt-repository -y ppa:deadsnakes/ppa
  sudo apt-get update
  sudo apt-get install -y python3.12 python3.12-venv python3.12-distutils
  echo "Install complete. Use: python3.12 -m venv .venv && . .venv/bin/activate"
else
  echo "Non-debian based distro: please install python3.12 using your distro packages or pyenv"
fi
