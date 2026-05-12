# Autonomous Upgrade

## 目標

讓研究流程在完成 retrospective / proposal 後，能在安全邊界內自主修正 workflow、CT 規則、文件或測試案例。

## 位置

```text
CT Retrospective
→ Self-Upgrade Proposal
→ Autonomous Upgrade Decision
→ Patch
→ Verify
→ Upgrade Report
```

## 決策規則

| Level | 行為 |
|---|---|
| L1 | 只記錄，不修改 |
| L2 | 只產生 proposal，不修改 |
| L3 | 可修改 docs / templates / examples / CT guidance |
| L4a | 可修改 escalation rules / non-critical validators，但必須跑 focused smoke test |
| L4b | quality gates 只提案，需人工批准 |
| L4c | workflow scripts 只提案，需人工批准 |
| L5 | 停止，要求人工批准 |

## 必要輸出

```text
.claude/memory/research/{topic-id}/upgrade-decision.yaml
.claude/memory/research/{topic-id}/upgrade-report.md  # 有實際 patch 時
```

## `upgrade-decision.yaml`

```yaml
upgrade_decision:
  proposal:
  automation_level:
  decision: applied | skipped | requires_human_approval
  reason:
  target_files:
  verification:
    commands:
    result:
  rollback_plan:
```

## 安全限制

- 不得修改 unrelated user changes。
- 不得靜默弱化 quality gate。
- L4a 必須附驗證命令與通過結果。
- L4b/L4c 只可提出 proposal，不得自主套用。
- L5 只能提出，不得套用。
- 無法驗證時，decision 必須是 `skipped` 或 `requires_human_approval`。
