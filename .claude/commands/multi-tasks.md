執行任務分解，生成 DAG 任務清單。

## 流程

1. 載入 @skills/tasks/SKILL.md
2. 載入 @shared/coordination/map-phase.md
3. 並行啟動 4 視角 Agent（dependency-analyst, task-decomposer, test-planner, risk-preventor）
4. 收集視角報告到 `.claude/memory/tasks/{plan-id}/perspectives/`
5. 執行 @shared/coordination/reduce-phase.md 匯總
6. 生成 `tasks.yaml`（DAG 定義）

## 視角配置

| ID | 名稱 | 模型 | 聚焦 |
|----|------|------|------|
| dependency-analyst | 依賴分析師 | sonnet | 任務依賴、執行順序 |
| task-decomposer | 任務分解師 | haiku | 粒度切分、並行識別 |
| test-planner | 測試規劃師 | haiku | TDD 對應、測試策略 |
| risk-preventor | 風險預防師 | haiku | 風險任務、預防措施 |

模型路由：@shared/config/model-routing.yaml

## 前置條件

必須先執行 `/multi-plan`：
```
.claude/memory/plans/{feature-id}/implementation-plan.md
```

## Flags

- `--plan <path>` - 指定計劃路徑
- `--granularity <fine|medium|coarse>` - 任務粒度

## 輸出

```
.claude/memory/tasks/{plan-id}/
├── meta.yaml
├── perspectives/*.md
├── summaries/*.yaml
└── tasks.yaml
```

## DAG 格式

```yaml
tasks:
  - id: T001
    title: 任務標題
    depends_on: []
    estimated_effort: S/M/L
    test_strategy: unit/integration/e2e
```

$ARGUMENTS
