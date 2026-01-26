執行多視角規劃分析。

## 流程

1. 載入 @skills/plan/SKILL.md
2. 載入 @shared/coordination/map-phase.md
3. 並行啟動 4 視角 Agent（architect, risk-analyst, estimator, ux-advocate）
4. 收集視角報告到 `.claude/memory/plans/{feature-id}/perspectives/`
5. 執行 @shared/coordination/reduce-phase.md 匯總
6. 生成 `implementation-plan.md`

## 視角配置

| ID | 名稱 | 模型 | 聚焦 |
|----|------|------|------|
| architect | 系統架構師 | sonnet | 技術可行性、組件設計 |
| risk-analyst | 風險分析師 | sonnet | 潛在風險、失敗場景 |
| estimator | 估算專家 | haiku | 工作量評估、時程規劃 |
| ux-advocate | UX 倡導者 | haiku | 使用者體驗、API 設計 |

模型路由：@shared/config/model-routing.yaml

## 前置條件

建議先執行 `/multi-research` 收集背景資料：
```
.claude/memory/research/{topic-id}/synthesis.md
```

## Flags

- `--research <path>` - 指定研究報告路徑
- `--quick` - 快速模式
- `--deep` - 深度模式

## 輸出

```
.claude/memory/plans/{feature-id}/
├── meta.yaml
├── perspectives/*.md
├── summaries/*.yaml
└── implementation-plan.md
```

## 擴展思考

技術選型和方案比較時，建議使用擴展思考。

$ARGUMENTS
