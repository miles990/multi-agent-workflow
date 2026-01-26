# 品質模組（Quality）

> 品質閘門與完整性檢查

## 自動載入

當引用 `@shared/quality` 時，自動應用：
- `gates.yaml` - 品質閘門配置
- `completeness-checklist.yaml` - 完整性檢查清單

## 品質閘門

各階段必須通過品質閘門才能進入下一階段：

| 階段 | 通過分數 | 關鍵條件 |
|------|---------|----------|
| RESEARCH | ≥ 70 | 至少 2 視角共識、無關鍵矛盾 |
| PLAN | ≥ 75 | 組件設計完整、風險評估完成、里程碑定義 |
| TASKS | ≥ 80 | DAG 驗證通過、TDD 對應完整、任務有估算 |
| IMPLEMENT | ≥ 80 | 測試通過、無 BLOCKER |
| REVIEW | ≥ 75 | 無 BLOCKER、HIGH ≤ 2 |
| VERIFY | ≥ 85 | 功能+回歸測試 100% 通過、驗收標準滿足 |

## 完整性檢查

### L1: 必要條件（Mandatory）

- [ ] 所有視角報告完整
- [ ] 關鍵發現有支撐證據
- [ ] 結論不矛盾
- [ ] 需求追溯完整

### L2: 建議條件（Recommended）

- [ ] 術語使用一致
- [ ] 格式規範統一
- [ ] 交叉引用完整

## 問題嚴重度分類

| 級別 | 說明 | 處理要求 |
|------|------|----------|
| BLOCKER | 阻斷性問題，必須立即修復 | 必須解決才能繼續 |
| HIGH | 高風險問題 | 必須在當前階段解決 |
| MEDIUM | 中等問題 | 建議解決，可延後 |
| LOW | 低風險/改善建議 | 可選處理 |

## 閘門檢查流程

```
階段完成
    ↓
執行品質檢查
    ↓
┌────────────────────────────────────┐
│ 分數 >= 閘門分數？                  │
├────┬───────────────────────────────┤
│ 是 │ 通過，進入下一階段             │
│ 否 │ 失敗，需修復後重新檢查         │
└────┴───────────────────────────────┘
```

## 驗收標準模板

```yaml
acceptance_criteria:
  functional:
    - description: "功能需求 1"
      test_method: "測試方式"
      pass_criteria: "通過標準"

  non_functional:
    - description: "效能需求"
      metric: "回應時間 < 200ms"

  edge_cases:
    - description: "邊界情況 1"
      input: "極端輸入"
      expected: "預期行為"
```

## 指標記錄

每個階段完成後，記錄指標到：
```
.claude/memory/{type}/{id}/metrics.yaml
```

```yaml
stage: RESEARCH
quality_score: 78
perspectives_completed: 4
consensus_rate: 0.85
conflicts_resolved: 2
duration_minutes: 15
```

## 參考

- @shared/synthesis/cross-validation.md - 交叉驗證
- @shared/coordination/reduce-phase.md - 匯總階段
