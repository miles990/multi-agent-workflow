# Closed-Loop Summary

## 目標

把 CT research、retrospective、自主升級決策收斂成單一成果報告，讓使用者不用翻多個 artifact 才知道結論。

## 產生時機

在以下步驟完成後產生：

```text
Synthesis
→ CT Compliance
→ Quality Gate
→ CT Retrospective
→ Self-Upgrade Proposal
→ Autonomous Upgrade Decision
→ Closed-Loop Summary
```

## 輸出

```text
.claude/memory/research/{topic-id}/closed-loop-summary.md
```

## 格式

```markdown
# Closed-Loop Summary

## Outcome
- research_question:
- final_status:
- quality_score:

## Selected CT Mode
- selected_mode:
- confidence:
- mode_was_correct:
- rationale:

## Key Artifacts
| Artifact | Status | Path |
|---|---|---|

## Retrospective Finding
- over_escalation:
- under_escalation:
- workflow_failures:
- lessons:

## Upgrade Decision
- decision:
- automation_level:
- applied_changes:
- requires_human_approval:

## Verification
- quality_gates:
- dag:
- status:
- action_log:
- tests:

## Final Recommendation
```

