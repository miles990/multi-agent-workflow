# Multi-Agent Workflow

[![Version](https://img.shields.io/badge/version-2.4.1-blue.svg)](https://github.com/miles990/multi-agent-workflow)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugin-purple.svg)](https://claude.ai/code)

> 多視角並行工作流生態系：RESEARCH → PLAN → TASKS → IMPLEMENT → REVIEW → VERIFY

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                      multi-agent-workflow（統一專案）                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │RESEARCH │→ │  PLAN   │→ │  TASKS  │→ │IMPLEMENT│→ │ REVIEW  │→ │ VERIFY  │ │
│  │   ✅    │  │   ✅    │  │   ✅    │  │   ✅    │  │   ✅    │  │   ✅    │ │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘ │
│       ↓            ↓            ↓            ↓            ↓            ↓      │
│  research/     plans/       tasks/       code/       reviews/    verification/│
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                     🔗 ORCHESTRATE（編排器）✅                          │  │
│  │               串聯所有階段，自動流轉，智能回退                          │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Features

- **6 階段完整工作流**：研究 → 規劃 → 任務分解 → 實作 → 審查 → 驗證
- **多視角並行處理**：每個階段 4 個視角同時工作
- **Map-Reduce 協調**：並行執行 → 交叉驗證 → 智能匯總
- **Git Worktree 隔離**：IMPLEMENT/REVIEW/VERIFY 在隔離分支中執行
- **零依賴設計**：只使用 Claude Code 內建工具
- **Memory 整合**：成果自動存檔，支持跨階段復用
- **共用模組架構**：避免重複程式碼
- **指標收集系統**：自動追蹤執行、品質、效率指標
- **報告系統**：單次報告、週報、基準線追蹤
- **即時進度顯示**：階段和視角狀態可視化
- **結構化錯誤處理**：標準化錯誤碼和排除指南

## Installation

### Via Plugin Marketplace (Recommended)

```bash
# 1. 添加 Marketplace
/plugin marketplace add miles990/multi-agent-workflow

# 2. 安裝 Plugin
/plugin install multi-agent-workflow@multi-agent-workflow

# 3. 重啟 Claude Code 載入新 Plugin
```

### Direct Install

```bash
/plugin install miles990/multi-agent-workflow
```

## Available Skills

| Skill | Command | Description | Status |
|-------|---------|-------------|--------|
| **research** | `/multi-research` | 多視角並行研究 | ✅ Ready |
| **plan** | `/multi-plan` | 多視角規劃設計 | ✅ Ready |
| **tasks** | `/multi-tasks` | 多視角任務分解（v2.2 新增） | ✅ Ready |
| **implement** | `/multi-implement` | 監督式並行實作 | ✅ Ready |
| **review** | `/multi-review` | 多視角程式碼審查 | ✅ Ready |
| **verify** | `/multi-verify` | 多視角驗證測試 | ✅ Ready |
| **orchestrate** | `/orchestrate` | 端到端編排 | ✅ Ready |
| **plugin-dev** | `/plugin-dev` | Plugin 開發工作流 | ✅ Ready |

## Quick Start

### Research

```bash
# 基本用法
/multi-research AI Agent 架構設計模式

# 快速模式（2 視角）
/multi-research --quick 技術選型問題

# 深度模式（6 視角）
/multi-research --deep 重大架構決策
```

### Plan

```bash
# 基本用法
/multi-plan 建立用戶認證系統

# 從研究報告載入
/multi-plan --from-research user-auth
```

### Tasks (v2.2 新增)

```bash
# 從計劃載入並分解任務
/multi-tasks user-auth

# 快速模式（2 視角）
/multi-tasks --quick user-auth

# 深度模式（6 視角）
/multi-tasks --deep user-auth

# 強制 TDD 順序
/multi-tasks --tdd user-auth
```

### Implement

```bash
# 從計劃載入
/multi-implement --from-plan user-auth

# 快速模式（2 視角）
/multi-implement --quick --from-plan small-feature
```

### Review

```bash
# 審查指定範圍
/multi-review src/auth/

# 審查 git diff
/multi-review --diff HEAD~3
```

### Verify

```bash
# 驗證功能
/multi-verify user-auth

# 嚴格模式
/multi-verify --strict user-auth
```

### Full Workflow

```bash
# 端到端編排（自動判斷起始點）
/orchestrate 新增用戶認證功能

# 從已有計劃開始
/orchestrate --from-plan user-auth
```

### Git Worktree Mode

```bash
# 自動使用 worktree（預設）
/orchestrate 新增用戶認證功能

# 強制使用 worktree
/orchestrate --worktree 新增功能

# 禁用 worktree（直接在 main 工作）
/orchestrate --no-worktree 快速修復

# 恢復中斷的工作流
/orchestrate --resume user-auth

# 清理孤立的 worktrees
/orchestrate --cleanup-worktrees
```

## Skill Perspectives

### research

| ID | Name | Focus |
|----|------|-------|
| `architecture` | 架構分析師 | 系統結構、設計模式、可擴展性 |
| `cognitive` | 認知科學研究員 | 方法論、思維模式、認知框架 |
| `workflow` | 工作流設計師 | 執行流程、整合策略、實作步驟 |
| `industry` | 業界實踐研究員 | 現有框架、案例研究、最佳實踐 |

### plan

| ID | Name | Focus |
|----|------|-------|
| `architect` | 系統架構師 | 技術可行性、組件設計、擴展性 |
| `risk-analyst` | 風險分析師 | 潛在風險、依賴問題、失敗場景 |
| `estimator` | 估算專家 | 工作量評估、優先順序、時程規劃 |
| `ux-advocate` | UX 倡導者 | 使用者體驗、API 設計、開發者體驗 |

### implement

| ID | Name | Focus |
|----|------|-------|
| `tdd-enforcer` | TDD 守護者 | 測試先行、覆蓋率、邊界案例 |
| `performance-optimizer` | 效能優化師 | 時間複雜度、記憶體、快取 |
| `security-auditor` | 安全審計員 | OWASP、輸入驗證、授權 |
| `maintainer` | 維護性專家 | 可讀性、文檔、重構友善 |

### review

| ID | Name | Focus |
|----|------|-------|
| `code-quality` | 程式碼品質審查員 | 風格一致性、重複程式碼、設計模式 |
| `test-coverage` | 測試覆蓋審查員 | 測試品質、邊界案例、Mock 適當性 |
| `documentation` | 文檔審查員 | API 文檔、註解、README |
| `integration` | 整合審查員 | 向後相容、API 契約、依賴影響 |

### tasks (v2.2 新增)

| ID | Name | Focus |
|----|------|-------|
| `dependency-analyst` | 依賴分析師 | 依賴關係、執行順序、並行機會 |
| `task-decomposer` | 任務分解師 | 實作任務、估算、驗收標準 |
| `test-planner` | 測試規劃師 | 測試任務、TDD 案例、邊界條件 |
| `risk-preventor` | 風險預防師 | 風險任務、回退點、監控任務 |

### verify

| ID | Name | Focus |
|----|------|-------|
| `functional-tester` | 功能測試員 | 核心功能、Happy Path、使用者流程 |
| `edge-case-hunter` | 邊界獵人 | 極端輸入、錯誤處理、容錯 |
| `regression-checker` | 回歸檢查員 | 現有功能、API 相容、向後相容 |
| `acceptance-validator` | 驗收驗證員 | 需求符合度、Definition of Done |

## Memory Structure

```
.claude/memory/
├── research/           # research skill 產出
│   └── [topic-id]/
│       ├── meta.yaml
│       ├── overview.md
│       ├── perspectives/
│       └── synthesis.md
├── plans/              # plan skill 產出
│   └── [feature-id]/
│       ├── meta.yaml
│       ├── perspectives/
│       └── implementation-plan.md
├── tasks/              # tasks skill 產出
│   └── [feature-id]/
│       ├── meta.yaml
│       ├── perspectives/
│       ├── tasks.yaml
│       └── dependency-graph.md
├── implementations/    # implement skill 產出
├── reviews/            # review skill 產出
└── verifications/      # verify skill 產出
```

## Project Structure

```
multi-agent-workflow/
├── skills/
│   ├── research/                 # ✅ Ready
│   │   ├── SKILL.md
│   │   ├── 00-quickstart/
│   │   └── 01-perspectives/
│   ├── plan/                     # ✅ Ready
│   ├── tasks/                    # ✅ Ready (v2.2 新增)
│   ├── implement/                # ✅ Ready
│   ├── review/                   # ✅ Ready
│   ├── verify/                   # ✅ Ready
│   └── orchestrate/              # ✅ Ready
├── scripts/                      # 開發工具
│   ├── create-skill.sh           # Skill 腳手架工具
│   └── validate-skills.sh        # Skill 結構驗證
├── shared/                       # 共用模組
│   ├── skill-structure/          # Skill 結構規範 (v2.3 新增)
│   │   ├── STANDARD.md           # 結構規範文件
│   │   ├── CLAUDE.md             # AI 自動載入說明
│   │   └── templates/            # 模板檔案
│   ├── coordination/
│   │   ├── map-phase.md          # 並行執行
│   │   └── reduce-phase.md       # 整合匯總
│   ├── synthesis/
│   │   ├── cross-validation.md   # 交叉驗證
│   │   └── conflict-resolution.md # 矛盾解決
│   ├── perspectives/
│   │   └── base-perspective.md   # 視角基礎結構
│   ├── isolation/                # Git Worktree 隔離
│   │   ├── worktree-setup.md     # Worktree 創建
│   │   ├── worktree-completion.md # Worktree 完成
│   │   └── path-resolution.md    # 路徑解析
│   ├── integration/
│   │   ├── evolve-checkpoints.md # CP 對應
│   │   └── memory-system.md      # Memory 寫入
│   ├── metrics/                  # 指標收集
│   │   ├── schema.yaml           # 指標定義
│   │   ├── collector.md          # 收集器
│   │   └── memory-structure.md   # Memory 結構
│   ├── reporting/                # 報告系統
│   │   ├── single-report.md      # 單次報告
│   │   ├── weekly-report.md      # 週報
│   │   └── baseline.md           # 基準線
│   ├── progress/                 # 進度顯示
│   │   └── display.md            # 進度模組
│   └── errors/                   # 錯誤處理
│       ├── error-codes.md        # 錯誤碼定義
│       └── formatter.md          # 錯誤格式化
├── docs/
│   └── troubleshooting/          # 錯誤排除指南
├── templates/                    # 共用模板
├── plugin.json                   # Plugin manifest
├── .claude-plugin/marketplace.json
├── LICENSE
└── README.md
```

## Documentation

| Module | Description | Link |
|--------|-------------|------|
| **research** | 多視角研究 | [→](./skills/research/SKILL.md) |
| **orchestrate** | 端到端編排 | [→](./skills/orchestrate/SKILL.md) |
| **Skill Structure** | Skill 結構規範 | [→](./shared/skill-structure/STANDARD.md) |
| **Map Phase** | 並行執行 | [→](./shared/coordination/map-phase.md) |
| **Reduce Phase** | 整合匯總 | [→](./shared/coordination/reduce-phase.md) |
| **Cross Validation** | 交叉驗證 | [→](./shared/synthesis/cross-validation.md) |
| **Conflict Resolution** | 矛盾解決 | [→](./shared/synthesis/conflict-resolution.md) |
| **Perspectives** | 視角配置 | [→](./shared/perspectives/base-perspective.md) |
| **Git Worktree** | Worktree 隔離 | [→](./skills/orchestrate/04-git-worktree/) |
| **Memory System** | 存儲系統 | [→](./shared/integration/memory-system.md) |
| **Checkpoints** | evolve 整合 | [→](./shared/integration/evolve-checkpoints.md) |
| **Metrics Schema** | 指標定義 | [→](./shared/metrics/schema.yaml) |
| **Metrics Collector** | 指標收集 | [→](./shared/metrics/collector.md) |
| **Single Report** | 單次報告 | [→](./shared/reporting/single-report.md) |
| **Weekly Report** | 週報/趨勢 | [→](./shared/reporting/weekly-report.md) |
| **Baseline** | 基準線機制 | [→](./shared/reporting/baseline.md) |
| **Progress Display** | 進度顯示 | [→](./shared/progress/display.md) |
| **Error Codes** | 錯誤碼定義 | [→](./shared/errors/error-codes.md) |
| **Troubleshooting** | 錯誤排除指南 | [→](./docs/troubleshooting/) |

## Development Tools

### 建立新 Skill

使用腳手架工具快速建立符合規範的 Skill 結構：

```bash
# 互動模式（引導式）
./scripts/create-skill.sh

# 非互動模式（CI/自動化）
./scripts/create-skill.sh --non-interactive \
  --name my-skill \
  --desc "Skill 描述" \
  --version 1.0.0
```

產生的結構：
```
skills/my-skill/
├── SKILL.md                    # 主要定義檔（frontmatter）
├── 00-quickstart/
│   └── _base/usage.md          # 快速開始指南
└── 01-perspectives/
    └── _base/default-perspectives.md  # 視角定義
```

### 驗證 Skill 結構

使用驗證工具確保所有 Skills 符合標準：

```bash
# 驗證所有 Skills
./scripts/validate-skills.sh

# 驗證單一 Skill
./scripts/validate-skills.sh research

# CI 模式（嚴格，有退出碼）
./scripts/validate-skills.sh --ci
```

驗證項目：
- SKILL.md 存在且 frontmatter 完整（name, description, version）
- 00-quickstart/_base/usage.md 存在
- 01-perspectives/_base/default-perspectives.md 存在

詳細規範請參考 [Skill 結構標準](./shared/skill-structure/STANDARD.md)。

### 查詢視角定義

查詢集中管理的視角定義：

```bash
# 列出所有視角
./scripts/list-perspectives.sh

# 按類別過濾
./scripts/list-perspectives.sh --category plan

# 按 skill 過濾
./scripts/list-perspectives.sh --skill implement

# 顯示視角詳細資訊
./scripts/list-perspectives.sh --show tdd-enforcer

# 顯示預設組合
./scripts/list-perspectives.sh --preset standard
```

### 查詢配置索引

查詢集中管理的配置索引：

```bash
# 列出所有配置類別
./scripts/get-config.sh --list-categories

# 列出某類別的配置
./scripts/get-config.sh --category skill-config

# 搜尋配置
./scripts/get-config.sh --search "tdd"

# 顯示配置詳情
./scripts/get-config.sh --show skills/implement/SKILL.md

# 顯示配置間的引用關係
./scripts/get-config.sh --relations
```

## For Plugin Developers

### Development Setup

```bash
# Clone repository
git clone https://github.com/miles990/multi-agent-workflow.git
cd multi-agent-workflow

# Start development mode (hot-reload)
/plugin-dev watch
# Or: ./scripts/plugin/dev-watch.sh
```

### Development Workflow (using /plugin-dev Skill)

```bash
# 1. Sync to Claude Code cache
/plugin-dev sync

# 2. Validate structure
/plugin-dev validate

# 3. Check status
/plugin-dev status

# 4. Start watch mode (auto-sync on file changes)
/plugin-dev watch
```

### Release Workflow

```bash
# 1. Dry-run to preview
/plugin-dev release patch --dry-run

# 2. Release
/plugin-dev release patch   # Bug fixes
/plugin-dev release minor   # New features
/plugin-dev release major   # Breaking changes

# 3. Resume from interruption
/plugin-dev release --resume
```

### Version Management

```bash
# Show current version
/plugin-dev version

# Bump version
/plugin-dev version bump patch

# Check consistency
/plugin-dev version check
```

### Shell Scripts (Fallback)

```bash
# Sync
./scripts/plugin/sync-to-cache.sh

# Watch
./scripts/plugin/dev-watch.sh

# Release
./scripts/plugin/publish.sh patch
```

### Testing

```bash
# Run all plugin tests
python -m pytest tests/plugin/ -v

# With coverage
python -m pytest tests/plugin/ --cov=cli/plugin
```

### Project Structure

```
skills/plugin-dev/    # /plugin-dev Skill
├── SKILL.md          # Main definition
├── 00-quickstart/    # Quick start guide
├── 01-commands/      # Command documentation
└── config/           # Command config

cli/plugin/           # Python CLI modules
├── __main__.py       # CLI entry point
├── cache.py          # CacheManager
├── version.py        # VersionManager
├── dev.py            # DevCommands
└── release.py        # ReleaseCommands

scripts/plugin/       # Shell scripts
├── sync-to-cache.sh
├── dev-watch.sh
├── validate-plugin.sh
├── bump-version.sh
├── generate-changelog.sh
└── publish.sh

shared/plugin/        # Configuration
├── config.yaml
├── cache-policy.yaml
└── version-strategy.yaml

tests/plugin/         # Tests (73 tests)
```

## Core Design Principles

| Principle | Description |
|-----------|-------------|
| **Zero Dependencies** | 只使用 Task API + 內建工具，無外部 MCP 依賴 |
| **Multi-Perspective** | Map-Reduce 模式，4 視角同時工作 |
| **Cross Validation** | 共識識別 + 矛盾解決 |
| **Git Worktree Isolation** | main 穩定，feature 在隔離分支開發 |
| **Memory Integration** | 與 evolve Checkpoint 對應 |
| **Shared Modules** | shared/ 避免重複程式碼 |
| **Unified Entry** | 單一 plugin，7 個 skill |
| **Standard Structure** | 所有 Skill 遵循統一結構規範 |

## Related Projects

- [self-evolving-agent](https://github.com/miles990/self-evolving-agent) — 自我進化 Agent 框架

## Changelog

### v2.5.0 (2026-02-01)
- **plugin-dev Skill**
  - 新增 `/plugin-dev` Skill：統一的 Plugin 開發工作流入口
  - 命令：sync, watch, validate, status, version, release
  - 統一 CLI 入口：`python -m cli.plugin <command>`
  - Skill + Python CLI 雙層架構（可測試、可 fallback）
  - Dogfooding：用 plugin-dev 開發 plugin-dev

### v2.4.0 (2026-02-01)
- **Plugin 開發工作流系統**
  - 新增 `cli/plugin/` 模組：CacheManager, VersionManager, DevCommands, ReleaseCommands
  - 新增 `scripts/plugin/` 腳本：sync-to-cache, dev-watch, validate, bump-version, changelog, publish
  - 新增 `shared/plugin/` 配置：config.yaml, cache-policy.yaml, version-strategy.yaml
  - 熱載入開發模式（fswatch/inotifywait/polling）
  - 增量同步（Hash-based）
  - 語義化版本管理
  - 自動變更日誌生成
  - 一鍵發布流程
  - 73 個測試覆蓋

### v2.3.2 (2026-02-01)
- **Git 操作統一模組**
  - 新增 `scripts/git_lib/` 模組，統一所有 Git 操作
  - 消除重複代碼（`_get_current_workflow_id()` 等 65 行重複）
  - 實作 Facade Pattern，簡化 Hook 開發
  - 55 個單元測試，覆蓋率 80%+
  - Hook 代碼減少 54%

### v2.3.0 (2026-02-01)
- **Skill 結構規範化**
  - 新增 `shared/skill-structure/STANDARD.md` 定義標準結構
  - 新增 `scripts/create-skill.sh` 腳手架工具（互動/非互動模式）
  - 新增 `scripts/validate-skills.sh` 驗證工具（含 CI 模式）
  - 統一所有 Skill 目錄結構

### v2.2.0 (2026-01-25)
- 新增 TASKS 階段（在 PLAN 和 IMPLEMENT 之間）
  - 4 視角任務分解：dependency-analyst, task-decomposer, test-planner, risk-preventor
  - tasks.yaml 結構化任務輸出
  - DAG 依賴分析和 Wave 分組
  - TDD 順序支持
- 更新 ORCHESTRATE 支持 TASKS 階段
- 工作流更新為 6 階段：RESEARCH → PLAN → TASKS → IMPLEMENT → REVIEW → VERIFY

### v2.1.0 (2026-01-24)
- 新增指標收集系統（Phase 1）
  - metrics schema 定義執行、品質、效率指標
  - metrics collector 標準化收集 API
  - 各 SKILL.md 嵌入指標收集點
- 新增報告系統（Phase 2）
  - 單次執行報告：詳細分析和改善建議
  - 週報/趨勢報告：長期追蹤和趨勢分析
  - 基準線機制：滾動平均和目標管理
- 新增進度和錯誤處理（Phase 3）
  - 即時進度顯示：階段和視角狀態可視化
  - 標準化錯誤碼：E-AGT, E-WKF, E-MEM, E-USR, E-GIT, E-ENV
  - 結構化錯誤訊息：可能原因 + 建議步驟
  - Troubleshooting 文檔：詳細錯誤排除指南

### v2.0.0 (2025-01-24)
- 重組專案為 multi-agent-workflow
- 提取共用模組到 shared/
- 更新 research skill 至 v2.0.0
- 新增 plan skill：多視角規劃設計
- 新增 implement skill：監督式並行實作（獨特設計）
- 新增 review skill：多視角程式碼審查
- 新增 verify skill：多視角驗證測試 + pass@k 機制
- 新增 orchestrate skill：端到端編排 + 智能回退

### v1.0.0 (2025-01-23)
- 初始版本：multi-agent-research-skill

## License

[MIT](./LICENSE)

## Author

**miles990** — [GitHub](https://github.com/miles990)
