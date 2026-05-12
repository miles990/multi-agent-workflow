# 基準線機制

> 建立和維護效能基準，追蹤改善進度

## 概述

基準線機制提供參考標準，用於評估每次執行的表現並追蹤長期改善趨勢。

## 存儲位置

```
.claude/memory/metrics/summary/baseline.yaml
```

## 基準線結構

### baseline.yaml

```yaml
# .claude/memory/metrics/summary/baseline.yaml

# 元數據
metadata:
  version: 1
  created: "2026-01-15T10:00:00Z"
  last_updated: "2026-01-24T12:00:00Z"
  sample_size: 10
  update_method: "rolling_average"

# 基準線數值
baseline:
  # 執行指標
  execution:
    duration_sec:
      average: 2850
      p50: 2700
      p90: 3500
      min: 1800
      max: 4200

    stage_duration_percent:
      research: 0.15
      plan: 0.20
      implement: 0.35
      review: 0.15
      verify: 0.15

    agent_success_rate:
      average: 0.95
      min: 0.85

  # 效率指標
  efficiency:
    rollback_count:
      average: 0.3
      p50: 0
      p90: 1
      max: 3

    first_pass_rate: 0.7

    pass_at_k:
      k1: 0.7   # 第一次通過率
      k2: 0.85  # 前兩次通過率
      k3: 0.95  # 前三次通過率

    total_iterations:
      average: 1.3
      max: 3

  # 品質指標
  quality:
    issues_per_workflow:
      average: 6.2
      by_severity:
        blocker: 0.1
        high: 0.8
        medium: 2.3
        low: 3.0

    false_positive_rate: 0.08

# 目標值
targets:
  duration_sec:
    value: 2400
    improvement: -0.16  # 減少 16%

  rollback_count:
    value: 0.2
    improvement: -0.33  # 減少 33%

  first_pass_rate:
    value: 0.85
    improvement: 0.15   # 增加 15pp

  false_positive_rate:
    value: 0.05
    improvement: -0.38  # 減少 38%

# 警戒閾值
thresholds:
  warning:
    duration_sec: 3500      # 超過此值顯示警告
    rollback_count: 2
    issues_blocker: 2

  critical:
    duration_sec: 4500      # 超過此值顯示嚴重警告
    rollback_count: 3
    issues_blocker: 3
```

## 基準線建立

### 首次建立

首次執行工作流時自動建立初始基準線：

```yaml
initial_baseline:
  trigger: "first_workflow_complete"

  # 使用首次執行的數據
  # 或使用預設值
  defaults:
    duration_sec: 3600      # 1 小時
    rollback_count: 1
    first_pass_rate: 0.5
    issues_per_workflow: 10
```

### 建立流程

```
首次工作流完成
       ↓
檢查 baseline.yaml 是否存在
       ↓
   不存在
       ↓
使用首次數據建立基準線
       ↓
設定預設目標（改善 20%）
       ↓
儲存 baseline.yaml
```

## 基準線更新

### 滾動平均更新

每次工作流完成後更新基準線：

```yaml
update_policy:
  method: "rolling_average"
  window_size: 10           # 最近 10 次執行
  update_frequency: "per_workflow"

  # 計算方式
  # new_baseline = (old_baseline * (n-1) + new_value) / n
  # 其中 n = min(current_count, window_size)
```

### 更新流程

```
工作流完成
     ↓
讀取當前 baseline.yaml
     ↓
計算滾動平均
     ↓
更新 baseline 數值
     ↓
檢查是否達到目標
     ↓
     ├── 是 → 設定新目標
     │
     └── 否 → 保持目標
     ↓
儲存更新後的 baseline.yaml
```

### 更新邏輯

```python
def update_baseline(current_baseline, new_metrics, window_size=10):
    """
    更新基準線（滾動平均）
    """
    sample_size = current_baseline['metadata']['sample_size']
    n = min(sample_size + 1, window_size)

    # 計算新的平均值
    for metric in ['duration_sec', 'rollback_count', 'issues']:
        old_value = current_baseline['baseline'][metric]['average']
        new_value = new_metrics[metric]

        # 滾動平均公式
        updated_value = (old_value * (n - 1) + new_value) / n
        current_baseline['baseline'][metric]['average'] = updated_value

    # 更新元數據
    current_baseline['metadata']['sample_size'] = n
    current_baseline['metadata']['last_updated'] = now()

    return current_baseline
```

## 手動重設

### 重設指令

```bash
# 重設為預設值
/multi-orchestrate --reset-baseline

# 使用指定執行作為新基準
/multi-orchestrate --set-baseline {workflow-id}

# 強制使用最近 N 次執行重新計算
/multi-orchestrate --recalculate-baseline --last 20
```

### 重設場景

| 場景 | 建議操作 |
|------|----------|
| 重大架構變更 | 重設為預設值 |
| 異常值污染 | 排除異常後重新計算 |
| 新團隊成員 | 保持現有基準線 |
| 新專案開始 | 重設為預設值 |

## 基準線使用

### 在報告中使用

```markdown
## 與基準線對比

| 指標 | 本次 | 基準線 | 差異 | 評價 |
|------|------|--------|------|------|
| 總耗時 | 45 分鐘 | 47.5 分鐘 | -5% | 良好 |
| 回退次數 | 1 | 0.3 | +233% | 需改善 |
| 問題數 | 5 | 6.2 | -19% | 良好 |
```

### 評價標準

```yaml
evaluation_criteria:
  excellent:
    condition: "value < baseline * 0.8"
    label: "優秀"

  good:
    condition: "value < baseline * 1.0"
    label: "良好"

  normal:
    condition: "value < baseline * 1.2"
    label: "正常"

  warning:
    condition: "value < baseline * 1.5"
    label: "需關注"

  critical:
    condition: "value >= baseline * 1.5"
    label: "需改善"
```

### 在建議中使用

```yaml
suggestion_rules:
  - name: "high_duration"
    condition: "duration > baseline.duration * 1.3"
    suggestion: "執行時間超過基準線 30%，建議優化"

  - name: "high_rollback"
    condition: "rollback > baseline.rollback * 2"
    suggestion: "回退次數超過基準線 2 倍，建議分析原因"
```

## 目標管理

### 自動目標調整

當達到目標時自動設定新目標：

```yaml
target_adjustment:
  trigger: "target_achieved"

  rules:
    duration_sec:
      improvement_step: 0.10  # 每次改善 10%
      min_value: 1800         # 最小目標值

    rollback_count:
      improvement_step: 0.20  # 每次改善 20%
      min_value: 0.1

    first_pass_rate:
      improvement_step: 0.05  # 每次改善 5pp
      max_value: 0.95         # 最大目標值
```

### 目標檢查

```
工作流完成
     ↓
計算近期平均值（最近 5 次）
     ↓
與目標對比
     ↓
     ├── 達標 → 設定新目標
     │         ├── 記錄達標事件
     │         └── 計算新目標值
     │
     └── 未達標 → 保持目標
               └── 記錄差距
```

## 基準線報告

### 基準線狀態報告

```markdown
# 基準線狀態報告

**更新時間**: 2026-01-24 12:00
**樣本數量**: 10

## 當前基準線

| 指標 | 基準值 | 目標值 | 差距 |
|------|--------|--------|------|
| 平均耗時 | 47.5 分鐘 | 40 分鐘 | -16% |
| 回退次數 | 0.3 | 0.2 | -33% |
| 一次通過率 | 70% | 85% | +15pp |
| 誤報率 | 8% | 5% | -38% |

## 達標進度

```
平均耗時     [████████░░░░░░░░]  50%
回退次數     [██████████░░░░░░]  60%
一次通過率   [████████████░░░░]  75%
誤報率       [██████░░░░░░░░░░]  40%
```

## 歷史基準線

| 日期 | 平均耗時 | 回退次數 | 一次通過率 |
|------|----------|----------|------------|
| 01/24 | 47.5 分鐘 | 0.3 | 70% |
| 01/17 | 50 分鐘 | 0.5 | 65% |
| 01/10 | 55 分鐘 | 0.8 | 55% |
```

## 相關模組

- [單次報告](./single-report.md)
- [週報](./weekly-report.md)
- [指標收集器](../metrics/collector.md)
- [Memory 結構](../metrics/memory-structure.md)
