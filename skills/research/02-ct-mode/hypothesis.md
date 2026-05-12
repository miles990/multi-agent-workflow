# Hypothesis Forge

## 目標

把 `/multi-research` 在 CT-experiment 模式下的核心結論轉成可驗證假設。

## 格式

```yaml
hypothesis:
  id: H001
  claim: "分層 CT 可降低 agent drift"
  independent_variable: "CT layer design: none | single-layer | multi-layer"
  dependent_variable: "drift_event_count"
  control: "same task without CT"
  metric: "drift_event_count, unsupported_claim_rate"
  falsification: "multi-layer CT drift rate is not lower than control"
  confidence: medium
```

## 規則

- 沒有變因與指標的 claim 只能保留為 research note。
- 高價值假設必須包含對照組與失敗案例。
