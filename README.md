# Multi-Agent Research Skill

> 多 Agent 並行研究框架：多視角同時研究，智能匯總成完整報告

## Features

- **多視角並行研究**：同時從架構、認知、工作流、業界等視角分析
- **Map-Reduce 協調**：並行研究 → 交叉驗證 → 智能匯總
- **零依賴設計**：只使用 Claude Code 內建工具，即裝即用
- **Memory 整合**：研究結果自動存檔，支持復用和查詢

## Installation

```bash
# 使用 Claude Code Plugin
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
```

## Default Perspectives

| ID | Name | Focus |
|----|------|-------|
| architecture | 架構分析師 | 系統結構、設計模式、可擴展性 |
| cognitive | 認知科學研究員 | 方法論、思維模式、認知框架 |
| workflow | 工作流設計師 | 執行流程、整合策略、實作步驟 |
| industry | 業界實踐研究員 | 現有框架、案例研究、最佳實踐 |

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

## Execution Flow

```
Phase 0: 北極星錨定
    ↓
Phase 1: Memory 搜尋（避免重複研究）
    ↓
Phase 2: 視角分解
    ↓
Phase 3: MAP（並行研究）
    ├─ Task API 啟動多個 Agent
    └─ 各 Agent 獨立研究
    ↓
Phase 4: 同步檢查點
    ↓
Phase 5: REDUCE（串行整合）
    ├─ 交叉驗證
    ├─ 矛盾解決
    └─ 報告生成
    ↓
Phase 6: Memory 存檔
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
- CP1: Memory 搜尋
- CP3: 目標確認
- CP3.5: Memory 存檔

### Zero Dependencies

只使用 Claude Code 內建工具：
- Task API（並行 Agent）
- WebSearch（網路搜尋）
- 檔案系統（狀態管理）

## Documentation

- [Quick Start Guide](./skills/multi-agent-research/00-quickstart/_base/usage.md)
- [Default Perspectives](./skills/multi-agent-research/01-perspectives/_base/default-perspectives.md)
- [Custom Perspectives](./skills/multi-agent-research/01-perspectives/_base/custom-perspectives.md)
- [Map Phase](./skills/multi-agent-research/02-coordination/_base/map-phase.md)
- [Reduce Phase](./skills/multi-agent-research/02-coordination/_base/reduce-phase.md)
- [Cross Validation](./skills/multi-agent-research/03-synthesis/_base/cross-validation.md)
- [Conflict Resolution](./skills/multi-agent-research/03-synthesis/_base/conflict-resolution.md)

## License

MIT

## Author

miles990
