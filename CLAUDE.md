# Multi-Agent Workflow

> 多視角並行工作流生態系 v2.4.0

## 專案概述

Claude Code Plugin，提供 6 階段完整軟體開發工作流：

```
RESEARCH → PLAN → TASKS → IMPLEMENT → REVIEW → VERIFY
```

**核心特性**：
- 每階段 4 視角並行（Map-Reduce 模式）
- 上下文新鮮機制（Task = Fresh Context）
- Skills + Subagents 整合（context: fork）
- Claude Code Tasks 跨 session 協作
- Claude Code Hooks 自動 logging + git commit
- Git Worktree 隔離實作環境
- 品質閘門自動檢查

## 快速開始

### 斜線命令

| 命令 | 說明 | 階段 |
|------|------|------|
| `/orchestrate [需求]` | 端到端工作流 | 全部 |
| `/multi-research [主題]` | 多視角研究 | RESEARCH |
| `/multi-plan [功能]` | 多視角規劃 | PLAN |
| `/multi-tasks [plan-path]` | 任務分解（DAG） | TASKS |
| `/multi-implement [task-path]` | 監督式實作 | IMPLEMENT |
| `/multi-review [impl-path]` | 程式碼審查 | REVIEW |
| `/multi-verify [review-path]` | 驗證測試 | VERIFY |
| `/status` | 工作流狀態 | - |

### 執行模式

根據需求選擇不同執行模式：

| 模式 | 視角數 | 模型 | 適用場景 |
|------|--------|------|---------|
| `express` | 1/階段 | haiku | 快速實驗、原型開發 |
| `default` | 4/階段 | 混合 | 標準開發（預設） |
| `quality` | 4/階段 | opus | 關鍵功能、安全敏感 |

使用方式：
```bash
/orchestrate 需求 --profile express   # 快速模式
/orchestrate 需求 --profile quality   # 品質模式
/multi-research 主題 --profile express
```

配置：[shared/config/execution-profiles.yaml](./shared/config/execution-profiles.yaml)

### Claude Code 新功能整合

> 2026 年 1 月更新：Skills + Subagents 整合、Todos → Tasks 升級

#### Skills + Subagents

Skill 現在可以直接在 Subagent 中執行，保護主 Context Window：

```yaml
# SKILL.md frontmatter 新選項
---
name: research-perspective
context: fork          # 在獨立 Subagent 執行
agent: Explore         # 使用 Explore subagent
allowed-tools: Read, Grep, Glob, Write
model: sonnet
---
```

| 選項 | 說明 |
|------|------|
| `context: fork` | Skill 在獨立 Subagent 中執行 |
| `agent: Explore` | 指定 Subagent 類型（Explore/Plan/general-purpose） |
| `allowed-tools` | 限制可用工具 |
| `disable-model-invocation` | 禁止 Claude 自動觸發（僅手動） |

#### Tasks 跨 Session 協作

Tasks 系統支援多 Agent 協作同一任務清單：

```bash
# 設定共享任務清單
export CLAUDE_CODE_TASK_LIST_ID=my-workflow

# 建立有依賴關係的任務
TaskCreate({ subject: "研究階段", ... })  # → taskId: 1
TaskCreate({ subject: "規劃階段", addBlockedBy: ["1"], ... })  # 等待研究完成
```

| API | 說明 |
|-----|------|
| `TaskCreate` | 建立任務 |
| `TaskUpdate` | 更新狀態、設定依賴 |
| `TaskList` | 列出所有任務 |
| `TaskGet` | 取得任務詳情 |

**跨 session 共享**：設定相同的 `CLAUDE_CODE_TASK_LIST_ID`，多個 Claude/Subagent 可協作同一任務清單。

### 擴展思考

在複雜分析階段（RESEARCH / PLAN）建議啟用擴展思考：

| 方式 | 說明 |
|------|------|
| 關鍵字 | 在提示中加入 `ultrathink` |
| 快捷鍵 | Option+T（Mac）/ Alt+T（Windows/Linux） |
| 環境變數 | `export MAX_THINKING_TOKENS=10000` |

觸發配置：[shared/config/thinking-triggers.yaml](./shared/config/thinking-triggers.yaml)

### @ 檔案參考

使用 `@` 符號動態載入模組指南：

```bash
# 載入協調模組指南
@shared/coordination

# 載入品質閘門配置
@shared/quality

# 載入特定視角配置
@shared/perspectives
```

每個 shared 子目錄都有 `CLAUDE.md` 自動說明使用方式。

## 常用命令

### 端到端編排
```bash
/orchestrate [需求描述]         # 完整工作流
/orchestrate --start-from PLAN  # 從指定階段開始
```

### 單一階段
```bash
/multi-research [主題]          # 研究（4 視角）
/multi-plan [功能]              # 規劃（4 視角）
/multi-tasks [plan-path]        # 任務分解（DAG）
/multi-implement [task-path]    # 監督式實作
/multi-review [impl-path]       # 程式碼審查
/multi-verify [review-path]     # 驗證測試
```

### 狀態與進度
```bash
/status                         # 當前工作流狀態
/status --list                  # 歷史工作流
/status --dag                   # 任務依賴圖（Mermaid）
```

## 視角配置

### RESEARCH 視角
| ID | 名稱 | 模型 | 聚焦 |
|----|------|------|------|
| architecture | 架構分析師 | sonnet | 系統結構、設計模式 |
| cognitive | 認知研究員 | sonnet | 方法論、思維框架 |
| workflow | 工作流設計 | haiku | 執行流程、整合策略 |
| industry | 業界實踐 | haiku | 現有框架、最佳實踐 |

### PLAN 視角
| ID | 名稱 | 模型 | 聚焦 |
|----|------|------|------|
| architect | 系統架構師 | sonnet | 技術可行性、組件設計 |
| risk-analyst | 風險分析師 | sonnet | 潛在風險、失敗場景 |
| estimator | 估算專家 | haiku | 工作量評估、時程規劃 |
| ux-advocate | UX 倡導者 | haiku | 使用者體驗、API 設計 |

### TASKS 視角
| ID | 名稱 | 模型 | 聚焦 |
|----|------|------|------|
| dependency-analyst | 依賴分析師 | sonnet | 任務依賴、執行順序 |
| task-decomposer | 任務分解師 | haiku | 粒度切分、並行識別 |
| test-planner | 測試規劃師 | haiku | TDD 對應、測試策略 |
| risk-preventor | 風險預防師 | haiku | 風險任務、預防措施 |

### IMPLEMENT 角色
| ID | 名稱 | 模型 | 聚焦 |
|----|------|------|------|
| main_agent | 主實作者 | sonnet | 功能實作 |
| tdd-enforcer | TDD 守護者 | haiku | 測試先行檢查 |
| security-auditor | 安全審計員 | sonnet | 安全漏洞檢測 |
| maintainer | 可維護性審查 | haiku | 程式碼品質 |

### REVIEW 視角
| ID | 名稱 | 模型 | 聚焦 |
|----|------|------|------|
| code-quality | 程式碼品質 | haiku | 命名、結構、可讀性 |
| test-coverage | 測試覆蓋 | haiku | 覆蓋率、測試品質 |
| documentation | 文檔檢查 | haiku | 註解、README、API 文檔 |
| integration | 整合分析 | sonnet | 整合問題、依賴衝突 |

### VERIFY 視角
| ID | 名稱 | 模型 | 聚焦 |
|----|------|------|------|
| functional-tester | 功能測試員 | haiku | 正常流程、功能驗證 |
| edge-case-hunter | 邊界獵人 | sonnet | 邊界條件、異常處理 |
| regression-checker | 回歸檢查員 | haiku | 回歸測試、副作用 |
| acceptance-validator | 驗收驗證員 | sonnet | 驗收標準、需求滿足 |

## Memory 結構

```
.claude/memory/
├── research/{topic-id}/        # 研究報告
│   ├── perspectives/*.md       # 視角報告
│   ├── summaries/*.yaml        # 結構化摘要
│   └── synthesis.md            # 匯總
├── plans/{feature-id}/         # 實作計劃
│   ├── perspectives/*.md       # 視角報告
│   └── implementation-plan.md  # 主輸出
├── tasks/{plan-id}/            # 任務清單
│   ├── perspectives/*.md       # 視角分析
│   └── tasks.yaml              # DAG 定義
├── implement/{tasks-id}/       # 實作記錄
│   ├── perspectives/*.md       # 角色報告
│   └── summary.md              # 實作摘要
├── review/{impl-id}/           # 審查報告
│   ├── perspectives/*.md       # 視角報告
│   └── review-summary.md       # 審查摘要
└── verify/{review-id}/         # 驗證結果
    ├── perspectives/*.md       # 視角報告
    └── verify-summary.md       # 驗證摘要
```

## 開發規範

### 視角報告強制寫入
每個 Agent 完成前**必須**執行：
```bash
Write → .claude/memory/{stage}/{id}/perspectives/{perspective_id}.md
```

### Hooks 自動處理
- **PreToolUse**: 工具調用前驗證
- **PostToolUse**:
  - Write: 記錄到 `actions.jsonl`
  - **Task: 自動 git commit 程式碼（可設定是否包含 memory/logs）**
- **SubagentStart**: Agent 啟動追蹤
- **SubagentStop**: Agent 完成 + memory 目錄 git commit

### Git Worktree 隔離
IMPLEMENT/REVIEW/VERIFY 階段在 `.worktrees/{feature-id}/` 執行。

## 品質閘門

| 階段 | 通過分數 | 關鍵條件 |
|------|---------|---------|
| RESEARCH | ≥ 70 | 至少 2 視角共識、無關鍵矛盾 |
| PLAN | ≥ 75 | 組件設計完整、風險評估完成、里程碑定義 |
| TASKS | ≥ 80 | DAG 驗證通過、TDD 對應完整、任務有估算 |
| IMPLEMENT | ≥ 80 | 測試通過、無 BLOCKER |
| REVIEW | ≥ 75 | 無 BLOCKER、HIGH ≤ 2 |
| VERIFY | ≥ 85 | 功能+回歸測試 100% 通過、驗收標準滿足 |

## 開發工具

### Skill 腳手架

快速建立符合規範的 Skill 結構：

```bash
# 互動模式
./scripts/create-skill.sh

# 非互動模式（CI/自動化）
./scripts/create-skill.sh --non-interactive \
  --name my-skill \
  --desc "Skill 描述" \
  --version 1.0.0
```

### 結構驗證

確保所有 Skills 符合標準結構：

```bash
./scripts/validate-skills.sh          # 驗證所有
./scripts/validate-skills.sh research # 驗證單一
./scripts/validate-skills.sh --ci     # CI 模式
```

### 視角查詢

查詢集中管理的 33 個視角定義：

```bash
./scripts/list-perspectives.sh                    # 列出全部
./scripts/list-perspectives.sh --category plan    # 按類別
./scripts/list-perspectives.sh --skill implement  # 按 Skill
./scripts/list-perspectives.sh --show tdd-enforcer # 詳情
./scripts/list-perspectives.sh --preset standard  # 預設組合
```

### 配置查詢

查詢集中管理的 37 個配置索引：

```bash
./scripts/get-config.sh --list-categories         # 列出類別
./scripts/get-config.sh --category skill-config   # 按類別
./scripts/get-config.sh --search "tdd"            # 搜尋
./scripts/get-config.sh --show skills/implement/SKILL.md # 詳情
./scripts/get-config.sh --relations               # 引用關係
```

## 開發經驗與技巧

### 1. Skill 結構規範化

**問題**：各 Skill 結構不一致，難以維護和擴展。

**解決方案**：
- 定義標準結構（`shared/skill-structure/STANDARD.md`）
- 腳手架工具自動生成符合規範的結構
- 驗證工具確保一致性

**必要結構**：
```
skills/{skill-name}/
├── SKILL.md                              # 必須：frontmatter (name, description, version)
├── 00-quickstart/_base/usage.md          # 必須：快速開始
└── 01-perspectives/_base/default-perspectives.md  # 必須：視角定義
```

**最佳實踐**：
- 新建 Skill 時使用 `create-skill.sh`
- 提交前執行 `validate-skills.sh --ci`
- 輕量級工具型 Skill 也需要基本結構（可簡化內容）

### 2. 視角系統集中化

**問題**：33 個視角分散在各 Skill 目錄，存在重複定義和不一致。

**解決方案**：
- 集中管理於 `shared/perspectives/catalog.yaml`
- 各 Skill 改為引用模式
- 提供查詢工具快速查找

**catalog.yaml 結構**：
```yaml
metadata:
  severity_levels: [critical, high, medium, low]
  model_tiers: [opus, sonnet, haiku]

categories:
  - id: research
    description: 研究分析視角
    applicable_skills: [research]

perspectives:
  - id: architecture
    name: 架構分析師
    category: research
    focus: 系統結構、設計模式
    model_tier: sonnet
    priority_weight: 0.9

presets:
  quick: { perspectives: 2 }
  standard: { perspectives: 4 }
  deep: { perspectives: 6 }
```

**引用模式**（在 `default-perspectives.md`）：
```yaml
perspectives:
  source: shared/perspectives/catalog.yaml
  filter:
    category: implement
  preset: standard
```

### 3. 配置系統優化

**問題**：37 個配置檔案分散，難以找到和理解關係。

**解決方案**：
- 建立配置索引 `shared/config/INDEX.yaml`
- 分類管理（skill/perspective/quality/coordination/...）
- 記錄配置間的引用關係

**配置分類**：
| 類別 | 數量 | 說明 |
|------|------|------|
| skill-config | 10 | Skill 定義 |
| perspective-config | 5 | 視角配置 |
| quality-config | 6 | 品質閘門 |
| coordination-config | 8 | 並行協調 |
| integration-config | 3 | 外部整合 |
| expertise-config | 4 | 專業框架 |

### 4. 並行 Agent 開發技巧

**任務獨立性判斷**：
- 無共享狀態 → 可並行
- 有依賴關係 → 順序執行
- DAG 分析確定執行順序

**背景任務管理**：
```bash
# 啟動背景任務
Task(run_in_background: true)

# 檢查狀態
TaskOutput(task_id, block: false)

# 等待完成
TaskOutput(task_id, block: true)
```

**最佳實踐**：
- 獨立任務盡量並行啟動
- 長時間任務使用背景模式
- 定期檢查背景任務狀態

### 5. DRY 原則實踐

**識別重複**：
- 多個 Skill 有相似的視角定義 → 集中到 catalog.yaml
- 多個地方有相同的配置邏輯 → 提取到 shared/
- 重複的腳本邏輯 → 抽取成工具函數

**抽象層級**：
```
具體實現 (skills/)
    ↓ 引用
共用模組 (shared/)
    ↓ 使用
基礎工具 (scripts/)
```

### 6. SOLID 原則應用

| 原則 | 應用 |
|------|------|
| **S**ingle Responsibility | 每個 Skill 只負責一個階段 |
| **O**pen/Closed | 通過 presets 擴展，不修改核心邏輯 |
| **L**iskov Substitution | 視角可互換，遵循相同介面 |
| **I**nterface Segregation | 小而專注的配置檔案 |
| **D**ependency Inversion | Skills 依賴 shared/ 抽象，不依賴具體實現 |

### 7. 文檔即代碼

**每個目錄都有 CLAUDE.md**：
- 自動載入說明
- 使用範例
- 配置參考

**文檔更新時機**：
- 新功能完成後立即更新
- 結構變更後更新 README.md
- 經驗總結後更新 CLAUDE.md

### 8. 錯誤處理模式

**腳本錯誤處理**：
```bash
set -euo pipefail  # 嚴格模式

# 檢查前置條件
[ -f "$file" ] || { echo "Error: $file not found"; exit 1; }

# 正確的退出碼
exit 0  # 成功
exit 1  # 失敗
```

**Agent 錯誤處理**：
- 明確的錯誤訊息
- 建議的修復步驟
- 適當的退出狀態

### 9. Git 操作統一模組（v2.3.2）

**問題**：Git 操作分散在多個 Hook 檔案，存在大量重複代碼：
- `_get_current_workflow_id()` 重複 5 次（65 行）
- Co-Author 字串重複 16+ 次
- Commit message 格式不一致
- 直接呼叫 subprocess，缺乏抽象層

**解決方案**：建立 `scripts/git_lib/` 統一模組

**模組結構**：
```
scripts/git_lib/
├── __init__.py           # 公開 API
├── exceptions.py         # 自訂例外
├── executor.py           # GitExecutor - 底層命令執行
├── operations.py         # GitOps - 基本 Git 操作
├── context.py            # WorkflowContext - 狀態管理
├── config.py             # ConfigManager - 設定管理
├── commit.py             # CommitManager - Commit 業務邏輯
└── facade.py             # WorkflowCommitFacade - 簡化入口
```

**使用方式**：
```python
# 簡單使用（Hooks 推薦）
from git_lib import WorkflowCommitFacade

facade = WorkflowCommitFacade(project_dir)
facade.auto_commit_after_task("add feature", success=True)
facade.auto_commit_memory("research", "api-design")

# 進階使用
from git_lib import GitOps, CommitManager, WorkflowContext

git = GitOps(project_dir)
if git.has_changes():
    git.stage(["."])
    git.commit("feat(api): add endpoint")
```

**設計模式**：
- **Facade Pattern**：`WorkflowCommitFacade` 提供簡化入口
- **Repository Pattern**：`GitOps` 封裝 Git 操作
- **Strategy Pattern**：`ConfigManager` 支援可配置的 commit type

**Git Pathspec 注意事項**：
- 使用 `:(exclude)` 而非 `:!` 排除路徑
- `:!` 後面跟 `_` 開頭的路徑會解析錯誤（如 `__pycache__/`）
- 正確寫法：`:(exclude)__pycache__/`

**效益**：
| 指標 | 改善 |
|------|------|
| Hook 代碼行數 | -54%（546 → 250 行）|
| 重複代碼 | -95% |
| 測試覆蓋率 | 0% → 80%+（55 tests） |
| 新 hook 開發時間 | -70% |

### 10. Plugin 開發注意事項

**源碼 vs Cache 位置**：
```
源碼倉庫：/Users/user/Workspace/multi-agent-workflow
Cache：   ~/.claude/plugins/cache/multi-agent-workflow/...
```

- Claude Code 載入 plugin 時會複製到 cache
- **修改 cache 不會影響源碼**，記得同步回源碼倉庫
- 開發完成後執行 `git status` 確認變更在源碼倉庫

**sys.path 設定**：
```python
# Hook 檔案需要正確設定 import 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))  # git_lib 目錄
sys.path.insert(0, str(Path(__file__).parent))         # 同層模組
```

### 11. subprocess 與 Git 互動技巧

**stdout/stderr 處理**：
```python
result = subprocess.run(cmd, capture_output=True, text=True)
# result.stdout 可能是 None，需要防禦性處理
stdout = result.stdout if result.stdout else ""
```

**Pathspec Magic 字元限制**：
```python
# ❌ 錯誤：:! 後面跟 _ 開頭會被誤解析
pathspecs = [":!__pycache__/"]  # Git 報錯：未實現的神奇前綴 '_'

# ✅ 正確：使用 :(exclude) 完整語法
pathspecs = [":(exclude)__pycache__/"]
```

**git add 不支援排除語法**：
```python
# ❌ git add 無法直接使用排除
git add -- . ':!.claude/memory/'  # 會失敗

# ✅ 解決方案：先 add 再 reset
git add -- .
git reset HEAD -- .claude/memory/
```

### 12. 測試驅動重構

**pytest fixtures 活用**：
```python
@pytest.fixture
def git_repo(tmp_path):
    """建立臨時 git repo"""
    repo = tmp_path / "test_repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, ...)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, ...)
    return repo

@pytest.fixture
def workflow_project(git_repo):
    """建立帶 workflow 結構的專案"""
    # 建立 .claude/workflow/ 結構
    # 建立 .claude/memory/ 結構
    return git_repo
```

**分層測試策略**：
1. **單元測試**：測試單一類別（GitExecutor, GitOps）
2. **整合測試**：測試多個類別協作（WorkflowCommitFacade）
3. **端到端測試**：模擬完整工作流程

**測試隔離**：
- 使用 `tmp_path` fixture 確保每個測試有獨立目錄
- 每個測試初始化獨立的 git repo
- 避免測試間的狀態污染

### 13. 多視角研究價值

**研究階段發現的問題**：

| 視角 | 發現 |
|------|------|
| 架構 | DRY 違反嚴重（5 處重複）、缺乏抽象層 |
| 工作流 | Hook 雙軌制混亂（templates/ vs scripts/hooks/）|
| 業界實踐 | 推薦 subprocess + 抽象層（零依賴）|
| 認知科學 | OCP 3/10、DIP 2/10（最差）|

**4 視角一致認同**：
- 需要統一的 `_get_current_workflow_id()` 實作
- 需要 Git 操作抽象層
- Commit message 格式應統一

**視角特有洞察**：
- 架構視角：建議 `scripts/git_lib/` 目錄結構
- 認知視角：建議 Facade Pattern 降低認知負擔 87%
- 業界視角：建議 subprocess + 抽象層（不引入 GitPython）

### 15. Plugin 開發工作流設計（v2.4）

**問題**：開發 Plugin 時需要手動複製到 Claude Code cache，效率低下。

**解決方案**：建立完整的開發工作流系統

**目錄結構**：
```
cli/plugin/           # Python CLI 模組
├── cache.py          # CacheManager - 快取管理
├── version.py        # VersionManager - 版本控制
├── dev.py            # DevCommands - 開發工作流
└── release.py        # ReleaseCommands - 發布流程

scripts/plugin/       # Shell 腳本
├── sync-to-cache.sh  # 同步到快取
├── dev-watch.sh      # 熱載入監控
├── validate-plugin.sh # Plugin 驗證
├── bump-version.sh   # 版本升級
├── generate-changelog.sh # 變更日誌
└── publish.sh        # 發布流程

shared/plugin/        # 配置
├── config.yaml       # 主配置
├── cache-policy.yaml # 快取策略
└── version-strategy.yaml # 版本策略
```

**設計模式**：
- **Facade Pattern**：`ReleaseCommands` 封裝複雜發布流程
- **Strategy Pattern**：同步模式（incremental/full/timestamp）
- **Template Method**：發布步驟可覆寫

**增量同步**：
```python
# Hash-based 增量同步
def sync():
    source_manifest = get_file_manifest(source)
    cache_manifest = load_cache_map()
    added, modified, deleted = compare(source_manifest, cache_manifest)
    # 只同步變更的檔案
```

**測試覆蓋**：73 個測試，覆蓋：
- CacheManager（15 tests）
- VersionManager（26 tests）
- DevCommands（15 tests）
- ReleaseCommands（17 tests）

### 16. 語義化版本最佳實踐

**版本組件**：
- `MAJOR`：破壞性變更（API 改變、Skill 移除）
- `MINOR`：新功能（新 Skill、新命令）
- `PATCH`：Bug 修復、文檔更新

**自動偵測破壞性變更**：
- Git commit 包含 "BREAKING CHANGE:"
- plugin.json 必要欄位變更
- Skill 參數變更

**變更日誌分類**：
- ⚠️ BREAKING CHANGES
- ✨ Features
- 🐛 Bug Fixes
- 📚 Documentation
- ♻️ Refactoring

### 17. 跨平台檔案監控策略

**問題**：不同平台有不同的檔案監控工具，需要優雅降級。

**解決方案**：按優先順序嘗試多種工具
```bash
# 優先順序：fswatch (macOS) → inotifywait (Linux) → polling (通用)
if command -v fswatch &> /dev/null; then
    watch_with_fswatch
elif command -v inotifywait &> /dev/null; then
    watch_with_inotifywait
else
    watch_with_polling  # 通用備選
fi
```

**fswatch 防抖動**：
```bash
fswatch --latency 0.5 ...  # 500ms 防抖動
```

**inotifywait 持續監控**：
```bash
inotifywait -r -m -e modify,create,delete --exclude '...' "$dir"
```

**Polling 備選**：
```bash
while true; do
    current_hash=$(find ... | xargs md5sum | md5sum)
    if [[ "$current_hash" != "$last_hash" ]]; then
        sync_on_change
    fi
    sleep 2
done
```

### 18. 增量同步與 Hash 比對

**問題**：每次全量同步效率低下，尤其大型專案。

**解決方案**：Hash-based 增量同步
```python
def sync(self, force: bool = False):
    # 1. 載入上次同步的快取映射
    cache_map = self._load_cache_map() if not force else {}

    # 2. 遍歷來源檔案，計算 hash
    for rel_path in files_to_sync:
        file_hash = self.compute_hash(src_file)
        cached_entry = cache_map.get(str(rel_path))

        if not cached_entry:
            added.append(str(rel_path))  # 新增
        elif cached_entry.get("hash") != file_hash:
            modified.append(str(rel_path))  # 修改
        # else: 無變更，跳過

    # 3. 找出已刪除的檔案
    for cached_path in cache_map.keys():
        if cached_path not in source_files:
            deleted.append(cached_path)
```

**快取映射結構**（`.plugin-dev/cache-map.json`）：
```json
{
  "skills/research/SKILL.md": {
    "hash": "a1b2c3...",
    "size": 12345,
    "mtime": 1706789012.34
  }
}
```

**效益**：
- 大型專案同步時間從 ~2s 降至 < 100ms
- 減少不必要的檔案 I/O
- 準確追蹤變更

### 19. 發布流程狀態機設計

**問題**：發布流程多步驟，任一步驟失敗需要能恢復。

**解決方案**：狀態機 + 進度持久化
```python
class ReleaseStep(Enum):
    VALIDATE = "validate"
    TEST = "test"
    CHECK_GIT = "check_git"
    BUMP_VERSION = "bump_version"
    GENERATE_CHANGELOG = "generate_changelog"
    GIT_COMMIT = "git_commit"
    GIT_TAG = "git_tag"
    GIT_PUSH = "git_push"
    COMPLETE = "complete"

@dataclass
class ReleaseProgress:
    current_step: ReleaseStep
    completed_steps: list[ReleaseStep]
    failed_step: Optional[ReleaseStep] = None
    error: Optional[str] = None
```

**失敗時自動保存進度**：
```python
try:
    # 執行步驟...
except Exception as e:
    progress.failed_step = progress.current_step
    progress.error = str(e)
    self._save_progress(progress)  # 持久化到檔案
    raise
```

**恢復執行**：
```bash
./scripts/plugin/publish.sh --resume
```

### 20. JSON 嵌套結構版本讀取

**問題**：`marketplace.json` 的版本在嵌套結構中，直接 `.get("version")` 會失敗。

**錯誤方式**：
```python
# ❌ 錯誤：假設 version 在頂層
data = json.load(f)
version = data.get("version", "unknown")  # 永遠返回 "unknown"
```

**正確方式**：
```python
# ✅ 正確：處理嵌套結構
if "plugins" in data and data["plugins"]:
    version = data["plugins"][0].get("version", "unknown")
else:
    version = data.get("version", "unknown")
```

**`marketplace.json` 結構**：
```json
{
  "name": "multi-agent-workflow",
  "plugins": [
    {
      "name": "multi-agent-workflow",
      "version": "2.4.0"  // ← 版本在這裡
    }
  ]
}
```

### 21. Git 遠端檢測與優雅降級

**問題**：測試環境或新倉庫可能沒有設定遠端，直接 push 會報錯。

**解決方案**：先檢測再執行
```python
def _git_push(self, tag: str) -> None:
    # 先檢查遠端是否存在
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=self.project_dir,
        capture_output=True,
    )
    if result.returncode != 0:
        # 無遠端，優雅跳過
        return

    # 有遠端，執行 push
    subprocess.run(["git", "push", "origin", "HEAD"], ...)
    subprocess.run(["git", "push", "origin", tag], ...)
```

**優雅錯誤訊息**：
```python
# 不是直接報錯，而是提示用戶手動處理
if no_remote:
    log_warning("No remote 'origin' configured")
    log_info("Run manually: git push origin HEAD --tags")
```

### 22. Dataclass 活用與類型安全

**問題**：複雜結果物件難以維護，欄位容易遺漏。

**解決方案**：使用 `@dataclass` 強制類型
```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class SyncResult:
    success: bool
    source: Path
    destination: Path
    files_added: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    files_deleted: list[str] = field(default_factory=list)
    duration_ms: int = 0
    error: Optional[str] = None

    @property
    def total_changes(self) -> int:
        """計算屬性，自動更新"""
        return len(self.files_added) + len(self.files_modified) + len(self.files_deleted)

    def to_dict(self) -> dict:
        """序列化方法"""
        return { ... }
```

**優點**：
- 類型提示 + IDE 自動完成
- 預設值處理（`field(default_factory=list)`）
- 計算屬性（`@property`）
- 自動生成 `__init__`、`__repr__`

### 23. Shell 腳本跨平台技巧

**嚴格模式**：
```bash
set -euo pipefail  # 錯誤即停、未定義變數報錯、管道錯誤傳播
```

**顏色輸出跨平台**：
```bash
# 使用 ANSI escape codes
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}✓${NC} Success"
```

**Python 解析 JSON（避免依賴 jq）**：
```bash
# 使用內建 python3 解析，避免額外依賴
VERSION=$(python3 -c "import json; print(json.load(open('plugin.json'))['version'])")
```

**條件檢測工具**：
```bash
if command -v rsync &> /dev/null; then
    sync_with_rsync
else
    sync_with_cp  # 備選
fi
```

**安全的字串比較**：
```bash
# 使用 [[ ]] 而非 [ ]，更安全
if [[ "$var" == "value" ]]; then
    ...
fi
```

### 24. 測試 Fixture 設計模式

**分層 Fixture**：
```python
@pytest.fixture
def temp_project(tmp_path):
    """基礎：建立專案目錄結構"""
    project_dir = tmp_path / "test-plugin"
    project_dir.mkdir()
    # 建立 plugin.json, skills/ 等
    return project_dir

@pytest.fixture
def temp_cache(tmp_path):
    """基礎：建立快取目錄"""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir

@pytest.fixture
def cache_manager(temp_project, temp_cache):
    """組合：建立 CacheManager 實例"""
    return CacheManager(
        project_dir=temp_project,
        cache_base=temp_cache,
    )

@pytest.fixture
def dev_commands(temp_project, temp_cache):
    """組合：建立 DevCommands 實例"""
    cache_manager = CacheManager(...)
    return DevCommands(
        project_dir=temp_project,
        cache_manager=cache_manager,
    )
```

**Git Fixture 完整初始化**：
```python
@pytest.fixture
def temp_project_with_git(tmp_path):
    project_dir = tmp_path / "test-plugin"
    project_dir.mkdir()

    # Git 初始化（必須設定 user 才能 commit）
    subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=project_dir, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=project_dir, capture_output=True
    )

    # 建立初始 commit（某些操作需要 HEAD 存在）
    (project_dir / ".gitkeep").touch()
    subprocess.run(["git", "add", "-A"], cwd=project_dir, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=project_dir, capture_output=True
    )

    return project_dir
```

### 14. 重構安全策略

**分階段重構**：
```
Phase 1: 建立新模組（不修改現有代碼）
Phase 2: 撰寫測試確保行為正確
Phase 3: 逐步替換舊實作
Phase 4: 移除舊代碼
```

**向後相容**：
- 新模組應能獨立運作
- 舊 Hook 可逐步遷移
- 保留原有 API 語義

**驗證檢查點**：
- 每個 Phase 完成後執行完整測試
- 比較重構前後的行為
- 監控 Hook 執行日誌

## Plugin 開發工作流（v2.4 新增）

### 快速開始

```bash
# 啟動開發模式（熱載入）
./scripts/plugin/dev-watch.sh

# 手動同步到快取
./scripts/plugin/sync-to-cache.sh

# 驗證 Plugin 結構
./scripts/plugin/validate-plugin.sh
```

### 版本管理

```bash
# 查看當前版本
./scripts/plugin/bump-version.sh --dry-run

# 升級版本
./scripts/plugin/bump-version.sh patch   # Bug 修復
./scripts/plugin/bump-version.sh minor   # 新功能
./scripts/plugin/bump-version.sh major   # 破壞性變更

# 生成變更日誌
./scripts/plugin/generate-changelog.sh
```

### 發布流程

```bash
# 模擬發布（不實際變更）
./scripts/plugin/publish.sh --dry-run

# 正式發布
./scripts/plugin/publish.sh patch
```

**發布流程**：
1. 驗證 Plugin 結構
2. 執行測試
3. 檢查 Git 狀態
4. 升級版本
5. 生成變更日誌
6. Git commit + tag
7. 推送到遠端

### 核心模組

| 模組 | 路徑 | 用途 |
|------|------|------|
| CacheManager | `cli/plugin/cache.py` | 快取管理 |
| VersionManager | `cli/plugin/version.py` | 版本控制 |
| DevCommands | `cli/plugin/dev.py` | 開發工作流 |
| ReleaseCommands | `cli/plugin/release.py` | 發布流程 |

### 配置檔案

| 檔案 | 用途 |
|------|------|
| `shared/plugin/config.yaml` | 主配置 |
| `shared/plugin/cache-policy.yaml` | 快取策略 |
| `shared/plugin/version-strategy.yaml` | 版本策略 |
| `.plugin-dev/watch.config.json` | 監控配置 |

### 測試

```bash
# 執行 Plugin 測試
python -m pytest tests/plugin/ -v

# 測試覆蓋率
python -m pytest tests/plugin/ --cov=cli/plugin
```

## 關鍵文檔

| 模組 | 路徑 |
|------|------|
| **Skills** | |
| 編排器 | [skills/orchestrate/SKILL.md](./skills/orchestrate/SKILL.md) |
| 研究框架 | [skills/research/SKILL.md](./skills/research/SKILL.md) |
| 規劃框架 | [skills/plan/SKILL.md](./skills/plan/SKILL.md) |
| 任務分解 | [skills/tasks/SKILL.md](./skills/tasks/SKILL.md) |
| 實作框架 | [skills/implement/SKILL.md](./skills/implement/SKILL.md) |
| 審查框架 | [skills/review/SKILL.md](./skills/review/SKILL.md) |
| 驗證框架 | [skills/verify/SKILL.md](./skills/verify/SKILL.md) |
| 狀態查看 | [skills/status/SKILL.md](./skills/status/SKILL.md) |
| **協調模組** | |
| 並行執行 | [shared/coordination/map-phase.md](./shared/coordination/map-phase.md) |
| 整合匯總 | [shared/coordination/reduce-phase.md](./shared/coordination/reduce-phase.md) |
| **品質與配置** | |
| 品質閘門 | [shared/quality/gates.yaml](./shared/quality/gates.yaml) |
| 執行模式 | [shared/config/execution-profiles.yaml](./shared/config/execution-profiles.yaml) |
| 上下文新鮮 | [shared/config/context-freshness.yaml](./shared/config/context-freshness.yaml) |
| Commit 設定 | [shared/config/commit-settings.yaml](./shared/config/commit-settings.yaml) |
| 錯誤碼 | [shared/errors/error-codes.md](./shared/errors/error-codes.md) |
| **開發規範（v2.3 新增）** | |
| Skill 結構標準 | [shared/skill-structure/STANDARD.md](./shared/skill-structure/STANDARD.md) |
| 視角目錄 | [shared/perspectives/catalog.yaml](./shared/perspectives/catalog.yaml) |
| 視角系統說明 | [shared/perspectives/CLAUDE.md](./shared/perspectives/CLAUDE.md) |
| 配置索引 | [shared/config/INDEX.yaml](./shared/config/INDEX.yaml) |
| 配置系統說明 | [shared/config/CLAUDE.md](./shared/config/CLAUDE.md) |
