# Metrics Collector 模組

> 標準化的指標收集 API，用於記錄工作流執行數據

## 概述

Metrics Collector 提供統一的 API 來收集工作流執行指標。所有 skill 使用相同的接口記錄數據，確保指標的一致性和可比較性。

## 存儲位置

```
.claude/memory/metrics/{workflow-id}/
├── metrics.yaml    ← 原始指標數據
└── report.md       ← 可讀報告（由報告模組生成）
```

## 收集 API

### 1. start_workflow

初始化工作流指標收集。

```yaml
# 調用時機：工作流開始時
# 調用位置：orchestrate/SKILL.md Phase 1

action: start_workflow
params:
  workflow_id: "{uuid}"
  task: "任務描述"
  started_at: "{ISO8601 timestamp}"

# 執行動作：
# 1. 建立目錄 .claude/memory/metrics/{workflow-id}/
# 2. 初始化 metrics.yaml：
#    workflow_id: {workflow_id}
#    task: {task}
#    started_at: {started_at}
#    status: running
#    stages: []
```

### 2. start_stage

開始記錄階段指標。

```yaml
# 調用時機：每個階段開始時
# 調用位置：各 SKILL.md Phase 開始處

action: start_stage
params:
  workflow_id: "{uuid}"
  stage_id: "research|plan|implement|review|verify"
  started_at: "{ISO8601 timestamp}"
  perspectives:
    - id: "{perspective_id}"
      name: "{perspective_name}"
      status: "pending"

# 執行動作：
# 1. 在 metrics.yaml 的 stages 陣列新增：
#    - stage_id: {stage_id}
#      started_at: {started_at}
#      status: running
#      perspectives: {perspectives}
#      execution: {}
#      quality: {}
#      efficiency: {}
```

### 3. record_agent

記錄單個 Agent 執行結果。

```yaml
# 調用時機：每個 Agent（視角）完成時
# 調用位置：各 SKILL.md MAP Phase 中

action: record_agent
params:
  workflow_id: "{uuid}"
  stage_id: "{stage_id}"
  perspective_id: "{perspective_id}"
  status: "completed|failed|skipped"
  duration_sec: {number}
  output_path: "{path to output file}"
  retry_count: {number}  # 可選，預設 0

# 執行動作：
# 1. 更新對應 perspective 的狀態和數據
# 2. 如果 status=failed，記錄失敗原因
```

### 4. record_issue

記錄發現的問題（用於 REVIEW/VERIFY）。

```yaml
# 調用時機：發現問題時
# 調用位置：review/SKILL.md, verify/SKILL.md

action: record_issue
params:
  workflow_id: "{uuid}"
  stage_id: "review|verify"
  issue:
    id: "{issue_id}"
    severity: "blocker|high|medium|low"
    category: "{category}"
    description: "{description}"
    file_path: "{affected file}"  # 可選
    line: {number}                # 可選
    is_false_positive: false      # 後續可標記

# 執行動作：
# 1. 將 issue 添加到 stage.quality.issues 陣列
# 2. 更新 by_severity 計數
```

### 5. record_iteration

記錄迭代資訊。

```yaml
# 調用時機：每次迭代完成時
# 調用位置：implement/SKILL.md, orchestrate/SKILL.md

action: record_iteration
params:
  workflow_id: "{uuid}"
  iteration: {number}
  result: "pass|fail"
  rollback: false  # 是否觸發回退
  reason: "{description}"  # 可選

# 執行動作：
# 1. 更新 efficiency.total_iterations
# 2. 如果 result=pass，設置 pass_at_k.k = iteration
# 3. 如果 rollback=true，增加 rollback_count
```

### 6. end_stage

結束階段指標收集。

```yaml
# 調用時機：每個階段結束時
# 調用位置：各 SKILL.md Phase 結束處

action: end_stage
params:
  workflow_id: "{uuid}"
  stage_id: "{stage_id}"
  ended_at: "{ISO8601 timestamp}"
  status: "completed|failed"

# 執行動作：
# 1. 計算 duration_sec = ended_at - started_at
# 2. 計算 agent_success_rate
# 3. 設置 first_pass_success（如果是第一次執行）
# 4. 更新 stage status
```

### 7. end_workflow

結束工作流指標收集並生成報告。

```yaml
# 調用時機：工作流結束時
# 調用位置：orchestrate/SKILL.md 最後

action: end_workflow
params:
  workflow_id: "{uuid}"
  ended_at: "{ISO8601 timestamp}"
  status: "completed|failed|cancelled"

# 執行動作：
# 1. 計算 total_duration_sec
# 2. 彙總所有階段指標到 summary
# 3. 觸發報告生成（見 reporting/single-report.md）
# 4. 更新趨勢數據（見 reporting/baseline.md）
```

## 指標文件格式

### metrics.yaml 範例

```yaml
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
        name: 架構分析師
        status: completed
        duration_sec: 120
        output_path: ".claude/memory/research/auth/perspectives/architecture.md"
      - id: security
        name: 安全專家
        status: completed
        duration_sec: 115
        output_path: ".claude/memory/research/auth/perspectives/security.md"
    execution:
      agent_success_rate: 100
      retry_count: 0
    efficiency:
      first_pass_success: true

  - stage_id: review
    started_at: "2026-01-24T10:30:00Z"
    ended_at: "2026-01-24T10:40:00Z"
    duration_sec: 600
    status: completed
    quality:
      issues_found: 5
      by_severity:
        blocker: 0
        high: 1
        medium: 2
        low: 2
      false_positive_rate: 0
    efficiency:
      total_iterations: 1
      rollback_count: 0

summary:
  total_agents: 16
  successful_agents: 16
  total_issues: 5
  blockers: 0
  total_rollbacks: 0
  final_pass_at_k: 1
```

## 使用範例

### 在 SKILL.md 中嵌入收集點

```markdown
## Phase 1: 初始化

<!-- METRICS: start_stage -->
開始 {stage_id} 階段，記錄開始時間。

...執行階段邏輯...

<!-- METRICS: record_agent -->
每個視角完成時，記錄執行結果。

## Phase N: 結束

<!-- METRICS: end_stage -->
階段完成，記錄結束時間和彙總數據。
```

## 收集點標記說明

在 SKILL.md 中使用以下標記來標示收集點：

| 標記 | 說明 | 參數 |
|------|------|------|
| `<!-- METRICS: start_stage -->` | 階段開始 | stage_id, perspectives |
| `<!-- METRICS: record_agent -->` | Agent 完成 | perspective_id, status, duration |
| `<!-- METRICS: record_issue -->` | 發現問題 | severity, description |
| `<!-- METRICS: record_iteration -->` | 迭代完成 | iteration, result |
| `<!-- METRICS: end_stage -->` | 階段結束 | status |

## 相關模組

- [指標 Schema](./schema.yaml) - 指標定義
- [單次報告](../reporting/single-report.md) - 報告生成
- [基準線](../reporting/baseline.md) - 趨勢追蹤
