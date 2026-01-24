# Metrics Memory 結構

> 定義指標數據的存儲結構和組織方式

## 目錄結構

```
.claude/memory/metrics/
├── {workflow-id}/              ← 單次工作流指標
│   ├── metrics.yaml            ← 原始指標數據
│   └── report.md               ← 可讀報告
└── summary/                    ← 彙總數據
    ├── weekly.md               ← 週報
    ├── trends.yaml             ← 趨勢數據
    └── baseline.yaml           ← 基準線數據
```

## 單次工作流指標

### metrics.yaml

每次工作流執行產生一個指標檔案：

```yaml
# .claude/memory/metrics/{workflow-id}/metrics.yaml

workflow_id: "abc123-def456"
task: "實作用戶認證功能"
started_at: "2026-01-24T10:00:00Z"
ended_at: "2026-01-24T10:45:00Z"
total_duration_sec: 2700
status: completed

stages:
  - stage_id: research
    started_at: "2026-01-24T10:00:00Z"
    ended_at: "2026-01-24T10:08:00Z"
    duration_sec: 480
    status: completed
    perspectives:
      - id: architecture
        status: completed
        duration_sec: 120
      - id: security
        status: completed
        duration_sec: 115
    execution:
      agent_success_rate: 100
      retry_count: 0

  - stage_id: plan
    # ... 類似結構

  - stage_id: implement
    # ... 包含 iterations 數據

  - stage_id: review
    quality:
      issues_found: 5
      by_severity:
        blocker: 0
        high: 1
        medium: 2
        low: 2

  - stage_id: verify
    # ... 包含 pass_at_k 數據

summary:
  total_agents: 16
  successful_agents: 16
  total_issues: 5
  blockers: 0
  total_rollbacks: 0
  final_pass_at_k: 1
```

### report.md

人類可讀的報告格式：

```markdown
# 工作流執行報告

## 執行摘要

| 指標 | 值 |
|------|-----|
| 工作流 ID | abc123-def456 |
| 任務 | 實作用戶認證功能 |
| 總耗時 | 45 分鐘 |
| 回退次數 | 0 |
| 一次通過 | 是 |

## 階段耗時分布

```
RESEARCH   ████████░░░░░░░░░░░░  8 分鐘 (18%)
PLAN       ████████████░░░░░░░░ 12 分鐘 (27%)
IMPLEMENT  ████████████████░░░░ 15 分鐘 (33%)
REVIEW     ████████░░░░░░░░░░░░  5 分鐘 (11%)
VERIFY     ████████░░░░░░░░░░░░  5 分鐘 (11%)
```

## 問題分布

| 嚴重度 | 數量 |
|--------|------|
| BLOCKER | 0 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 2 |

## 改善建議

- 無特別建議，執行順利
```

## 彙總數據

### weekly.md

週報格式：

```markdown
# 週報：2026-01-18 至 2026-01-24

## 本週執行統計

| 指標 | 本週 | 上週 | 變化 |
|------|------|------|------|
| 工作流數 | 8 | 6 | +33% |
| 平均耗時 | 42 分鐘 | 48 分鐘 | -12% |
| 一次通過率 | 75% | 60% | +15pp |
| 平均回退 | 0.5 | 0.8 | -38% |

## 常見問題 Top 5

1. 測試覆蓋不足 (3 次)
2. 安全漏洞 (2 次)
3. 效能問題 (2 次)
4. 文檔缺失 (1 次)
5. API 設計問題 (1 次)

## 趨勢分析

- 耗時持續下降，效率提升
- 一次通過率穩定上升
- 安全相關問題需要關注
```

### trends.yaml

趨勢追蹤數據：

```yaml
# .claude/memory/metrics/summary/trends.yaml

last_updated: "2026-01-24T12:00:00Z"

# 最近 10 次執行
recent_executions:
  - workflow_id: "abc123"
    date: "2026-01-24"
    duration_sec: 2700
    rollbacks: 0
    first_pass: true
    issues: 5

  - workflow_id: "xyz789"
    date: "2026-01-23"
    duration_sec: 3200
    rollbacks: 1
    first_pass: false
    issues: 8
  # ... 更多

# 滾動平均
rolling_averages:
  duration_sec: 2850
  rollbacks: 0.3
  first_pass_rate: 0.7
  issues: 6.2

# 週度趨勢
weekly_trends:
  - week: "2026-W04"
    avg_duration: 2700
    avg_rollbacks: 0.5
    first_pass_rate: 0.75
    total_workflows: 8

  - week: "2026-W03"
    avg_duration: 2880
    avg_rollbacks: 0.8
    first_pass_rate: 0.6
    total_workflows: 6
```

### baseline.yaml

基準線數據：

```yaml
# .claude/memory/metrics/summary/baseline.yaml

version: 1
created: "2026-01-15T10:00:00Z"
last_updated: "2026-01-24T12:00:00Z"
sample_size: 10

baseline:
  duration_sec:
    average: 2850
    p50: 2700
    p90: 3500

  rollback_count:
    average: 0.3
    p50: 0
    p90: 1

  first_pass_rate: 0.7

  issues:
    average: 6.2
    by_severity:
      blocker: 0.1
      high: 0.8
      medium: 2.3
      low: 3.0

  false_positive_rate: 0.08

# 目標值
targets:
  duration_sec: 2400      # 減少 20%
  rollback_count: 0.2     # 減少 33%
  first_pass_rate: 0.85   # 增加 15pp
  false_positive_rate: 0.10
```

## 檔案命名規則

### workflow-id 格式

```
{timestamp}-{task-slug}
例如：20260124-user-auth
```

### 自動清理

- 保留最近 30 天的單次報告
- 保留最近 12 週的週報
- 趨勢數據保留最近 100 次執行

## 相關模組

- [指標 Schema](./schema.yaml)
- [收集器](./collector.md)
- [單次報告](../reporting/single-report.md)
- [週報](../reporting/weekly-report.md)
- [基準線](../reporting/baseline.md)
