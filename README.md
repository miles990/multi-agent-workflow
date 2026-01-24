# Multi-Agent Workflow

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/miles990/multi-agent-workflow)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugin-purple.svg)](https://claude.ai/code)

> 多視角並行工作流生態系：RESEARCH → PLAN → IMPLEMENT → REVIEW → VERIFY

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     multi-agent-workflow（統一專案）                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ RESEARCH │ → │  PLAN    │ → │IMPLEMENT │ → │  REVIEW  │ → │  VERIFY  │  │
│  │   ✅     │    │   ✅     │    │   ✅     │    │   ✅     │    │   ✅     │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       ↓               ↓               ↓               ↓               ↓       │
│   research/       plans/          code/          reviews/       verification/ │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    🔗 ORCHESTRATE（編排器）✅                        ││
│  │              串聯所有階段，自動流轉，智能回退                        ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

## Features

- **5 階段完整工作流**：研究 → 規劃 → 實作 → 審查 → 驗證
- **多視角並行處理**：每個階段 4 個視角同時工作
- **Map-Reduce 協調**：並行執行 → 交叉驗證 → 智能匯總
- **零依賴設計**：只使用 Claude Code 內建工具
- **Memory 整合**：成果自動存檔，支持跨階段復用
- **共用模組架構**：避免重複程式碼

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
| **implement** | `/multi-implement` | 監督式並行實作 | ✅ Ready |
| **review** | `/multi-review` | 多視角程式碼審查 | ✅ Ready |
| **verify** | `/multi-verify` | 多視角驗證測試 | ✅ Ready |
| **orchestrate** | `/multi-orchestrate` | 端到端編排 | ✅ Ready |

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
/multi-orchestrate 新增用戶認證功能

# 從已有計劃開始
/multi-orchestrate --from-plan user-auth
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
│   ├── implement/                # ✅ Ready
│   ├── review/                   # ✅ Ready
│   ├── verify/                   # ✅ Ready
│   └── orchestrate/              # ✅ Ready
├── shared/                       # 共用模組
│   ├── coordination/
│   │   ├── map-phase.md          # 並行執行
│   │   └── reduce-phase.md       # 整合匯總
│   ├── synthesis/
│   │   ├── cross-validation.md   # 交叉驗證
│   │   └── conflict-resolution.md # 矛盾解決
│   ├── perspectives/
│   │   └── base-perspective.md   # 視角基礎結構
│   └── integration/
│       ├── evolve-checkpoints.md # CP 對應
│       └── memory-system.md      # Memory 寫入
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
| **Map Phase** | 並行執行 | [→](./shared/coordination/map-phase.md) |
| **Reduce Phase** | 整合匯總 | [→](./shared/coordination/reduce-phase.md) |
| **Cross Validation** | 交叉驗證 | [→](./shared/synthesis/cross-validation.md) |
| **Conflict Resolution** | 矛盾解決 | [→](./shared/synthesis/conflict-resolution.md) |
| **Perspectives** | 視角配置 | [→](./shared/perspectives/base-perspective.md) |
| **Memory System** | 存儲系統 | [→](./shared/integration/memory-system.md) |
| **Checkpoints** | evolve 整合 | [→](./shared/integration/evolve-checkpoints.md) |

## Core Design Principles

| Principle | Description |
|-----------|-------------|
| **Zero Dependencies** | 只使用 Task API + 內建工具，無外部 MCP 依賴 |
| **Multi-Perspective** | Map-Reduce 模式，4 視角同時工作 |
| **Cross Validation** | 共識識別 + 矛盾解決 |
| **Memory Integration** | 與 evolve Checkpoint 對應 |
| **Shared Modules** | shared/ 避免重複程式碼 |
| **Unified Entry** | 單一 plugin，6 個 skill |

## Related Projects

- [self-evolving-agent](https://github.com/miles990/self-evolving-agent) — 自我進化 Agent 框架

## Changelog

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
