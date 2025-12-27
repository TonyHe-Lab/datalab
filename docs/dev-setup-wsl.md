---
title: WSL 开发环境快速安装（Python & Node）
---

本指南在干净的 WSL（推荐 Ubuntu 22.04）中快速设置 Python 与 Node 开发工具链，并包含常见问题排查。

快速步骤

1. 更新系统并安装基础软件

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential curl git ca-certificates
```

2. 安装 Python（系统包或 pyenv）并创建虚拟环境

系统包（简单、可重复）:

```bash
sudo apt install -y python3 python3-venv python3-pip
python3 --version
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

可选：使用 pyenv 管理多版本 Python（见 pyenv 文档）

3. 安装 nvm 与 Node.js LTS（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.4/install.sh | bash
# 重新加载 shell（或重新打开终端）
export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm install --lts
nvm use --lts
node --version
```

4. 安装包管理器（可选）

推荐 `pnpm`：

```bash
npm install -g pnpm
pnpm --version
```

或者使用 `npm` / `yarn`：

```bash
# npm 已随 node 提供
npm --version
# 或者
npm install -g yarn
yarn --version
```

5. 前端依赖安装（若存在 `frontend/`）

```bash
cd frontend
pnpm install   # 或 npm ci
```

6. 使用验证脚本快速检查

仓库包含一个验证脚本：`dev/verify_wsl_tooling.sh`。
运行：

```bash
./dev/verify_wsl_tooling.sh
```

若脚本退出码为 0，说明基础工具存在且能创建临时虚拟环境；非零退出码表示缺少某项工具或检查失败，请根据脚本输出排查。

常见问题与排查

- python3 未安装：使用 `sudo apt install python3 python3-venv python3-pip`。
- node 未安装或版本过低：建议使用 `nvm` 安装 LTS 版本。
- 权限与网络：在公司网络或代理下，`npm/ pnpm` 可能需要配置 registry 或代理。
- Windows 层问题：如果在启用 WSL 时遇到 Hyper-V/Virtualization 错误，请参阅 Microsoft WSL 安装文档。

CI 建议

- 可将 `dev/verify_wsl_tooling.sh` 作为 GitHub Actions 的 `workflow_dispatch` job 运行，用于手动或按需验证环境。
- 在 CI 中运行时，避免在工作区内创建/删除持久文件（脚本中仅使用临时 venv）。

安全提示

- 不要将 `.env` 或凭据提交到仓库。将 `.env` 加入 `.gitignore`，并在 CI 中使用 Secrets。

更多参考

- nvm: https://github.com/nvm-sh/nvm
- pyenv: https://github.com/pyenv/pyenv
- pnpm: https://pnpm.io/
