# Git Workflow Best Practices: Industry Perspective

*研究日期: 2026-02-01*

## Executive Summary

本研究從業界實踐角度分析 Git 工作流模式、工具選擇、自動化策略，特別針對 AI Agent 工作流場景提供最佳實踐建議。

## 1. Git 工作流模式比較

### 1.1 三大主流模式

| 模式 | 分支策略 | 發布頻率 | 適用場景 | 2026 趨勢 |
|------|---------|---------|---------|----------|
| **Git Flow** | 多長期分支 (main/develop/feature/release/hotfix) | 定期發布 | 大型企業、排程發布 | 逐漸式微 |
| **GitHub Flow** | 單主分支 + 功能分支 | 持續部署 | 小團隊、單版本產品 | 穩定流行 |
| **Trunk-Based** | 單主幹 + 短期分支 | 每日多次 | DevOps、CI/CD 驅動 | **主流趨勢** |

### 1.2 各模式特點

#### Git Flow
- **優點**: 結構化、階段明確、適合多版本管理
- **缺點**: 複雜、分支壽命長、合併衝突多
- **業界評價**: "雖然仍有價值，但逐漸被 Trunk-Based 取代" 

#### GitHub Flow
- **優點**: 簡單、主分支隨時可部署、PR 審查流程
- **缺點**: 不適合多版本支援
- **業界評價**: "小團隊和初創公司的首選"

#### Trunk-Based Development (推薦)
- **優點**: 
  - CI/CD 必備實踐
  - 小而頻繁的更新
  - 主幹隨時可部署
  - 減少合併衝突
- **缺點**: 需要成熟的測試和 CI/CD
- **業界評價**: "現代 DevOps 的標準做法"

### 1.3 AI Agent 場景推薦

**推薦: Trunk-Based Development 變體**

理由:
1. **頻繁整合**: AI Agent 產生的變更應快速整合，避免長期分支
2. **自動化友好**: Trunk-Based 與 CI/CD 完美契合
3. **簡化衝突**: 短期分支大幅降低衝突機率
4. **快速反饋**: 每次提交觸發自動測試和部署

實施策略:
```
main (protected, always deployable)
  ├── feature/agent-task-123 (short-lived, 1-2 days max)
  ├── feature/agent-task-124 (short-lived, 1-2 days max)
  └── hotfix/agent-error-fix (very short-lived, hours)
```

## 2. Git Worktree 最佳實踐

### 2.1 核心概念

Git Worktree 允許從同一倉庫同時檢出多個分支到不同目錄，共享 `.git` 數據。

### 2.2 業界最佳實踐

#### 原則 1: 視為臨時工作區
> "Treat worktrees as temporary—create them for a specific task, then remove them when done."

**Anti-pattern**: 專案累積 15+ 被遺忘的 worktrees，消耗數 GB 空間

#### 原則 2: 有意義的目錄結構
```bash
# Good
~/project/.worktrees/
  ├── feature-user-auth/
  ├── hotfix-security-patch/
  └── review-pr-123/

# Bad
~/project/.worktrees/
  ├── temp1/
  ├── test/
  └── asdf/
```

#### 原則 3: 定期清理
```bash
# 列出所有 worktrees
git worktree list

# 清理孤立的 worktrees
git worktree prune

# 移除特定 worktree
git worktree remove <path>
```

#### 原則 4: 保持同步
> "All worktrees share the same repository history, ensure that you regularly fetch and merge changes to keep your branches up to date."

### 2.3 大型專案使用模式

#### 場景 1: 緊急修復
```bash
# 當前在 feature 分支工作，突然需要修 hotfix
git worktree add ../hotfix-urgent main
cd ../hotfix-urgent
# 修復、測試、提交
cd -
git worktree remove ../hotfix-urgent
```

#### 場景 2: 程式碼審查
```bash
# 不打斷當前工作，建立 worktree 審查 PR
git worktree add ../review-pr-456 pr-456
cd ../review-pr-456
npm install  # 每個 worktree 需要獨立設置環境
# 審查、測試、評論
```

#### 場景 3: 並行 AI 開發 (關鍵用例!)
> "Teams report completing work in hours that previously took days. For example, incident.io runs 4–5 Claude Code agents in parallel using this pattern."

**Multi-Agent Worktree 模式**:
```bash
# 主控端
~/project/

# Agent worktrees
~/project/.agents/
  ├── agent-1-frontend/    (運行 Agent 1)
  ├── agent-2-backend/     (運行 Agent 2)
  ├── agent-3-tests/       (運行 Agent 3)
  └── agent-4-docs/        (運行 Agent 4)
```

**優勢**:
- ✅ 4-5 個 Agent 並行工作
- ✅ 共享 Git 歷史，即時同步
- ✅ 獨立工作目錄，無衝突
- ✅ 完成後快速清理

### 2.4 重要限制

⚠️ **同一分支不能在兩個 worktrees 中檢出**
```bash
# 會失敗
git worktree add ../wt1 feature-branch
git worktree add ../wt2 feature-branch  # Error!
```

原因: 防止產生衝突的提交

### 2.5 自動化 Worktree 管理

**推薦腳本模式**:
```bash
#!/bin/bash
# worktree-manager.sh

create_agent_worktree() {
    local agent_id=$1
    local branch=$2
    local worktree_dir=".agents/agent-${agent_id}"
    
    git worktree add "$worktree_dir" -b "agent-${agent_id}/${branch}" main
    cd "$worktree_dir"
    npm install  # 或其他環境設置
    cd -
    echo "$worktree_dir"
}

cleanup_agent_worktree() {
    local worktree_dir=$1
    git worktree remove "$worktree_dir"
    git branch -D "$(basename $worktree_dir)"
}
```

## 3. Python Git 工具庫評估

### 3.1 三大主流庫比較

| 特性 | GitPython | pygit2 | dulwich |
|------|-----------|--------|---------|
| **實現** | Git CLI 包裝器 | libgit2 C 綁定 | 純 Python |
| **效能** | 慢 | **最快** | 中等 |
| **安裝** | 簡單 | 需編譯 C 擴展 | **最簡單** |
| **API 風格** | Pythonic | 低階 (需懂 Git 內部) | Pythonic |
| **Windows** | ⚠️ 檔案未關閉問題 | ✅ 良好 | ✅ 良好 |
| **文檔** | ✅ 完善 | ⚠️ 一般 | ⚠️ 較少 |
| **維護** | ✅ 活躍 | ✅ 活躍 | ⚠️ 較慢 |

### 3.2 效能測試 (社群反饋)

> "In most cases pygit2 is faster than GitPython, but for very large files the git show/git cat-file equivalent is slower."

> "In one developer's experience, dulwich (python implementation of git) was faster than GitPython but still slow, while pygit2 (libgit2 c bindings in python) was fastest."

效能排序: **pygit2 > dulwich > GitPython**

### 3.3 業界選擇建議

#### 場景 1: 快速原型、簡單操作 → **GitPython**
```python
from git import Repo

repo = Repo('/path/to/repo')
repo.index.add(['file.txt'])
repo.index.commit('Add file')
repo.remotes.origin.push()
```

**優點**: 
- API 簡單直觀
- 文檔完善，易學習
- 適合大多數常見操作

**缺點**:
- 效能較差
- Windows 問題

#### 場景 2: 高效能、進階操作 → **pygit2** (推薦!)
```python
import pygit2

repo = pygit2.Repository('/path/to/repo')
index = repo.index
index.add('file.txt')
tree = index.write_tree()
author = pygit2.Signature('Agent', 'agent@example.com')
repo.create_commit('HEAD', author, author, 'Add file', tree, [repo.head.target])
```

**優點**:
- 最佳效能 (C 綁定)
- 進階功能 (blob streaming, libgit2 特性)
- 跨平台穩定

**缺點**:
- 學習曲線陡峭
- 需要理解 Git 內部結構

#### 場景 3: 純 Python 環境、無法編譯 → **dulwich**
```python
from dulwich import porcelain

porcelain.add(repo='/path/to/repo', paths=['file.txt'])
porcelain.commit(repo='/path/to/repo', message='Add file')
porcelain.push(repo='/path/to/repo', remote_location='origin')
```

**優點**:
- 無需編譯，純 Python
- 部署簡單
- 適合受限環境

**缺點**:
- 效能不如 pygit2
- 文檔較少
- 社群較小

### 3.4 AI Agent 場景推薦

**推薦: pygit2 (主) + GitPython (fallback)**

理由:
1. **高效能**: Agent 可能頻繁操作 Git，pygit2 效能優勢明顯
2. **穩定性**: libgit2 成熟穩定，適合自動化場景
3. **降級策略**: 若 pygit2 安裝失敗，自動降級到 GitPython

實施策略:
```python
try:
    import pygit2 as git_backend
    BACKEND = 'pygit2'
except ImportError:
    import git as git_backend  # GitPython
    BACKEND = 'gitpython'

# 統一抽象層
class GitOperations:
    def __init__(self, repo_path):
        if BACKEND == 'pygit2':
            self.repo = pygit2.Repository(repo_path)
        else:
            self.repo = git_backend.Repo(repo_path)
    
    def commit(self, message, files):
        if BACKEND == 'pygit2':
            # pygit2 實現
            pass
        else:
            # GitPython 實現
            pass
```

## 4. Pre-commit Hook 框架

### 4.1 業界標準: pre-commit Framework

官方網站: https://pre-commit.com/

> "A framework for managing and maintaining multi-language pre-commit hooks."

### 4.2 2026 最佳實踐

#### 原則 1: 選擇最佳工具，避免重複
> "The approach prioritizes best-in-class tools without redundancy, selecting the most effective option for each task rather than using multiple overlapping tools."

**示例**:
- ✅ Python linting: **只用 Ruff**
- ❌ 不要: flake8 + pylint + pycodestyle

#### 原則 2: 五大類別 Hooks
1. **Guard Rails**: 防止錯誤 (trailing-whitespace, check-yaml, no-commit-to-branch)
2. **Formatters**: 格式化 (black, prettier)
3. **Code Checkers**: 靜態檢查 (ruff, mypy)
4. **Code Correctors**: 自動修復 (autopep8, isort)
5. **Git Helpers**: Git 輔助 (check-added-large-files, check-merge-conflict)

#### 原則 3: 注重效能
> "It's crucial to consider the performance impact of checks performed by pre-commit hooks, as long-running checks can significantly impede team productivity."

**優化策略**:
- 只檢查變更的檔案 (`files: "^src/"`)
- 使用快速工具 (Ruff 比 flake8 快 10-100 倍)
- 平行執行 hooks

### 4.3 AI Agent 工作流配置範例

`.pre-commit-config.yaml`:
```yaml
# 專為 AI Agent 工作流設計
repos:
  # 1. Guard Rails - 防止基本錯誤
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']  # Agent 不應提交大檔案
      - id: no-commit-to-branch
        args: ['--branch', 'main']  # 保護 main 分支

  # 2. Security - 防止洩密
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
        name: Detect secrets
        description: Detect hardcoded secrets

  # 3. Python - 程式碼品質
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  # 4. Type Checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]

  # 5. Commit Message - AI Agent 提交訊息規範
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.0.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        args: [--force-scope]  # 強制 Agent 提供 scope

# CI 跳過配置
ci:
  autofix_commit_msg: |
    [pre-commit.ci] auto fixes from pre-commit.com hooks
    
    [skip ci]  # 避免無限循環
  autofix_prs: true
  autoupdate_commit_msg: '[pre-commit.ci] pre-commit autoupdate'
```

### 4.4 跨語言 Hook 管理

**Husky vs pre-commit**:

| 特性 | Husky (Node.js) | pre-commit (Python) |
|------|----------------|-------------------|
| 生態 | JavaScript | **多語言** |
| 配置 | package.json | .pre-commit-config.yaml |
| 管理 | npm scripts | pre-commit CLI |
| 適用 | 前端專案 | **任何專案** |

**推薦**: 
- 純前端專案 → Husky
- Python 專案或多語言 → **pre-commit** (更通用)

### 4.5 CI/CD 整合

**GitHub Actions 範例**:
```yaml
name: Pre-commit Checks

on: [push, pull_request]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - uses: pre-commit/action@v3.0.0
        with:
          extra_args: --all-files  # CI 檢查所有檔案
```

## 5. 自動化 Commit/Push 最佳實踐

### 5.1 核心原則

#### 原則 1: 頻繁提交
> "Push code to the repository frequently to decrease the complexity of merges and increase collaborative potential."

**推薦頻率**:
- 開發: 每完成一個小功能即提交 (1-2 小時)
- AI Agent: 每完成一個任務即提交 (可能幾分鐘)

#### 原則 2: 避免無限循環
> "You have to be cautious that your pipeline doesn't create an infinite build loop, since the tool will commit and push changes to itself."

**解決方案**:
```bash
# 方案 1: 提交訊息標記
git commit -m "Auto-fix by agent [skip ci]"

# 方案 2: 檢查 commit author
if [[ "$GIT_AUTHOR_NAME" == "github-actions[bot]" ]]; then
  exit 0
fi

# 方案 3: 使用特定分支
git push origin HEAD:auto-commits  # CI 不監聽此分支
```

#### 原則 3: 原子化提交
每個提交應該:
- ✅ 單一功能或修復
- ✅ 可獨立回滾
- ✅ 包含相關測試
- ❌ 不混合多個不相關變更

### 5.2 Conventional Commits 規範

業界標準格式:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**類型 (type)**:
- `feat`: 新功能
- `fix`: 修復
- `docs`: 文檔
- `style`: 格式 (不影響程式碼運行)
- `refactor`: 重構
- `perf`: 效能優化
- `test`: 測試
- `chore`: 維護

**AI Agent 範例**:
```
feat(auth): implement user login endpoint

- Add JWT token generation
- Add password hashing with bcrypt
- Add input validation

Co-authored-by: AI Agent <agent@example.com>
```

### 5.3 自動化提交工作流

**GitHub Actions 範例**:
```yaml
name: Auto-commit Changes

on:
  workflow_dispatch:  # 手動觸發
  schedule:
    - cron: '0 */6 * * *'  # 每 6 小時

jobs:
  auto-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Run agent tasks
        run: |
          # Agent 工作...
          python agent.py --task update-docs
      
      - name: Check for changes
        id: verify-diff
        run: |
          git diff --quiet . || echo "changed=true" >> $GITHUB_OUTPUT
      
      - name: Commit changes
        if: steps.verify-diff.outputs.changed == 'true'
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add .
          git commit -m "chore: auto-update by agent [skip ci]"
          git push
```

### 5.4 錯誤處理策略

```bash
#!/bin/bash
# robust-commit.sh

set -e  # 遇錯退出

# 1. 確保工作目錄乾淨 (或有預期變更)
if ! git diff-index --quiet HEAD --; then
    echo "Working directory has changes"
else
    echo "No changes to commit"
    exit 0
fi

# 2. 拉取最新變更，避免衝突
git pull --rebase origin main || {
    echo "Rebase failed, manual intervention required"
    exit 1
}

# 3. 運行測試
npm test || {
    echo "Tests failed, aborting commit"
    exit 1
}

# 4. 提交
git add .
git commit -m "$1" || {
    echo "Commit failed"
    exit 1
}

# 5. 推送，帶重試機制
for i in {1..3}; do
    git push && break || {
        echo "Push failed, attempt $i/3"
        sleep 2
    }
done
```

### 5.5 CI/CD 整合最佳實踐

#### 關鍵策略:

**1. Workflow 觸發事件**
```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  workflow_dispatch:  # 手動觸發
  schedule:
    - cron: '0 0 * * *'  # 定時觸發
```

**2. 並發控制**
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true  # 取消進行中的舊任務
```

**3. 測試策略**
- Unit tests: 每次提交
- Integration tests: 每次 PR
- E2E tests: 每次合併到 main

**4. 部署策略**
- Development: 自動部署 (每次 push)
- Staging: 自動部署 (PR 合併)
- Production: 手動批准 + 自動部署

## 6. 衝突解決與錯誤恢復

### 6.1 自動化衝突解決策略

#### 策略 1: Git Rerere (推薦)
> "Tools like 'git rerere' (reuse recorded resolution) assist in remembering how you've resolved conflicts in the past, making future resolutions easier."

**啟用**:
```bash
git config --global rerere.enabled true
git config --global rerere.autoupdate true
```

**運作原理**:
1. 首次解決衝突後，Git 記錄解決方式
2. 未來遇到相同衝突，自動套用解決方案
3. 特別適合 rebase 重複衝突

#### 策略 2: 合併策略選項
```bash
# 優先使用「我們的」版本
git merge -X ours branch-name

# 優先使用「他們的」版本
git merge -X theirs branch-name

# 遞迴策略 + 更激進的衝突標記
git merge -X patience branch-name
```

#### 策略 3: 自訂衝突解決腳本
```python
# auto-resolve-conflicts.py
import pygit2

def auto_resolve_simple_conflicts(repo_path):
    """自動解決簡單衝突 (如空白字元、格式化差異)"""
    repo = pygit2.Repository(repo_path)
    index = repo.index
    
    conflicts = list(index.conflicts)
    
    for ancestor, ours, theirs in conflicts:
        if is_simple_conflict(ours, theirs):
            # 自動選擇一方或合併
            resolved = merge_simple_conflict(ours, theirs)
            index.add(resolved)
    
    return len(conflicts) - len(list(index.conflicts))  # 已解決數量
```

#### 策略 4: CI/CD 整合
```yaml
# .github/workflows/auto-resolve.yml
- name: Auto-resolve conflicts
  run: |
    git config merge.ours.driver true  # 「我們的」優先策略
    git merge feature-branch || {
      python scripts/auto-resolve.py
      if [ $? -eq 0 ]; then
        git add .
        git commit -m "chore: auto-resolve conflicts"
      else
        exit 1  # 需人工介入
      fi
    }
```

### 6.2 衝突預防最佳實踐

> "The modern approach emphasizes prevention through short-lived branches, frequent merging, and automation rather than simply managing reactive conflict resolution."

#### 預防原則:

**1. 短期分支** (最重要!)
- ✅ 分支壽命 < 2 天
- ✅ 每日合併 main 到功能分支
- ❌ 避免長期功能分支

**2. 頻繁同步**
```bash
# 每日早上
git checkout feature-branch
git pull origin main --rebase

# 提交前
git fetch origin
git rebase origin/main
```

**3. 標準化程式碼格式**
> "Standardizing code formatting across your team."

使用自動格式化工具:
- Python: Black, Ruff
- JavaScript: Prettier
- 所有人使用相同配置，避免格式衝突

**4. 模組化設計**
- 不同 Agent 操作不同模組
- 減少同時修改相同檔案

### 6.3 回滾策略

#### Git Revert vs Reset

| 操作 | Git Revert | Git Reset |
|------|-----------|----------|
| **作用** | 建立新提交反轉變更 | 移動 HEAD，刪除提交 |
| **歷史** | 保留所有歷史 | **修改歷史** |
| **安全性** | ✅ 安全 (公開分支) | ⚠️ 危險 (私有分支) |
| **可追溯** | ✅ 可追溯 | ❌ 歷史消失 |

#### 最佳實踐:

**公開/共享分支 → Git Revert** (推薦)
```bash
# 回滾單一提交
git revert abc123

# 回滾多個提交
git revert abc123..def456

# 回滾但不立即提交 (允許修改)
git revert -n abc123
```

**私有分支 → Git Reset**
```bash
# 軟重置 (保留變更在工作區)
git reset --soft HEAD~1

# 混合重置 (保留變更，取消 staging)
git reset --mixed HEAD~1

# 硬重置 (丟棄所有變更) ⚠️ 危險!
git reset --hard HEAD~1
```

### 6.4 GitOps 自動化回滾

> "GitOps rollbacks simplify disaster recovery by automating the process of reverting to a stable system state when issues arise, using Git as the single source of truth."

**架構**:
```
Git Repo (Source of Truth)
    ↓
ArgoCD / FluxCD (GitOps Controller)
    ↓
Kubernetes Cluster
    ↓
Monitoring (Prometheus, Grafana)
    ↓ (偵測到問題)
Automatic Rollback
```

**優勢**:
- ✅ 全自動故障轉移
- ✅ Git 歷史完整追溯
- ✅ 聲明式配置
- ✅ 無需手動 kubectl / 修補

**實施範例**:
```yaml
# ArgoCD Application with auto-rollback
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
spec:
  syncPolicy:
    automated:
      prune: true
      selfHeal: true  # 自動修復差異
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  # 健康檢查
  healthCheck:
    enabled: true
```

### 6.5 災難恢復 SOP

**情境 1: 錯誤提交到 main**
```bash
# 1. 立即回滾
git revert HEAD
git push origin main

# 2. 通知團隊
echo "Reverted bad commit abc123, please pull latest main"

# 3. 調查原因
git log -p abc123
```

**情境 2: 衝突無法自動解決**
```bash
# 1. 中止合併
git merge --abort

# 2. 建立臨時分支備份
git branch backup-$(date +%Y%m%d-%H%M%S)

# 3. 人工解決衝突
git merge feature-branch
# ... 手動編輯衝突檔案 ...
git add .
git commit

# 4. 記錄解決方案 (供 rerere 學習)
# rerere 已自動記錄
```

**情境 3: 強制推送導致歷史消失**
```bash
# 1. 從 reflog 恢復
git reflog  # 找到消失的提交
git reset --hard abc123

# 2. 恢復遠端分支
git push --force-with-lease origin branch-name

# 3. 建立保護規則，防止未來強推
# GitHub: Settings → Branches → Branch protection rules
# ✅ Require pull request reviews
# ✅ Do not allow bypassing the above settings
```

## 7. AI Agent 工作流整合建議

### 7.1 推薦技術棧

```yaml
工作流模式: Trunk-Based Development
分支策略: main + 短期功能分支 (< 2 天)
並行開發: Git Worktree (每個 Agent 一個 worktree)
Python 庫: pygit2 (主) + GitPython (fallback)
Hook 框架: pre-commit
自動化: GitHub Actions
衝突策略: Git rerere + 短期分支預防
回滾策略: Git revert (公開) + GitOps 自動回滾
```

### 7.2 工作流範例

**Agent 任務執行流程**:
```
1. 建立 worktree
   git worktree add .agents/agent-123 -b agent-123/feature main

2. Agent 在 worktree 中工作
   cd .agents/agent-123
   # AI 執行任務...

3. Pre-commit hooks 自動檢查
   git add .
   git commit -m "feat(module): implement feature X"
   # hooks 自動執行: lint, format, test, security scan

4. 推送到遠端
   git push -u origin agent-123/feature

5. 建立 PR
   gh pr create --title "Feature X" --body "..."

6. CI/CD 自動測試
   # GitHub Actions 自動執行完整測試套件

7. 自動或人工合併
   gh pr merge --squash

8. 清理 worktree
   cd ../..
   git worktree remove .agents/agent-123
   git branch -d agent-123/feature
```

### 7.3 關鍵配置範例

**`.pre-commit-config.yaml`** (見第 4.3 節)

**`pyproject.toml`**:
```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "B", "C4", "S"]
ignore = ["E501"]  # Line too long (由 formatter 處理)

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
```

**`.github/workflows/ci.yml`**:
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run pre-commit
        uses: pre-commit/action@v3.0.0
      - name: Run tests
        run: pytest --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### 7.4 監控與告警

**關鍵指標**:
- 分支平均壽命 (目標: < 2 天)
- 衝突解決時間 (目標: < 1 小時)
- CI/CD 成功率 (目標: > 95%)
- Worktree 清理率 (目標: 100% 任務完成後清理)

**告警規則**:
```yaml
# Grafana Alert
- name: Long-lived branches
  condition: branch_age_days > 3
  action: notify_team

- name: Frequent conflicts
  condition: conflicts_per_day > 5
  action: review_workflow

- name: CI failures
  condition: ci_success_rate < 90%
  action: pause_auto_merge
```

## 8. 總結與建議

### 8.1 核心建議

| 層面 | 建議 | 優先級 |
|------|------|--------|
| **工作流** | Trunk-Based Development | 🔴 高 |
| **並行** | Git Worktree (每 Agent 一個) | 🔴 高 |
| **工具庫** | pygit2 (主) + GitPython (fallback) | 🟡 中 |
| **Hooks** | pre-commit framework | 🔴 高 |
| **自動化** | GitHub Actions | 🔴 高 |
| **衝突** | 短期分支 + Git rerere | 🔴 高 |
| **回滾** | Git revert + GitOps | 🟡 中 |

### 8.2 實施路線圖

**Phase 1: 基礎架構 (第 1 週)**
- [ ] 設置 Trunk-Based 分支策略
- [ ] 配置 pre-commit hooks
- [ ] 建立 GitHub Actions CI/CD

**Phase 2: 工具整合 (第 2 週)**
- [ ] 實作 pygit2 抽象層
- [ ] 建立 Worktree 管理腳本
- [ ] 啟用 Git rerere

**Phase 3: 自動化優化 (第 3-4 週)**
- [ ] 自動化衝突解決 (簡單情況)
- [ ] GitOps 回滾機制
- [ ] 監控與告警系統

**Phase 4: 持續改進**
- [ ] 分析衝突模式，優化 Agent 協作
- [ ] 效能調優 (hook 執行時間、CI 速度)
- [ ] 團隊培訓與文檔完善

### 8.3 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|---------|
| Worktree 忘記清理 | 磁碟空間、混淆 | 定期掃描腳本 + 告警 |
| pygit2 安裝失敗 | 功能不可用 | GitPython fallback |
| 自動提交循環 | CI 資源耗盡 | [skip ci] 標記 + author 檢查 |
| 衝突無法自動解決 | 工作流中斷 | 人工介入 SOP + 通知機制 |

### 8.4 成功指標

**定量指標**:
- 部署頻率: 從每週 1 次 → 每日多次
- 變更前置時間: 從數天 → 數小時
- 平均修復時間: 從數小時 → 分鐘級
- 變更失敗率: < 5%

**定性指標**:
- Agent 可獨立完成 Git 操作
- 衝突解決自動化率 > 80%
- 開發者滿意度提升
- 程式碼品質穩定

## 參考資料

### Git 工作流
- [Trunk-Based Development Vs Git Flow: A Comparison | Assembla](https://get.assembla.com/blog/trunk-based-development-vs-git-flow/)
- [Trunk-based Development | Atlassian](https://www.atlassian.com/continuous-delivery/continuous-integration/trunk-based-development)
- [Trunk-Based Development vs Gitflow: Which Branching Model Actually Works? — Mergify](https://mergify.com/blog/trunk-based-development-vs-gitflow-which-branching-model-actually-works)
- [Github Flow vs. Git Flow: What's the Difference?](https://www.harness.io/blog/github-flow-vs-git-flow-whats-the-difference)
- [Git Workflows: Git Flow vs GitHub Flow vs Trunk-Based Dev | Medium](https://medium.com/@amareswer/git-workflows-git-flow-vs-github-flow-vs-trunk-based-dev-a998823cf47c)

### Git Worktree
- [Git Worktree Tutorial: Work on Multiple Branches Without Switching | DataCamp](https://www.datacamp.com/tutorial/git-worktree-tutorial)
- [Git - git-worktree Documentation](https://git-scm.com/docs/git-worktree)
- [Mastering Git Worktree: A Developer's Guide | Medium](https://mskadu.medium.com/mastering-git-worktree-a-developers-guide-to-multiple-working-directories-c30f834f79a5)
- [Working on two git branches at once with git worktree](https://andrewlock.net/working-on-two-git-branches-at-once-with-git-worktree/)
- [Multitasking with Cursor: Using Git Worktree for Parallel Branch Development | Medium](https://revs.runtime-revolution.com/multitasking-with-cursor-using-git-worktree-for-parallel-branch-development-7505499a1bfc)

### Python Git 工具庫
- [dvc: consider switching from GitPython · Issue #2215](https://github.com/iterative/dvc/issues/2215)
- [gitpython vs pygit2 vs dulwich](https://piptrends.com/compare/gitpython-vs-pygit2-vs-pygit2-vs-dulwich-vs-gitdb)
- [Git Implementations and Bindings in Python](https://www.legendu.net/misc/blog/git-implementations-and-bindings-in-python/)
- [Consider switching away from GitPython · Issue #66](https://github.com/godaddy/tartufo/issues/66)
- [Pygit2 Overview, Examples, Pros and Cons in 2025](https://best-of-web.builder.io/library/libgit2/pygit2)

### Pre-commit Hooks
- [pre-commit](https://pre-commit.com/)
- [GitHub - pre-commit/pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks)
- [The Power of Pre-Commit for Python Developers | DEV](https://dev.to/techishdeep/maximize-your-python-efficiency-with-pre-commit-a-complete-but-concise-guide-39a5)
- [Effortless Code Quality: The Ultimate Pre-Commit Hooks Guide for 2025](https://gatlenculp.medium.com/effortless-code-quality-the-ultimate-pre-commit-hooks-guide-for-2025-57ca501d9835)
- [pre-commit framework - Python for Data Science](https://python4data.science/en/latest/productive/git/advanced/hooks/pre-commit.html)

### CI/CD 自動化
- [A Beginner's Guide to Git Workflow and CI/CD with GitHub Actions | Medium](https://medium.com/@bhumikadasari0/a-beginners-guide-to-git-workflow-and-implementing-ci-cd-with-github-actions-040b4e03635e)
- [Improving The CI/CD Flow For Your Application | Smashing Magazine](https://www.smashingmagazine.com/2022/03/improving-ci-cd-flow-application/)
- [Building a CI/CD Workflow with GitHub Actions](https://resources.github.com/learn/pathways/automation/essentials/building-a-workflow-with-github-actions/)
- [CI/CD best practices](https://graphite.dev/guides/in-depth-guide-ci-cd-best-practices)
- [How to Automate CI/CD with GitHub Actions](https://www.freecodecamp.org/news/automate-cicd-with-github-actions-streamline-workflow/)

### 衝突解決與回滾
- [Conflict resolution | Git Tutorial](https://coderefinery.github.io/git-intro/conflicts/)
- [Fix Git Conflicts and Commit: 2026 Best Practices](https://copyprogramming.com/howto/git-conflict-rename-rename)
- [How to Resolve Merge Conflicts in Git | Atlassian](https://www.atlassian.com/git/tutorials/using-branches/merge-conflicts)
- [Resolving Git Conflicts – Strategies and Best Practices](https://www.usefulfunctions.co.uk/2025/10/23/resolving-git-conflicts-key-strategies/)
- [Conflict Resolution Automation | Chuck's Academy](https://www.chucksacademy.com/en/topic/git-conflicts/conflict-resolution-automation)
- [Automated Failover & Git Rollback with GitOps](https://www.aviator.co/blog/automated-failover-and-git-rollback-strategies-with-gitops-and-argo-rollouts/)
- [How to roll back Git code to a previous commit | TechTarget](https://www.techtarget.com/searchitoperations/answer/How-to-roll-back-Git-code-to-a-previous-commit)
- [GitOps Rollbacks: Automating Disaster Recovery](https://hokstadconsulting.com/blog/gitops-rollbacks-automating-disaster-recovery)
- [How to Revert a Commit in Git | Atlassian](https://www.atlassian.com/git/tutorials/undoing-changes/git-revert)

### AI Agent 工作流
- [How to build reliable AI workflows | GitHub Blog](https://github.blog/ai-and-ml/github-copilot/how-to-build-reliable-ai-workflows-with-agentic-primitives-and-context-engineering/)
- [agentic-workflows · GitHub Topics](https://github.com/topics/agentic-workflows)
- [GitHub Next | Agentic Workflows](https://githubnext.com/projects/agentic-workflows/)
- [Introducing Agent HQ | GitHub Blog](https://github.blog/news-insights/company-news/welcome-home-agents/)
- [The Rise of Agentic Workflows in Enterprise AI](https://www.qodo.ai/blog/agentic-workflows-in-ai-development/)

---

*研究完成日期: 2026-02-01*
*建議定期更新: 每季度檢視業界最新實踐*
