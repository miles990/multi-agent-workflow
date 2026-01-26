執行多視角研究分析。

## 流程

1. 載入 @skills/research/SKILL.md
2. 載入 @shared/coordination/map-phase.md
3. 並行啟動 4 視角 Agent（architecture, cognitive, workflow, industry）
4. 收集視角報告到 `.claude/memory/research/{topic-id}/perspectives/`
5. 執行 @shared/coordination/reduce-phase.md 匯總
6. 生成 `synthesis.md`

## 視角配置

| ID | 名稱 | 模型 | 聚焦 |
|----|------|------|------|
| architecture | 架構分析師 | sonnet | 系統結構、設計模式 |
| cognitive | 認知研究員 | sonnet | 方法論、思維框架 |
| workflow | 工作流設計 | haiku | 執行流程、整合策略 |
| industry | 業界實踐 | haiku | 現有框架、最佳實踐 |

模型路由：@shared/config/model-routing.yaml

## Flags

- `--perspectives N` - 指定視角數量（預設 4）
- `--quick` - 快速模式（2 視角）
- `--deep` - 深度模式（6 視角）
- `--no-memory` - 不保存到 Memory

## 輸出

```
.claude/memory/research/{topic-id}/
├── meta.yaml
├── perspectives/*.md
├── summaries/*.yaml
└── synthesis.md
```

## 擴展思考

複雜架構分析時，建議在提示中加入 `ultrathink` 或按 Option+T 啟用。

$ARGUMENTS
