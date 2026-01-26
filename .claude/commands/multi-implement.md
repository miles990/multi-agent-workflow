執行監督式實作。

## 流程

1. 載入 @skills/implement/SKILL.md
2. 建立 Git Worktree（`.worktrees/{feature-id}/`）
3. 依 DAG 順序執行任務
4. 各角色審查（tdd-enforcer, security-auditor, maintainer）
5. 收集角色報告到 `.claude/memory/implement/{tasks-id}/perspectives/`
6. 生成 `summary.md`

## 角色配置

| ID | 名稱 | 模型 | 聚焦 |
|----|------|------|------|
| main_agent | 主實作者 | sonnet | 功能實作 |
| tdd-enforcer | TDD 守護者 | haiku | 測試先行檢查 |
| security-auditor | 安全審計員 | sonnet | 安全漏洞檢測 |
| maintainer | 可維護性審查 | haiku | 程式碼品質 |

模型路由：@shared/config/model-routing.yaml

## 前置條件

必須先執行 `/multi-tasks`：
```
.claude/memory/tasks/{plan-id}/tasks.yaml
```

## Flags

- `--tasks <path>` - 指定任務清單路徑
- `--worktree <name>` - 指定 worktree 名稱
- `--no-worktree` - 不使用 worktree（直接在主分支）

## TDD 流程

每個任務執行順序：
1. 寫測試（紅）
2. 實作（綠）
3. 重構（藍）
4. 審查（角色檢查）

## 輸出

```
.claude/memory/implement/{tasks-id}/
├── meta.yaml
├── perspectives/*.md
└── summary.md
```

$ARGUMENTS
