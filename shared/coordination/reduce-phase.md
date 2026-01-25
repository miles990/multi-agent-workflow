# Reduce Phase（共用模組）

> 匯總整合階段：將多視角成果整合為統一輸出

## 概述

Reduce Phase 負責：
1. 收集所有視角報告
2. 識別共識與矛盾
3. 解決矛盾
4. 生成匯總報告

**此為共用模組**，各 skill 根據需求配置整合策略。

## 執行流程

```
┌─────────────────────────────────────────────────────────────────┐
│  收集階段                                                        │
│  • 等待所有 Map Agent 完成                                       │
│  • 讀取所有視角報告                                              │
│  • 建立發現索引                                                  │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│  交叉驗證（引用 synthesis/cross-validation.md）                  │
│  • 識別共識點（多視角同意）                                      │
│  • 識別矛盾點（視角衝突）                                        │
│  • 識別獨特洞察（單一視角發現）                                  │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│  矛盾解決（引用 synthesis/conflict-resolution.md）               │
│  • 分析矛盾原因                                                  │
│  • 多輪比較分析                                                  │
│  • 產出解決方案或標記「需進一步處理」                            │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│  報告生成                                                        │
│  • 匯總所有發現                                                  │
│  • 組織成結構化報告                                              │
│  • 產出行動建議                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 收集階段

### 從檔案讀取視角報告

**重要**：視角報告應已保存在檔案中（由 Map Phase 負責）。

```
讀取路徑：
.claude/memory/{type}/{id}/perspectives/*.md

範例：
Read → .claude/memory/research/user-auth/perspectives/architecture.md
Read → .claude/memory/research/user-auth/perspectives/cognitive.md
Read → .claude/memory/research/user-auth/perspectives/workflow.md
Read → .claude/memory/research/user-auth/perspectives/industry.md
```

如果視角報告檔案不存在，表示 Map Phase 未正確保存，應該報錯。

### ⚠️ 大檔案處理策略

**問題**：多個視角報告合併後可能超過 25000 tokens 限制。

**解決方案**：分層讀取策略

```
第一層：只讀摘要（每個報告前 100 行）
────────────────────────────────────────
Read(file, limit=100) → 獲取 Executive Summary + Core Findings

第二層：按需深入
────────────────────────────────────────
如果某視角需要更多細節，再讀取該視角的完整內容

第三層：並行處理（如仍超限）
────────────────────────────────────────
啟動子 Agent 分別處理每個視角，只收集匯總結果
```

**實作指引**：

```javascript
// 1. 先收集所有視角的摘要
for (perspective of perspectives) {
  // 只讀前 100 行（約 2000-3000 tokens）
  const summary = Read(perspectivePath, { limit: 100 });
  summaries.push({ id: perspective, content: summary });
}

// 2. 從摘要中提取關鍵資訊進行交叉驗證
// 關鍵 sections：Executive Summary, Core Findings, Cross-Reference Notes

// 3. 如需深入某視角，使用 offset 讀取
const details = Read(specificPath, { offset: 100, limit: 200 });
```

**Token 預算分配**（總預算 20000 tokens）：

| 用途 | 配額 | 說明 |
|-----|------|------|
| 視角摘要 | 12000 | 4 視角 × 3000 tokens |
| 交叉驗證分析 | 4000 | 識別共識/矛盾 |
| 匯總報告生成 | 4000 | 產出最終報告 |

**降級策略**：

如果視角報告總量仍超過預算：
1. 只使用 Executive Summary 和 Core Findings
2. 使用 Grep 搜尋特定關鍵字而非完整讀取
3. 啟動獨立 Agent 進行分段匯總

### 報告格式標準化

每份視角報告應包含：

```markdown
## 核心發現/建議
- 項目 1
- 項目 2
- ...

## 詳細分析
...

## 建議
...

## 信心度
高 / 中 / 低
```

### 建立發現索引

```javascript
// 概念示意
const findingsIndex = {
  consensus: [],      // 多視角同意的發現
  conflicts: [],      // 視角間的矛盾
  unique: [],         // 單一視角的獨特洞察
  uncertain: []       // 信心度低的發現
}
```

## 整合策略配置

各 skill 可配置不同的整合策略：

### research skill

```yaml
reduce_config:
  strategy: synthesis
  output:
    primary: synthesis.md
    secondary: overview.md
  consensus_threshold: 0.75    # 3/4 視角同意
```

### plan skill

```yaml
reduce_config:
  strategy: design_consensus
  output:
    primary: implementation-plan.md
    secondary: milestones.md
  priority: risk_first         # 優先處理風險相關發現
```

### review skill

```yaml
reduce_config:
  strategy: issue_classification
  output:
    primary: review-summary.md
  severity_levels: [BLOCKER, HIGH, MEDIUM, LOW]
  deduplicate: true
```

### verify skill

```yaml
reduce_config:
  strategy: pass_fail
  output:
    primary: release-decision.md
  pass_criteria:
    functional: 1.0            # 100% 通過
    edge_case: 0.9             # 90% 通過
    regression: 1.0            # 100% 通過
```

## 報告生成

### 通用匯總報告結構

```markdown
# {主題} - 匯總報告

## 摘要
一段話總結關鍵發現

## 方法
- 視角：{列表}
- 日期：{日期}
- 模式：{quick/normal/deep}

## 共識發現
### 強共識
- 發現 1：...（4/4 視角同意）

### 弱共識
- 發現 2：...（2/4 視角同意）

## 矛盾分析
### 已解決
- 矛盾 1：{描述} → {解決方案}

### 需進一步處理
- 矛盾 2：{描述} → {建議方向}

## 關鍵洞察
整合所有視角後的深層發現

## 行動建議
1. 立即行動：...
2. 短期規劃：...
3. 長期考量：...

## 附錄
各視角完整報告連結
```

## 品質檢查

### 報告品質標準

- [ ] 摘要準確反映核心發現
- [ ] 共識有明確的視角支持
- [ ] 矛盾有清楚的分析
- [ ] 行動建議具體可執行

### 完整性檢查

- [ ] 所有視角報告都已納入
- [ ] 沒有遺漏重要發現
- [ ] 矛盾都有處理（解決或標記）

## 配置參數

```yaml
reduce_config:
  strategy: synthesis | design_consensus | issue_classification | pass_fail
  cross_validation:
    enabled: true
    consensus_threshold: 0.75
  conflict_resolution:
    enabled: true
    max_rounds: 3
  output:
    primary: string             # 主輸出檔案
    secondary: string           # 次要輸出檔案（可選）
  quality_check:
    enabled: true
```

## 相關模組

- [cross-validation.md](../synthesis/cross-validation.md) - 交叉驗證邏輯
- [conflict-resolution.md](../synthesis/conflict-resolution.md) - 矛盾解決邏輯
