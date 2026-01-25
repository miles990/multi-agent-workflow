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

### 1. 分層讀取策略（推薦）

```javascript
// 只讀取每個報告的前 100 行（包含 Executive Summary + Core Findings）
for (perspective of perspectives) {
  const summary = Read(perspectivePath, { limit: 100 });
  summaries.push(summary);
}

// 如需深入，再針對特定視角讀取更多
const details = Read(specificPath, { offset: 100, limit: 200 });
```

### 2. 使用 Grep 搜尋關鍵內容

```javascript
// 搜尋特定 section
Grep({
  pattern: "## Executive Summary|## Core Findings|## Cross-Reference",
  path: perspectivesDir
});
```

### 3. 啟動子 Agent 分段處理

```javascript
// 每個視角用獨立 Agent 處理，只收集匯總結果
Task({
  description: "匯總單一視角",
  prompt: `讀取 ${perspectivePath} 並產出 200 字摘要`,
  model: "haiku"
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
