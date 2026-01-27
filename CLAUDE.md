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

## 關鍵文檔

| 模組 | 路徑 |
|------|------|
| 編排器 | [skills/orchestrate/SKILL.md](./skills/orchestrate/SKILL.md) |
| 研究框架 | [skills/research/SKILL.md](./skills/research/SKILL.md) |
| 規劃框架 | [skills/plan/SKILL.md](./skills/plan/SKILL.md) |
| 任務分解 | [skills/tasks/SKILL.md](./skills/tasks/SKILL.md) |
| 實作框架 | [skills/implement/SKILL.md](./skills/implement/SKILL.md) |
| 審查框架 | [skills/review/SKILL.md](./skills/review/SKILL.md) |
| 驗證框架 | [skills/verify/SKILL.md](./skills/verify/SKILL.md) |
| 狀態查看 | [skills/status/SKILL.md](./skills/status/SKILL.md) |
| 並行執行 | [shared/coordination/map-phase.md](./shared/coordination/map-phase.md) |
| 整合匯總 | [shared/coordination/reduce-phase.md](./shared/coordination/reduce-phase.md) |
| 品質閘門 | [shared/quality/gates.yaml](./shared/quality/gates.yaml) |
| 執行模式 | [shared/config/execution-profiles.yaml](./shared/config/execution-profiles.yaml) |
| 上下文新鮮 | [shared/config/context-freshness.yaml](./shared/config/context-freshness.yaml) |
| Commit 設定 | [shared/config/commit-settings.yaml](./shared/config/commit-settings.yaml) |
| 錯誤碼 | [shared/errors/error-codes.md](./shared/errors/error-codes.md) |
