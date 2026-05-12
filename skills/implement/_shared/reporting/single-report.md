# 單次執行報告模組

> 生成每次工作流執行的詳細報告

## 概述

單次執行報告在工作流結束時自動生成，提供完整的執行分析和改善建議。

## 報告位置

```
.claude/memory/metrics/{workflow-id}/report.md
```

## 報告結構

### 1. 執行摘要

```markdown
# 工作流執行報告

**工作流 ID**: {workflow-id}
**任務**: {task-description}
**執行時間**: {started_at} - {ended_at}
**狀態**: {status}

## 執行摘要

| 指標 | 值 | 與基準線比較 |
|------|-----|-------------|
| 總耗時 | {duration} | {vs_baseline} |
| 回退次數 | {rollbacks} | {vs_baseline} |
| 一次通過 | {first_pass} | - |
| 發現問題 | {issues} | {vs_baseline} |
| pass@k | {k} | {vs_baseline} |
```

### 2. 階段耗時分布

```markdown
## 階段耗時分布

| 階段 | 耗時 | 佔比 | 視覺化 |
|------|------|------|--------|
| RESEARCH | {duration} | {percent}% | {bar} |
| PLAN | {duration} | {percent}% | {bar} |
| IMPLEMENT | {duration} | {percent}% | {bar} |
| REVIEW | {duration} | {percent}% | {bar} |
| VERIFY | {duration} | {percent}% | {bar} |

### 視覺化

```
RESEARCH   {bar}  {percent}%
PLAN       {bar}  {percent}%
IMPLEMENT  {bar}  {percent}%
REVIEW     {bar}  {percent}%
VERIFY     {bar}  {percent}%
```

### 階段詳情

#### RESEARCH
- 開始時間：{started_at}
- 結束時間：{ended_at}
- 視角數量：{perspectives_count}
- 成功率：{success_rate}%

[詳細視角報告...]
```

### 3. 迭代歷程

```markdown
## 迭代歷程

### 總覽

- 總迭代次數：{total_iterations}
- 回退次數：{rollback_count}
- 最終通過：第 {pass_at_k} 次嘗試

### 迭代詳情

| 迭代 | 階段流程 | 結果 | 原因 |
|------|----------|------|------|
| 1 | PLAN → IMPLEMENT → REVIEW | 回退 | BLOCKER: 安全漏洞 |
| 2 | IMPLEMENT → REVIEW → VERIFY | 通過 | - |

### 回退分析

**迭代 1 回退原因**：
- 觸發階段：REVIEW
- 問題類型：BLOCKER
- 具體問題：SQL 注入風險
- 修復方式：添加參數化查詢
```

### 4. 問題分布

```markdown
## 問題分布

### 嚴重度分布

| 嚴重度 | 數量 | 佔比 |
|--------|------|------|
| BLOCKER | {count} | {percent}% |
| HIGH | {count} | {percent}% |
| MEDIUM | {count} | {percent}% |
| LOW | {count} | {percent}% |

### 分類統計

| 分類 | 數量 | 主要來源 |
|------|------|----------|
| 安全 | {count} | security-auditor |
| 效能 | {count} | performance-optimizer |
| 測試 | {count} | tdd-enforcer |
| 維護性 | {count} | maintainer |

### 問題清單

#### BLOCKER (必須修正)

1. **[SEC-001] SQL 注入風險**
   - 檔案：`src/db/query.ts:45`
   - 視角：security-auditor
   - 狀態：已修正

#### HIGH (強烈建議)

1. **[PERF-001] O(n²) 複雜度**
   - 檔案：`src/utils/sort.ts:12`
   - 視角：performance-optimizer
   - 狀態：已修正

[更多問題...]
```

### 5. 視角統計

```markdown
## 視角統計

### 各視角表現

| 視角 | 總執行次數 | 成功率 | 平均耗時 | 發現問題 |
|------|-----------|--------|----------|----------|
| architecture | 2 | 100% | 2.5 分鐘 | 1 |
| security | 2 | 100% | 3.0 分鐘 | 2 |
| tdd-enforcer | 2 | 100% | 2.0 分鐘 | 1 |
| performance | 2 | 100% | 2.5 分鐘 | 1 |

### 視角貢獻度

按發現問題的影響排序：

1. **security-auditor** - 發現 1 個 BLOCKER
2. **performance-optimizer** - 發現 1 個 HIGH
3. **tdd-enforcer** - 發現 1 個 MEDIUM
4. **maintainer** - 發現 2 個 LOW
```

### 6. 改善建議

```markdown
## 改善建議

### 基於本次執行

| 優先級 | 建議 | 預期效果 |
|--------|------|----------|
| HIGH | 加強安全審查前置 | 減少回退 |
| MEDIUM | 優化 IMPLEMENT 階段 | 縮短耗時 |
| LOW | 增加測試覆蓋 | 提高品質 |

### 詳細建議

#### 1. 加強安全審查前置 (HIGH)

**問題**：安全問題導致回退，浪費時間。

**建議**：
- 在 PLAN 階段加入安全檢查清單
- IMPLEMENT 階段使用安全編碼模板

**預期效果**：減少安全相關回退 50%

#### 2. 優化 IMPLEMENT 階段 (MEDIUM)

**問題**：IMPLEMENT 耗時佔比過高 (45%)。

**建議**：
- 使用更細粒度的任務分解
- 考慮並行實作獨立模組

**預期效果**：縮短 IMPLEMENT 耗時 20%

### 與基準線對比

| 指標 | 本次 | 基準線 | 差異 | 評價 |
|------|------|--------|------|------|
| 總耗時 | 45 分鐘 | 48 分鐘 | -6% | 良好 |
| 回退次數 | 1 | 0.3 | +233% | 需改善 |
| 問題數 | 5 | 6.2 | -19% | 良好 |
```

## 報告生成邏輯

### 觸發時機

```yaml
trigger:
  event: end_workflow
  conditions:
    - workflow.status in [completed, failed]
```

### 生成步驟

1. **讀取 metrics.yaml**
   - 載入所有原始指標數據

2. **計算衍生指標**
   - 階段耗時佔比
   - 視角成功率
   - 問題分布

3. **載入基準線**
   - 讀取 `summary/baseline.yaml`
   - 計算與基準線的差異

4. **生成建議**
   - 基於規則引擎分析
   - 識別異常指標
   - 提供改善建議

5. **渲染報告**
   - 使用 Markdown 模板
   - 生成視覺化圖表
   - 輸出到 `report.md`

### 建議規則

```yaml
suggestion_rules:
  - name: security_rollback
    condition: "rollback.reason contains 'security'"
    priority: HIGH
    suggestion: "加強安全審查前置"
    expected_effect: "減少安全相關回退 50%"

  - name: long_implement
    condition: "implement.duration_percent > 0.4"
    priority: MEDIUM
    suggestion: "優化 IMPLEMENT 階段"
    expected_effect: "縮短 IMPLEMENT 耗時 20%"

  - name: high_rollback
    condition: "rollback_count > baseline.rollback_count * 1.5"
    priority: HIGH
    suggestion: "分析回退原因，加強前置檢查"
    expected_effect: "減少回退次數"

  - name: low_first_pass
    condition: "first_pass == false"
    priority: MEDIUM
    suggestion: "提升一次通過率"
    expected_effect: "減少迭代次數"
```

## 報告模板

### 完整模板

```markdown
# 工作流執行報告

**生成時間**: {{generated_at}}
**工作流 ID**: {{workflow_id}}

---

## 1. 執行摘要

{{> summary_section}}

## 2. 階段耗時分布

{{> duration_section}}

## 3. 迭代歷程

{{> iteration_section}}

## 4. 問題分布

{{> issues_section}}

## 5. 視角統計

{{> perspectives_section}}

## 6. 改善建議

{{> suggestions_section}}

---

*報告由 Multi-Agent Workflow 自動生成*
```

## 相關模組

- [指標收集器](../metrics/collector.md)
- [Memory 結構](../metrics/memory-structure.md)
- [週報模板](./weekly-report.md)
- [基準線機制](./baseline.md)
