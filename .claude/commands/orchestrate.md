執行端到端工作流編排。

## 完整流程

```
RESEARCH → PLAN → TASKS → IMPLEMENT → REVIEW → VERIFY
```

1. 載入 @skills/orchestrate/SKILL.md
2. 初始化工作流（`.claude/workflow/current.json`）
3. 依序執行各階段
4. 品質閘門檢查（@shared/quality/gates.yaml）
5. 自動 git commit（hooks 處理）

## 階段說明

| 階段 | 視角數 | 主輸出 |
|------|--------|--------|
| RESEARCH | 4 | synthesis.md |
| PLAN | 4 | implementation-plan.md |
| TASKS | 4 | tasks.yaml |
| IMPLEMENT | 4 角色 | summary.md |
| REVIEW | 4 | review-summary.md |
| VERIFY | 4 | verify-summary.md |

## Flags

- `--start-from <stage>` - 從指定階段開始（RESEARCH/PLAN/TASKS/IMPLEMENT/REVIEW/VERIFY）
- `--stop-at <stage>` - 在指定階段停止
- `--quick` - 快速模式（每階段 2 視角）
- `--deep` - 深度模式（每階段 6 視角）
- `--no-worktree` - 不使用 git worktree

## 品質閘門

| 階段 | 通過分數 |
|------|---------|
| RESEARCH | ≥ 70 |
| PLAN | ≥ 75 |
| TASKS | ≥ 80 |
| IMPLEMENT | ≥ 80 |
| REVIEW | ≥ 75 |
| VERIFY | ≥ 85 |

## 斷點續接

如果工作流中斷，可使用：
```
/orchestrate --resume
```

會從 `.claude/workflow/current.json` 讀取狀態並續接。

## 輸出

所有階段輸出保存到：
```
.claude/memory/
├── research/{topic-id}/
├── plans/{feature-id}/
├── tasks/{plan-id}/
├── implement/{tasks-id}/
├── review/{impl-id}/
└── verify/{review-id}/
```

$ARGUMENTS
