# CT Retrospective

## 目標

在 `/multi-research` 結束後吃自己的狗食：檢查本次 CT mode 是否選對、輸出 artifact 是否完整、workflow 是否暴露可回寫的失敗模式。

## 執行時機

在 REDUCE、CT compliance、quality gate 之後執行。若 workflow 失敗，也必須產生 retrospective，標記為 partial。

```text
CT Escalation Router
→ MAP
→ REDUCE
→ CT Compliance
→ Quality Gate
→ CT Retrospective
→ Self-Upgrade Proposal
```

## 必查項目

- `selected_mode` 是否符合使用者意圖
- 是否過度升級造成摩擦
- 是否低估風險造成 artifact 缺漏
- CT-strict / experiment 必要產物是否存在
- 是否有 workflow failure 可轉為 regression case
- 是否應更新 escalation rules、quality gates、templates、scripts

## 輸出

寫入：

```text
.claude/memory/research/{topic-id}/ct-retrospective.md
```

格式：

```markdown
# CT Retrospective

## Mode Review
- selected_mode:
- expected_mode:
- mode_was_correct:
- over_escalation:
- under_escalation:
- confidence:
- rationale:

## Artifact Review
| Artifact | Required | Present | Notes |
|---|---:|---:|---|

## Workflow Failures
| Failure | Layer | Severity | Evidence | Regression Case |
|---|---|---|---|---|

## Lessons
- ...

## Recommended Updates
| Target | Change | Risk | Automation Level |
|---|---|---|---|
```

## Automation Level

- `L1`: 只記錄 retrospective
- `L2`: 產生 self-upgrade proposal
- `L3`: 低風險 docs / templates / CT examples 可自動修
- `L4`: router / gates / scripts 可修，但必須跑測試
- `L5`: 架構級變更需人工批准

