# Orchestrate 視角定義

本 Skill 為編排器，協調各階段 Skill 的執行，視角由各階段 Skill 自行管理。

## 說明

`orchestrate` 是端到端工作流編排器，負責：
1. 串聯 RESEARCH → PLAN → TASKS → IMPLEMENT → REVIEW → VERIFY 各階段
2. 品質閘門控制和智慧回退
3. File-Based Handoff 協議管理

## 視角委派

Orchestrate 不直接定義視角，而是將視角管理委派給各階段 Skill：

| 階段 | Skill | 視角來源 |
|------|-------|---------|
| RESEARCH | `/research` | `skills/research/01-perspectives/` |
| PLAN | `/plan` | `skills/plan/01-perspectives/` |
| TASKS | `/tasks` | `skills/tasks/01-perspectives/` |
| IMPLEMENT | `/implement` | `skills/implement/01-perspectives/` |
| REVIEW | `/review` | `skills/review/01-perspectives/` |
| VERIFY | `/verify` | `skills/verify/01-perspectives/` |

## 執行模式配置

視角數量由執行模式決定：

```yaml
# shared/config/execution-profiles.yaml
profiles:
  express:     # 快速模式 - 2 視角
  default:     # 預設模式 - 4 視角
  quality:     # 品質模式 - 6 視角
```

## 相關資源

- [SKILL.md](../../SKILL.md) - 完整的 Skill 定義
- [usage.md](../../00-quickstart/_base/usage.md) - 快速上手指南
- [execution-profiles.yaml](../../../../shared/config/execution-profiles.yaml) - 執行模式配置
