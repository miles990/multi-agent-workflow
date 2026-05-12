# 週報/趨勢報告模組

> 追蹤長期趨勢，提供持續改善洞察

## 概述

週報自動彙總過去一週的工作流執行數據，與歷史趨勢對比，識別改善機會。

## 報告位置

```
.claude/memory/metrics/summary/weekly.md
```

## 生成週期

- **生成時間**：每週日 23:59 或首次執行時
- **保留期限**：最近 12 週
- **歷史存檔**：`summary/archive/weekly-{YYYY-Www}.md`

## 週報結構

### 1. 週度摘要

```markdown
# 週報：{start_date} 至 {end_date}

**報告週次**: {YYYY}-W{ww}
**生成時間**: {generated_at}

## 本週摘要

| 指標 | 本週 | 上週 | 變化 | 趨勢 |
|------|------|------|------|------|
| 工作流執行數 | {count} | {prev_count} | {change}% | {trend_icon} |
| 平均總耗時 | {duration} | {prev_duration} | {change}% | {trend_icon} |
| 一次通過率 | {rate}% | {prev_rate}% | {change}pp | {trend_icon} |
| 平均回退次數 | {rollbacks} | {prev_rollbacks} | {change}% | {trend_icon} |
| 總發現問題 | {issues} | {prev_issues} | {change}% | {trend_icon} |
| BLOCKER 問題 | {blockers} | {prev_blockers} | {change}% | {trend_icon} |

### 趨勢圖示說明
- 上升：改善中
- 下降：需關注
- 持平：穩定
```

### 2. 工作流清單

```markdown
## 本週工作流

| # | 日期 | 任務 | 耗時 | 回退 | 結果 |
|---|------|------|------|------|------|
| 1 | 01/24 | 用戶認證功能 | 45 分鐘 | 1 | SHIP IT |
| 2 | 01/23 | API 重構 | 60 分鐘 | 0 | SHIP IT |
| 3 | 01/22 | 購物車功能 | 35 分鐘 | 0 | SHIP IT |
| ... | ... | ... | ... | ... | ... |

### 統計
- 成功完成：{success_count} ({success_rate}%)
- 失敗/中止：{failed_count} ({failed_rate}%)
```

### 3. 階段分析

```markdown
## 階段耗時分析

### 平均耗時分布

| 階段 | 平均耗時 | 佔比 | vs 上週 |
|------|----------|------|---------|
| RESEARCH | {duration} | {percent}% | {change} |
| PLAN | {duration} | {percent}% | {change} |
| IMPLEMENT | {duration} | {percent}% | {change} |
| REVIEW | {duration} | {percent}% | {change} |
| VERIFY | {duration} | {percent}% | {change} |

### 階段成功率

| 階段 | 成功率 | vs 上週 | 備註 |
|------|--------|---------|------|
| RESEARCH | {rate}% | {change} | {note} |
| PLAN | {rate}% | {change} | {note} |
| IMPLEMENT | {rate}% | {change} | {note} |
| REVIEW | {rate}% | {change} | {note} |
| VERIFY | {rate}% | {change} | {note} |

### 瓶頸識別

本週耗時最長的階段：**{bottleneck_stage}**
- 平均耗時：{duration}
- 佔總耗時：{percent}%
- 建議：{suggestion}
```

### 4. 問題分析

```markdown
## 問題分析

### 嚴重度分布

| 嚴重度 | 本週 | 上週 | 變化 |
|--------|------|------|------|
| BLOCKER | {count} | {prev} | {change} |
| HIGH | {count} | {prev} | {change} |
| MEDIUM | {count} | {prev} | {change} |
| LOW | {count} | {prev} | {change} |

### 常見問題 Top 5

| 排名 | 問題類型 | 出現次數 | 主要來源 |
|------|----------|----------|----------|
| 1 | {issue_type} | {count} | {source} |
| 2 | {issue_type} | {count} | {source} |
| 3 | {issue_type} | {count} | {source} |
| 4 | {issue_type} | {count} | {source} |
| 5 | {issue_type} | {count} | {source} |

### 問題熱點

最常出現問題的檔案/模組：

1. `src/api/auth.ts` - 3 個問題（安全相關）
2. `src/utils/validation.ts` - 2 個問題（邊界案例）
3. `src/db/query.ts` - 2 個問題（效能相關）

### 誤報分析

- 本週誤報數：{false_positives}
- 誤報率：{rate}%
- vs 上週：{change}
- 主要誤報來源：{source}
```

### 5. 視角表現

```markdown
## 視角表現分析

### 各視角統計

| 視角 | 執行次數 | 成功率 | 平均耗時 | 發現問題 |
|------|----------|--------|----------|----------|
| architecture | {count} | {rate}% | {duration} | {issues} |
| security | {count} | {rate}% | {duration} | {issues} |
| tdd-enforcer | {count} | {rate}% | {duration} | {issues} |
| performance | {count} | {rate}% | {duration} | {issues} |
| ... | ... | ... | ... | ... |

### 視角效益排名

按發現有效問題數排序：

1. **security-auditor** - {issues} 個問題（{blockers} BLOCKER）
2. **tdd-enforcer** - {issues} 個問題
3. **performance-optimizer** - {issues} 個問題
4. **maintainer** - {issues} 個問題

### 視角建議

- **建議增加**：{perspective}（本週未使用但可能有幫助）
- **建議調優**：{perspective}（執行慢或誤報高）
```

### 6. 趨勢分析

```markdown
## 趨勢分析

### 近 4 週趨勢

| 週次 | 執行數 | 平均耗時 | 一次通過率 | 平均回退 |
|------|--------|----------|------------|----------|
| W04 | {count} | {duration} | {rate}% | {rollbacks} |
| W03 | {count} | {duration} | {rate}% | {rollbacks} |
| W02 | {count} | {duration} | {rate}% | {rollbacks} |
| W01 | {count} | {duration} | {rate}% | {rollbacks} |

### 趨勢圖

```
一次通過率趨勢
100% ┤
 80% ┤      ╭──────╮
 60% ┤   ╭──╯      ╰──╮
 40% ┤───╯            ╰───
 20% ┤
  0% ┼────┬────┬────┬────
     W01  W02  W03  W04
```

### 趨勢解讀

**正面趨勢**：
- 一次通過率持續上升（W01: 50% → W04: 75%）
- 平均耗時穩定下降

**需關注**：
- BLOCKER 問題數量上升
- 安全相關問題增加
```

### 7. 改善建議

```markdown
## 本週改善建議

### 優先處理

| 優先級 | 建議 | 依據 | 預期效果 |
|--------|------|------|----------|
| HIGH | 加強安全審查 | BLOCKER 增加 50% | 減少回退 |
| HIGH | 優化 IMPLEMENT 階段 | 佔比 45% | 縮短耗時 |
| MEDIUM | 增加測試覆蓋 | 邊界問題頻繁 | 提高品質 |

### 詳細建議

#### 1. 加強安全審查 (HIGH)

**問題**：本週安全相關 BLOCKER 增加 50%。

**分析**：
- 主要集中在 API 認證模組
- 常見問題：SQL 注入、XSS

**建議行動**：
1. 在 PLAN 階段加入安全檢查清單
2. 使用安全編碼模板
3. 考慮添加 security-first 視角

**預期效果**：減少安全相關回退 50%

#### 2. 優化 IMPLEMENT 階段 (HIGH)

**問題**：IMPLEMENT 階段佔總耗時 45%，高於基準線 35%。

**分析**：
- 任務分解粒度過粗
- 依賴關係導致串行執行

**建議行動**：
1. 使用更細粒度的任務分解
2. 識別可並行的任務
3. 加強前置依賴分析

**預期效果**：縮短 IMPLEMENT 耗時 20%

### 下週目標

基於本週分析，建議下週目標：

| 指標 | 本週值 | 目標值 | 改善幅度 |
|------|--------|--------|----------|
| 一次通過率 | 75% | 80% | +5pp |
| 平均回退 | 0.5 | 0.3 | -40% |
| BLOCKER 數 | 3 | 2 | -33% |
```

## 趨勢數據格式

### trends.yaml

```yaml
# .claude/memory/metrics/summary/trends.yaml

last_updated: "2026-01-24T23:59:00Z"

# 最近執行記錄
recent_executions:
  - workflow_id: "abc123"
    date: "2026-01-24"
    duration_sec: 2700
    rollbacks: 1
    first_pass: false
    issues: 5
    blockers: 0
  # ... 最多 100 條

# 週度彙總
weekly_summaries:
  - week: "2026-W04"
    start_date: "2026-01-20"
    end_date: "2026-01-26"
    workflow_count: 8
    avg_duration_sec: 2700
    avg_rollbacks: 0.5
    first_pass_rate: 0.75
    total_issues: 42
    total_blockers: 3

  - week: "2026-W03"
    # ... 類似結構

# 滾動平均（最近 10 次）
rolling_10:
  duration_sec: 2850
  rollbacks: 0.4
  first_pass_rate: 0.7
  issues: 5.5

# 趨勢指標
trends:
  duration:
    direction: "decreasing"  # increasing, decreasing, stable
    change_rate: -0.05       # 週環比變化率

  first_pass_rate:
    direction: "increasing"
    change_rate: 0.08

  rollbacks:
    direction: "decreasing"
    change_rate: -0.15
```

## 生成邏輯

### 觸發條件

```yaml
trigger:
  schedule: "0 23 * * 0"  # 每週日 23:00
  on_demand: true          # 支援手動觸發
```

### 生成步驟

1. **收集本週數據**
   - 掃描 `metrics/{workflow-id}/` 目錄
   - 篩選本週日期範圍內的執行

2. **計算統計**
   - 彙總各項指標
   - 計算平均值、佔比

3. **載入歷史數據**
   - 讀取 `trends.yaml`
   - 獲取上週數據進行對比

4. **分析趨勢**
   - 計算週環比變化
   - 識別異常指標
   - 生成趨勢圖示

5. **生成建議**
   - 基於規則引擎
   - 結合歷史趨勢
   - 設定下週目標

6. **更新 trends.yaml**
   - 添加本週彙總
   - 更新滾動平均
   - 更新趨勢指標

7. **渲染報告**
   - 輸出到 `weekly.md`
   - 存檔到 `archive/`

## 相關模組

- [單次報告](./single-report.md)
- [基準線機制](./baseline.md)
- [Memory 結構](../metrics/memory-structure.md)
