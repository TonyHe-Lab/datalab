# WSL 2 Setup

This document describes steps to enable WSL2 on Windows and prepare a distro for development.

1. Enable WSL and Virtual Machine Platform (PowerShell as Admin):

```powershell
wsl --install
# Or, to ensure WSL2 and set default version
wsl --set-default-version 2
```

2. Install a Linux distro (recommended: Ubuntu LTS) from Microsoft Store, or:

```powershell
wsl --install -d Ubuntu-22.04
```

3. Update the distro and kernel if prompted. Inside WSL:

```sh
sudo apt update && sudo apt upgrade -y
uname -r  # should show a WSL-compatible kernel
```

4. Virtualization requirements

- Ensure that virtualization (VT-x/AMD-V) is enabled in BIOS/UEFI.
- On some Windows installs, install the latest WSL kernel update from Microsoft.

5. Next steps

- Follow `docs/setup/wsl-post-setup.md` for user-level tooling (Python, Node). Or use scripts in `dev/`:
  - `dev/setup_python.sh`
  - `dev/setup_node.sh`

Links:

- https://learn.microsoft.com/windows/wsl/
- https://learn.microsoft.com/windows/wsl/install
