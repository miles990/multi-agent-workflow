# E-RED-001: File content exceeds maximum allowed tokens

## 錯誤訊息

```
Error: File content (47859 tokens) exceeds maximum allowed tokens (25000).
Please use offset and limit parameters to read specific portions of the file,
or use the GrepTool to search for specific content.
```

## 原因

在 REDUCE 階段嘗試讀取所有視角報告進行匯總時，檔案內容總量超過了 25000 tokens 的限制。

常見場景：
- 4 個視角報告，每個約 12000 tokens = 48000 tokens
- 深度研究模式產出較長的報告

## 解決方案

### ✅ 推薦：並行子 Agent 完整處理（確保完整性）

**原理**：每個視角報告由獨立子 Agent **完整讀取**，產出結構化摘要，主 Agent 收集摘要進行最終匯總。

**優點**：
- ✅ 每個視角都被**完整處理**，不遺漏任何內容
- ✅ 保證高品質和正確性
- ✅ 子 Agent 各自有獨立 context，不受 25000 tokens 限制

```javascript
// 1. 並行啟動子 Agent（每個完整讀取一份報告）
const tasks = perspectives.map(p => Task({
  description: `提取 ${p.name} 視角摘要`,
  prompt: `
    完整讀取 ${p.reportPath}，產出結構化摘要（YAML 格式）：
    - executive_summary: 2-3 句話
    - core_findings: 列出所有核心發現 + 證據
    - unique_insights: 此視角獨特的洞察（不可遺漏）
    - cross_reference: 共識點、衝突點
  `,
  subagent_type: 'general-purpose',
  model: 'haiku'
}));

// 2. 收集所有摘要（每份約 1000 tokens）
const summaries = await Promise.all(tasks);

// 3. 主 Agent 基於完整摘要進行交叉驗證和匯總
```

### 備選：分層讀取（僅適用於簡單場景）

⚠️ **注意**：此方法可能遺漏詳細分析中的重要內容，僅適用於 `--quick` 模式。

```javascript
// 只讀取每個報告的前 100 行
for (perspective of perspectives) {
  const summary = Read(perspectivePath, { limit: 100 });
  summaries.push(summary);
}
```

### 備選：Grep 搜尋關鍵內容

```javascript
// 搜尋特定 section
Grep({
  pattern: "## Executive Summary|## Core Findings|## Cross-Reference",
  path: perspectivesDir
});
```

## 預防措施

### Map Phase 階段

在 Agent Prompt 中加入長度限制：

```markdown
### 輸出要求
請產出一份結構化報告，**總長度不超過 300 行**（約 5000 tokens）
```

### 報告模板

使用優化後的模板結構，確保關鍵資訊在前 100 行內：

1. Metadata（前 15 行）
2. Executive Summary + Key Takeaways（第 16-30 行）
3. Core Findings（第 31-80 行）
4. Cross-Reference Notes（第 81-100 行）
5. 詳細內容（第 100 行以後，可選讀取）

## 相關文件

- [reduce-phase.md](../../shared/coordination/reduce-phase.md) - 大檔案處理策略
- [map-phase.md](../../shared/coordination/map-phase.md) - 報告長度限制
- [perspective-report.md](../../skills/research/templates/perspective-report.md) - 報告模板

## 版本

- 新增於 v2.4.0
- 最後更新：2026-01-26
