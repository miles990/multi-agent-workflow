# Evaluation Design

## 目標

為 CT 假設建立可重跑的評估設計。

## 必填欄位

```yaml
eval_case:
  id: E001
  prompt: string
  control_condition: string
  treatment_condition: string
  expected_observation: string
  metrics:
    - constraint_compliance_rate
    - unsupported_claim_rate
    - drift_event_count
  pass_criteria:
    evidence_coverage: ">= 0.8"
    hypothesis_testability_score: ">= 0.7"
```

## 設計原則

- 控制組與實驗組只改變 CT 條件。
- 指標必須能從報告或 action logs 中抽取。
- 至少包含一個容易誘發 drift 的壓力案例。
