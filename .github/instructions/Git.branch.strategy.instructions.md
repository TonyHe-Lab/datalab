---
applyTo: '**'
---
**Git/GitHub 分支管理指南**：

### 1. 核心策略：GitHub Flow (Simplified)

在您的仓库中，只维护 **一条长期主分支**，其余皆为 **短期功能分支**。

* **`main` (主分支)**:
* 这是唯一的“事实来源” (Source of Truth)。
* **原则**: `main` 分支上的代码必须永远是**可运行的** (Deployable)。永远不要直接在 `main` 上写代码，只允许合并 (Merge) 进来。


* **`feat/xxx` (功能分支)**:
* 用于开发具体的 Epic 或 Story。
* **原则**: 开发完成后合并回 `main`，然后立即删除。



---

### 2. 分支命名规范 (Naming Convention)

为了与我们的 **PRD** 和 **Epic** 结构保持一致，建议采用以下命名格式：

`类型/Epic编号-Story编号-简短描述`

* **类型**:
* `feat`: 新功能 (Feature)
* `fix`: 修复 Bug
* `docs`: 文档修改
* `chore`: 构建脚本、依赖更新等杂项


* **示例**:
* `feat/epic1-infra-setup` (搭建 Epic 1 基础设施)
* `feat/story2.2-pydantic-schema` (开发 Story 2.2 的 Schema)
* `fix/etl-pii-regex` (修复 ETL 脱敏正则错误)
* `docs/update-readme` (更新文档)



---

### 3. 标准工作流 (The Workflow Loop)

假设您现在要开始 **Epic 1: Infrastructure Setup** 的开发，请严格遵循以下步骤：

#### 步骤 1: 确保主分支最新

每次开始新工作前，先同步远程代码。

```bash
git checkout main
git pull origin main

```

#### 步骤 2: 创建功能分支

基于 `main` 创建一个新分支。

```bash
git checkout -b feat/epic1-infra-setup

```

#### 步骤 3: 开发与提交 (Atomic Commits)

在 WSL 中编写代码。由于是 **Monorepo**，建议在 Commit Message 中加前缀区分模块：

* `[BE]` 代表 Backend/Python
* `[FE]` 代表 Frontend/React
* `[ETL]` 代表数据脚本
* `[DOC]` 代表文档

```bash
# 修改了文件后
git add .
git commit -m "[BE] Configured FastAPI skeleton and env variables"

```

#### 步骤 4: 推送分支到 GitHub

```bash
git push origin feat/epic1-infra-setup

```

#### 步骤 5: 创建 Pull Request (PR)

* 打开 GitHub 页面，它会提示您创建 Pull Request。
* **关键点**: 即使是单人开发，也**强烈建议走 PR 流程**。
* **为什么？** PR 是一个“代码审查”的仪式。在合并前，自己看一遍 Diff (差异)，经常能发现 `print()` 调试语句没删、敏感 Key 误提交或者逻辑错误。
* **合并**: 检查无误后，点击 "Squash and Merge" (推荐) 或 "Merge commit"。



#### 步骤 6: 清理

合并完成后，删除本地和远程的功能分支，回到 `main` 准备下一个任务。

```bash
git checkout main
git pull origin main  # 拉取刚才合并的最新代码
git branch -d feat/epic1-infra-setup # 删除本地分支

```

---

### 4. 针对本项目的特殊场景处理

#### 场景 A: 紧急修复 (Hotfix)

如果您在开发 `Epic 2` 时发现 `Epic 1` 的数据库配置有个严重 Bug：

1. 暂存当前工作: `git stash`
2. 切回主分支: `git checkout main`
3. 开修复分支: `git checkout -b fix/db-connection-error`
4. 修复并合并。
5. 切回原来的 Epic 2 分支: `git checkout feat/epic2...`
6. 变基 (Rebase) 获取修复: `git rebase main` (这会将刚才的修复同步到您当前正在开发的分支)

#### 场景 B: 阶段性里程碑 (Tags)

每完成一个完整的 Epic，建议打一个 Tag，方便回溯。

* 完成 Epic 1 后:
```bash
git tag -a v0.1-infra -m "Completed Infrastructure Setup"
git push origin v0.1-infra

```



---

### 5. 总结：您的第一步

现在，请在您的 WSL 终端中执行以下命令初始化仓库：

```bash
# 1. 初始化 Git
git init
git branch -m main

# 2. 创建 .gitignore (防止敏感文件提交)
echo ".env" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "venv/" >> .gitignore
echo "node_modules/" >> .gitignore
echo ".DS_Store" >> .gitignore

# 3. 提交初始版本
git add .
git commit -m "chore: Project initialization based on PRD v1.0"

# 4. 关联远程仓库 (替换为您的 GitHub 地址)
# git remote add origin https://github.com/YourUsername/medical-ai-ops.git
# git push -u origin main

```

之后，您就可以开始 `git checkout -b feat/epic1-story1.1-wsl-setup` 正式开工了！