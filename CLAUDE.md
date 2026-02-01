# Multi-Agent Workflow

> 多視角並行工作流生態系 v2.3.1

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
