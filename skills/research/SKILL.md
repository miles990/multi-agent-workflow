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
    ⚠️ **強制**：每個 Agent 必須在完成前執行：
       1. mkdir -p .claude/memory/research/{topic-id}/perspectives/
       2. Write → .claude/memory/research/{topic-id}/perspectives/{perspective_id}.md
       未執行 Write = 任務失敗，工作流中止
    ↓
Phase 4: REDUCE（交叉驗證 + 匯總）
    ↓
Phase 5: Memory 存檔 → 品質閘門檢查 → 存儲報告
```

## CP4: Task Commit

Memory 存檔完成後，**必須執行 CP4 Task Commit**。

```
Phase 5: Memory 存檔
    ↓
CP4: Task Commit
    ├── git add .claude/memory/research/{topic-id}/
    └── git commit -m "docs(research): complete {topic} research"
```

→ 協議：[shared/git/commit-protocol.md](../../shared/git/commit-protocol.md)

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

## Agent 能力限制

**視角 Agent 不應該開啟 Task**：

| 允許的操作 | 說明 |
|-----------|------|
| ✅ Read | 讀取檔案 |
| ✅ Glob/Grep | 搜尋檔案和內容 |
| ✅ Explore agent | 輕量級探索 |
| ✅ Bash | 執行命令 |
| ✅ WebFetch | 抓取網頁 |
| ✅ Write | 寫入報告 |
| ❌ Task | 開子 Agent |

## 網頁抓取策略

當需要抓取網頁時，使用以下順序：

1. **優先使用 WebFetch** - 快速、輕量
2. **如果 WebFetch 失敗**，使用 Chrome：
   ```
   a. mcp__claude-in-chrome__tabs_create_mcp → 建立新分頁
   b. mcp__claude-in-chrome__navigate → 導航到 URL
   c. mcp__claude-in-chrome__get_page_text → 讀取內容
   ```
3. **如果仍然失敗**，記錄 URL 供人工處理

## 行動日誌

每個工具調用完成後，記錄到 `.claude/workflow/{workflow-id}/logs/actions.jsonl`。

**記錄時機**：
- 成功：記錄 `tool`、`input`、`output_preview`、`duration_ms`、`status: success`
- 失敗：記錄 `tool`、`input`、`error`、`stderr`（如有）、`status: failed`

**關鍵行動（RESEARCH 階段）**：
| 行動 | 記錄重點 |
|------|----------|
| Read（讀取檔案） | `file_path`、`output_size` |
| Glob（搜尋檔案） | `pattern`、`match_count` |
| Grep（搜尋內容） | `pattern`、`match_count` |
| Task（啟動 Agent） | `subagent_type`、`prompt` (truncated)、`agent_id` |
| WebFetch（抓取網頁） | `url`、`status_code` |

**排查問題**：
```bash
# 查看 RESEARCH 階段所有失敗行動
jq 'select(.stage == "RESEARCH" and .status == "failed")' actions.jsonl

# 查看特定視角 Agent 的行動
jq 'select(.agent_id == "agent_architecture")' actions.jsonl
```

→ 日誌規範：[shared/communication/execution-logs.md](../../shared/communication/execution-logs.md)

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
