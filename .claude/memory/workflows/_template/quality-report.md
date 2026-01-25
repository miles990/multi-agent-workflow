# 📊 品質評估報告

## 總體評分：{total_score}/100

### 評分細項

| 維度 | 分數 | 權重 | 加權分 |
|------|------|------|--------|
| 功能完整性 | {func_score} | 25% | {func_weighted} |
| 測試覆蓋 | {test_score} | 20% | {test_weighted} |
| 安全性 | {sec_score} | 25% | {sec_weighted} |
| 可維護性 | {maint_score} | 15% | {maint_weighted} |
| 效能 | {perf_score} | 15% | {perf_weighted} |
| **總計** | | 100% | **{total_score}** |

### 各階段品質

{stage_quality_table}

### 問題追蹤

{issues_table}

### TDD 遵循追蹤

{tdd_tracking_table}
