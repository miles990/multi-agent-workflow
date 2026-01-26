# 視角模組（Perspectives）

> 多視角配置與角色定義

## 自動載入

當引用 `@shared/perspectives` 時，自動載入各階段視角定義。

## 階段視角配置

### RESEARCH 視角

| ID | 名稱 | 模型 | 聚焦領域 |
|----|------|------|----------|
| architecture | 架構分析師 | sonnet | 系統結構、設計模式、技術選型 |
| cognitive | 認知研究員 | sonnet | 方法論、思維框架、學習曲線 |
| workflow | 工作流設計 | haiku | 執行流程、整合策略、自動化 |
| industry | 業界實踐 | haiku | 現有框架、最佳實踐、案例研究 |

### PLAN 視角

| ID | 名稱 | 模型 | 聚焦領域 |
|----|------|------|----------|
| architect | 系統架構師 | sonnet | 技術可行性、組件設計、介面定義 |
| risk-analyst | 風險分析師 | sonnet | 潛在風險、失敗場景、緩解策略 |
| estimator | 估算專家 | haiku | 工作量評估、時程規劃、資源配置 |
| ux-advocate | UX 倡導者 | haiku | 使用者體驗、API 設計、易用性 |

### TASKS 視角

| ID | 名稱 | 模型 | 聚焦領域 |
|----|------|------|----------|
| dependency-analyst | 依賴分析師 | sonnet | 任務依賴、執行順序、關鍵路徑 |
| task-decomposer | 任務分解師 | haiku | 粒度切分、並行識別、邊界劃分 |
| test-planner | 測試規劃師 | haiku | TDD 對應、測試策略、覆蓋目標 |
| risk-preventor | 風險預防師 | haiku | 風險任務、預防措施、回滾計劃 |

### REVIEW 視角

| ID | 名稱 | 模型 | 聚焦領域 |
|----|------|------|----------|
| code-quality | 程式碼品質 | haiku | 命名、結構、可讀性、SOLID |
| test-coverage | 測試覆蓋 | haiku | 覆蓋率、測試品質、邊界測試 |
| documentation | 文檔檢查 | haiku | 註解、README、API 文檔 |
| integration | 整合分析 | sonnet | 整合問題、依賴衝突、版本相容 |

### VERIFY 視角

| ID | 名稱 | 模型 | 聚焦領域 |
|----|------|------|----------|
| functional-tester | 功能測試員 | haiku | 正常流程、功能驗證、使用案例 |
| edge-case-hunter | 邊界獵人 | sonnet | 邊界條件、異常處理、壓力測試 |
| regression-checker | 回歸檢查員 | haiku | 回歸測試、副作用、相容性 |
| acceptance-validator | 驗收驗證員 | sonnet | 驗收標準、需求滿足、發布就緒 |

## 視角報告格式

```markdown
# {視角名稱} 報告

**視角 ID**: {perspective_id}
**執行時間**: {timestamp}
**主題**: {topic}

## 核心發現

1. ...
2. ...
3. ...

## 詳細分析

...

## 建議

...

## 信心度

高 / 中 / 低

---
*由 {perspective_name} 視角產出*
```

## 模型選擇原則

參考 @shared/config/model-routing.yaml：
- **深度分析**（architecture, cognitive, integration）→ sonnet
- **流程整理**（workflow, estimator）→ haiku
- **關鍵決策**（衝突解決、最終判定）→ opus

## 參考

- @shared/coordination/map-phase.md - 並行執行
- @shared/config/model-routing.yaml - 模型路由
