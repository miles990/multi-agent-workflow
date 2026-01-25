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

**核心原則**：**完整性優先** — 每個視角的完整內容都必須被處理，不可遺漏。

---

#### 策略選擇流程

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: 評估總量                                                 │
│ 檢查所有視角報告的總行數/大小                                    │
└─────────────────────────────────────────────────────────────────┘
         ↓
    總量 < 500 行？
         ↓
    ┌────┴────┐
    是        否
    ↓         ↓
┌────────┐  ┌────────────────────────────────────────────────────┐
│ 策略 A │  │ 策略 B: 並行子 Agent 完整處理（推薦）               │
│ 直接讀 │  │ 每個視角由獨立 Agent 完整讀取並產出結構化摘要       │
└────────┘  └────────────────────────────────────────────────────┘
```

---

#### 策略 A：直接讀取（小檔案，總量 < 500 行）

```javascript
// 所有報告一次讀取
for (perspective of perspectives) {
  const content = Read(perspectivePath);
  reports.push({ id: perspective, content });
}
// 直接進行交叉驗證和匯總
```

---

#### 策略 B：並行子 Agent 完整處理（推薦，確保完整性）

**原理**：每個視角報告由獨立子 Agent **完整讀取**，產出結構化摘要，主 Agent 收集摘要進行最終匯總。

```
┌─────────────────────────────────────────────────────────────────┐
│ 並行啟動 4 個子 Agent                                            │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Agent A  │  │ Agent B  │  │ Agent C  │  │ Agent D  │        │
│  │ 架構視角 │  │ 認知視角 │  │ 工作流   │  │ 業界實踐 │        │
│  │          │  │          │  │          │  │          │        │
│  │ 完整讀取 │  │ 完整讀取 │  │ 完整讀取 │  │ 完整讀取 │        │
│  │ 報告     │  │ 報告     │  │ 報告     │  │ 報告     │        │
│  │    ↓     │  │    ↓     │  │    ↓     │  │    ↓     │        │
│  │ 產出結構 │  │ 產出結構 │  │ 產出結構 │  │ 產出結構 │        │
│  │ 化摘要   │  │ 化摘要   │  │ 化摘要   │  │ 化摘要   │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       └──────────────┴──────────────┴──────────────┘            │
│                              ↓                                   │
│                    收集 4 份結構化摘要                           │
│                              ↓                                   │
│                    主 Agent 進行匯總                            │
└─────────────────────────────────────────────────────────────────┘
```

**子 Agent Prompt 模板**：

```markdown
## 任務：視角報告摘要提取

請完整讀取以下視角報告，並產出**結構化摘要**。

### 報告路徑
{perspective_report_path}

### 輸出格式（必須遵循）

```yaml
perspective_id: {id}
confidence: high | medium | low

executive_summary: |
  {2-3 句話總結此視角的核心觀點}

core_findings:
  - finding: {發現 1}
    evidence: {關鍵證據}
    confidence: {★★★★ | ★★★ | ★★ | ★}
  - finding: {發現 2}
    evidence: {關鍵證據}
    confidence: {★★★★ | ★★★ | ★★ | ★}
  - finding: {發現 3}
    evidence: {關鍵證據}
    confidence: {★★★★ | ★★★ | ★★ | ★}

key_recommendations:
  - {建議 1}
  - {建議 2}

risks:
  - {風險 1}
  - {風險 2}

cross_reference:
  consensus_points:
    - {可能與其他視角一致的點}
  potential_conflicts:
    - {可能與其他視角衝突的點}
  unique_insights:
    - {此視角獨特的洞察，不可遺漏}
```

### 重要
- 必須**完整閱讀**報告後再摘要
- 不可遺漏任何**核心發現**或**獨特洞察**
- unique_insights 特別重要，這些是其他視角可能沒有的觀點
```

**主 Agent 匯總流程**：

```javascript
// 1. 並行啟動子 Agent
const extractionTasks = perspectives.map(p => Task({
  description: `提取 ${p.name} 視角摘要`,
  prompt: generateExtractionPrompt(p.reportPath),
  subagent_type: 'general-purpose',
  model: 'haiku'  // 摘要提取用快速模型
}));

// 2. 收集結構化摘要
const summaries = await Promise.all(extractionTasks);

// 3. 解析 YAML 摘要
const parsedSummaries = summaries.map(parseYAML);

// 4. 進行交叉驗證（基於完整摘要）
const crossValidation = analyzeCrossReferences(parsedSummaries);

// 5. 產出最終匯總報告
generateSynthesisReport(parsedSummaries, crossValidation);
```

---

#### 品質保證機制

| 檢查點 | 驗證內容 | 失敗處理 |
|-------|---------|---------|
| 摘要完整性 | 每個摘要都有 core_findings 和 unique_insights | 重新執行該視角的提取 |
| 交叉引用 | consensus_points 和 potential_conflicts 已標記 | 手動檢查視角間關係 |
| 信心度一致性 | 高信心度發現有足夠證據 | 降級或標記待確認 |

---

#### Token 預算分配（策略 B）

| 階段 | 用途 | 說明 |
|-----|------|------|
| 子 Agent（×4） | 各自獨立 context | 每個 Agent 完整讀取一份報告 |
| 主 Agent | 收集 4 份摘要 | 約 4000 tokens（4 × 1000） |
| 主 Agent | 交叉驗證 + 匯總 | 約 6000 tokens |

**優勢**：每個視角都被**完整處理**，不會因為 token 限制而遺漏重要內容。

---

#### 何時使用哪個策略

| 情況 | 策略 | 原因 |
|-----|------|------|
| 4 個視角，每個 < 150 行 | A | 總量小，直接讀取 |
| 4 個視角，每個 > 150 行 | B | 超限風險，用子 Agent |
| 深度研究（--deep） | B | 報告通常較長 |
| 快速研究（--quick） | A | 報告較短 |

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
