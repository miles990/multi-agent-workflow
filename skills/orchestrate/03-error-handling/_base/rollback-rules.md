# 回退規則

> 工作流失敗時的自動回退與恢復機制

## 回退觸發條件

### REVIEW 階段回退

```yaml
review_rollback:
  trigger:
    condition: "review-summary.md contains BLOCKER"
    severity: "CRITICAL or HIGH"

  action:
    target_stage: IMPLEMENT
    data_to_pass:
      - blocker_list
      - suggested_fixes
      - affected_files

  message: |
    ⚠️ REVIEW 發現阻擋問題
    回退到 IMPLEMENT 進行修正
```

### VERIFY 階段回退

```yaml
verify_rollback:
  trigger:
    condition: "release-decision.md == BLOCKED"

  action:
    target_stage: IMPLEMENT
    data_to_pass:
      - failure_analysis
      - failed_tests
      - test_output

  message: |
    ⚠️ VERIFY 驗證失敗
    回退到 IMPLEMENT 進行修正
```

## 回退流程

### 標準回退

```
┌─────────────────────────────────────────────────────────────┐
│                     回退流程                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Step 1: 識別失敗                                            │
│  ┌──────────────────────────────────────┐                   │
│  │ 檢測到 BLOCKER / BLOCKED              │                   │
│  │ 記錄失敗原因和細節                    │                   │
│  └──────────────────────────────────────┘                   │
│      ↓                                                       │
│  Step 2: 準備回退數據                                        │
│  ┌──────────────────────────────────────┐                   │
│  │ 收集：                                │                   │
│  │   - 失敗原因                          │                   │
│  │   - 建議修正                          │                   │
│  │   - 相關檔案                          │                   │
│  └──────────────────────────────────────┘                   │
│      ↓                                                       │
│  Step 3: 更新狀態                                            │
│  ┌──────────────────────────────────────┐                   │
│  │ workflow.yaml:                        │                   │
│  │   - 增加迭代計數                      │                   │
│  │   - 記錄回退原因                      │                   │
│  │   - 更新當前階段                      │                   │
│  └──────────────────────────────────────┘                   │
│      ↓                                                       │
│  Step 4: 觸發目標階段                                        │
│  ┌──────────────────────────────────────┐                   │
│  │ 呼叫 /multi-implement                 │                   │
│  │ 傳入回退數據                          │                   │
│  │ 優先處理失敗項                        │                   │
│  └──────────────────────────────────────┘                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 回退數據格式

```yaml
rollback_data:
  source_stage: "REVIEW"
  target_stage: "IMPLEMENT"
  iteration: 2
  timestamp: "2025-01-24T14:30:00Z"

  failures:
    - type: "BLOCKER"
      category: "Security"
      description: "SQL injection vulnerability in login function"
      location: "src/auth/login.ts:45"
      suggested_fix: "Use parameterized queries"

    - type: "BLOCKER"
      category: "TDD"
      description: "Missing test for edge case"
      location: "src/auth/login.ts:60"
      suggested_fix: "Add test for empty password"

  affected_files:
    - "src/auth/login.ts"
    - "src/auth/login.test.ts"

  priority_order:
    1: "Fix SQL injection"
    2: "Add missing test"
```

## 回退限制

### 最大迭代次數

```yaml
max_iterations:
  default: 3
  configurable: true
  flag: "--max-iterations N"

  on_exceed:
    action: pause_and_notify
    message: |
      ⚠️ 已達回退上限（{max} 次）

      迭代歷史：
      {iteration_history}

      請人工審查後使用以下命令繼續：
      /multi-orchestrate --resume {id}

    options:
      - "手動修正後繼續"
      - "調整計劃後重新開始"
      - "放棄此工作流"
```

### 禁用回退

```yaml
no_rollback:
  flag: "--no-rollback"

  behavior:
    on_failure:
      action: stop_immediately
      message: |
        ❌ 工作流失敗（回退已禁用）

        失敗階段：{stage}
        失敗原因：{reason}

        請手動處理後重新執行。
```

## 回退策略

### 增量修正

```yaml
incremental_fix:
  description: "每次只修正一個問題"

  use_when:
    - multiple_blockers
    - blockers_may_be_related

  implementation:
    1. sort_blockers_by_priority
    2. fix_highest_priority
    3. re_run_review
    4. if_still_blocked: repeat
```

### 批次修正

```yaml
batch_fix:
  description: "一次修正所有問題"

  use_when:
    - blockers_are_independent
    - time_is_critical

  implementation:
    1. collect_all_blockers
    2. fix_all_in_parallel
    3. re_run_review
```

### 策略選擇

```yaml
strategy_selection:
  default: incremental

  auto_switch_to_batch:
    if:
      - blockers_count <= 3
      - blockers_are_in_different_files
      - no_dependency_between_fixes
```

## 迭代追蹤

### 迭代歷史

```yaml
iteration_history:
  format:
    iteration: 1
    stages_executed: ["PLAN", "IMPLEMENT", "REVIEW"]
    outcome: "rollback"
    reason: "BLOCKER: SQL injection"
    duration: "45m"
    files_changed: 12

  storage:
    file: "workflows/{id}/workflow.yaml"
    section: "iterations"
```

### 迭代報告

```markdown
## 迭代歷史

### 迭代 1
- **階段**：PLAN → IMPLEMENT → REVIEW
- **結果**：回退
- **原因**：Security BLOCKER - SQL injection
- **時長**：45 分鐘

### 迭代 2
- **階段**：IMPLEMENT → REVIEW
- **結果**：回退
- **原因**：TDD BLOCKER - Missing tests
- **時長**：30 分鐘

### 迭代 3（當前）
- **階段**：IMPLEMENT → REVIEW → VERIFY
- **結果**：✅ SHIP IT
- **時長**：40 分鐘

**總計**：3 次迭代，115 分鐘
```

## 恢復機制

### 自動恢復

```yaml
auto_resume:
  trigger: "session restart"

  implementation:
    1. load_workflow_state: "workflows/{id}/workflow.yaml"
    2. check_current_stage
    3. check_pending_rollback
    4. resume_from_last_state
```

### 手動恢復

```bash
# 從中斷處恢復
/multi-orchestrate --resume {id}

# 強制從特定階段恢復
/multi-orchestrate --resume {id} --start-at implement

# 忽略之前的失敗，重新開始
/multi-orchestrate --resume {id} --fresh
```

## 錯誤分類

### 可恢復錯誤

```yaml
recoverable_errors:
  - code_issues:
      - compilation_error
      - test_failure
      - security_vulnerability
    action: rollback_and_fix

  - quality_issues:
      - code_smell
      - missing_documentation
    action: rollback_and_fix
```

### 不可恢復錯誤

```yaml
unrecoverable_errors:
  - infrastructure:
      - environment_unavailable
      - dependency_missing
    action: pause_and_notify

  - data_corruption:
      - workflow_state_corrupted
      - artifact_missing
    action: pause_and_notify
```

## Checkpoint 整合

### CP5 驗屍

```yaml
cp5_integration:
  trigger: rollback

  actions:
    - analyze_failure_root_cause
    - document_lessons_learned
    - update_memory_with_findings

  output:
    file: "workflows/{id}/postmortem-{iteration}.md"
    content:
      - failure_summary
      - root_cause
      - fix_applied
      - prevention_suggestions
```

## 相關資源

- [階段判斷](../../01-stage-detection/_base/auto-detect.md)
- [數據傳遞](../../02-data-flow/_base/stage-handoff.md)
- [evolve Checkpoint 整合](../../../../shared/integration/evolve-checkpoints.md)
