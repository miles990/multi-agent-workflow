# Multi-Agent Research Skill

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/miles990/multi-agent-research-skill)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugin-purple.svg)](https://claude.ai/code)

> 多 Agent 並行研究框架：多視角同時研究，智能匯總成完整報告

## Features

- **多視角並行研究**：同時從架構、認知、工作流、業界等視角分析
- **Map-Reduce 協調**：並行研究 → 交叉驗證 → 智能匯總
- **零依賴設計**：只使用 Claude Code 內建工具，即裝即用
- **Memory 整合**：研究結果自動存檔，支持復用和查詢

## Installation

### Via Plugin Marketplace (Recommended)

```bash
# 添加 Marketplace
/plugin marketplace add miles990/multi-agent-research-skill

# 安裝 Plugin
/plugin install multi-agent-research@multi-agent-research-skill
```

### Direct Install

```bash
/plugin install miles990/multi-agent-research-skill
```

## Quick Start

```bash
# 基本用法
/multi-research AI Agent 架構設計模式

# 快速模式（2 視角）
/multi-research --quick 技術選型問題

# 深度模式（6 視角）
/multi-research --deep 重大架構決策

# 自訂視角
/multi-research --custom 特定領域問題
```

## Default Perspectives

| ID | Name | Focus |
|----|------|-------|
| `architecture` | 架構分析師 | 系統結構、設計模式、可擴展性 |
| `cognitive` | 認知科學研究員 | 方法論、思維模式、認知框架 |
| `workflow` | 工作流設計師 | 執行流程、整合策略、實作步驟 |
| `industry` | 業界實踐研究員 | 現有框架、案例研究、最佳實踐 |

## Execution Flow

```
/multi-research [主題]
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 0: 北極星錨定                 │
│  Phase 1: Memory 搜尋（避免重複）    │
│  Phase 2: 視角分解                   │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 3: MAP（並行研究）            │
│  ┌────────┬────────┬────────┬────┐ │
│  │ 架構   │ 認知   │ 工作流 │ 業界│ │
│  │ Agent  │ Agent  │ Agent  │Agent│ │
│  └────────┴────────┴────────┴────┘ │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 4-5: REDUCE（整合）           │
│  • 交叉驗證 → 識別共識               │
│  • 矛盾解決 → 多輪分析               │
│  • 報告生成 → 匯總報告               │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 6: Memory 存檔                │
└─────────────────────────────────────┘
```

## Output Structure

```
.claude/memory/research/[topic-id]/
├── meta.yaml           # 元數據
├── overview.md         # 一頁概述
├── perspectives/       # 各視角報告
│   ├── architecture.md
│   ├── cognitive.md
│   ├── workflow.md
│   └── industry.md
└── synthesis.md        # 匯總報告（主輸出）
```

## Flags

| Flag | Description |
|------|-------------|
| `--perspectives N` | 使用 N 個視角（預設 4）|
| `--quick` | 快速模式：2 視角，淺度研究 |
| `--deep` | 深度模式：6 視角，詳盡研究 |
| `--custom` | 互動式自訂視角 |
| `--no-memory` | 不存檔到 Memory |

## Integration

### With evolve Skill

研究流程與 evolve Checkpoint 對應：

| Checkpoint | 動作 |
|------------|------|
| CP1 | Memory 搜尋 |
| CP3 | 目標確認 |
| CP3.5 | Memory 存檔 |

### Zero Dependencies

只使用 Claude Code 內建工具：
- **Task API** — 並行 Agent
- **WebSearch** — 網路搜尋
- **File System** — 狀態管理

## Documentation

| Module | Description | Link |
|--------|-------------|------|
| Quick Start | 3 分鐘上手 | [→](./skills/multi-agent-research/00-quickstart/_base/usage.md) |
| Perspectives | 視角配置 | [→](./skills/multi-agent-research/01-perspectives/_base/default-perspectives.md) |
| Custom | 自訂視角 | [→](./skills/multi-agent-research/01-perspectives/_base/custom-perspectives.md) |
| Map Phase | 並行研究 | [→](./skills/multi-agent-research/02-coordination/_base/map-phase.md) |
| Reduce Phase | 整合匯總 | [→](./skills/multi-agent-research/02-coordination/_base/reduce-phase.md) |
| Cross Validation | 交叉驗證 | [→](./skills/multi-agent-research/03-synthesis/_base/cross-validation.md) |
| Conflict Resolution | 矛盾解決 | [→](./skills/multi-agent-research/03-synthesis/_base/conflict-resolution.md) |

## Related Projects

- [self-evolving-agent](https://github.com/miles990/self-evolving-agent) — 自我進化 Agent 框架

## License

[MIT](./LICENSE)

## Author

**miles990** — [GitHub](https://github.com/miles990)
