---
name: research
version: 3.0.0
description: 多 Agent 並行研究框架 - 多視角同時研究，智能匯總成完整報告
triggers: [multi-research, parallel-research, 多角度研究]
---

# Multi-Agent Research v3.0.0

> 多視角並行研究 → 交叉驗證 → 智能匯總 → Memory 存檔

## 使用方式

```bash
/multi-research [研究主題]
/multi-research AI Agent 架構設計模式 --deep
```

**Flags**: `--perspectives N` | `--quick` | `--deep` | `--no-memory`

## 預設 4 視角

| ID | 名稱 | 模型 | 聚焦 |
|----|------|------|------|
| `architecture` | 架構分析師 | sonnet | 系統結構、設計模式 |
| `cognitive` | 認知研究員 | sonnet | 方法論、思維框架 |
| `workflow` | 工作流設計 | haiku | 執行流程、整合策略 |
| `industry` | 業界實踐 | haiku | 現有框架、最佳實踐 |

→ 模型路由配置：[shared/config/model-routing.yaml](../../shared/config/model-routing.yaml)

## 執行流程

```
Phase 0: 北極星錨定 → 定義研究目標、成功標準
    ↓
Phase 1: Memory 搜尋 → 避免重複研究
    ↓
Phase 2: 視角分解 → 為每視角生成專屬 prompt
    ↓
Phase 3: MAP（並行研究）
    ┌──────────┬──────────┬──────────┬──────────┐
    │架構分析師│認知研究員│工作流設計│業界實踐  │
    └──────────┴──────────┴──────────┴──────────┘
    ⚠️ 每個 Agent 完成後立即 Write → perspectives/{id}.md
    ↓
Phase 4: REDUCE（交叉驗證 + 匯總）
    ↓
Phase 5: Memory 存檔 → 品質閘門檢查 → 存儲報告
```

## 品質閘門

通過條件（RESEARCH 階段）：
- ✅ 至少 2 視角達成共識
- ✅ 無未解決的關鍵矛盾
- ✅ 品質分數 ≥ 70

→ 閘門配置：[shared/quality/gates.yaml](../../shared/quality/gates.yaml)

## 早期終止

當 `consensus_rate >= 0.9` 時，可跳過衝突解決。

→ 配置：[shared/config/early-termination.yaml](../../shared/config/early-termination.yaml)

## Context7 整合

自動偵測技術棧關鍵字（react, vue, fastapi 等）時，查詢最新文檔。

→ 配置：[shared/integration/context7.yaml](../../shared/integration/context7.yaml)

## 輸出結構

```
.claude/memory/research/[topic-id]/
├── meta.yaml           # 元數據
├── perspectives/       # 完整視角報告（MAP 產出，保留）
│   ├── architecture.md
│   ├── cognitive.md
│   ├── workflow.md
│   └── industry.md
├── summaries/          # 結構化摘要（REDUCE 產出，供快速查閱）
│   ├── architecture.yaml
│   ├── cognitive.yaml
│   ├── workflow.yaml
│   └── industry.yaml
├── synthesis.md        # 匯總報告（主輸出）
└── metrics.yaml        # 階段指標
```

> ⚠️ perspectives/ 保存完整報告，summaries/ 保存結構化摘要，兩者都必須保留。

## 共用模組

| 模組 | 用途 |
|------|------|
| [coordination/map-phase.md](../../shared/coordination/map-phase.md) | 並行協調 |
| [coordination/reduce-phase.md](../../shared/coordination/reduce-phase.md) | 匯總整合、大檔案處理 |
| [synthesis/cross-validation.md](../../shared/synthesis/cross-validation.md) | 交叉驗證 |
| [quality/gates.yaml](../../shared/quality/gates.yaml) | 品質閘門 |
| [config/model-routing.yaml](../../shared/config/model-routing.yaml) | 模型路由 |

## 工作流位置

```
RESEARCH → PLAN → TASKS → IMPLEMENT → REVIEW → VERIFY
   ↑
  你在這裡
```

研究結果可被 `plan` skill 引用，作為規劃的輸入。
