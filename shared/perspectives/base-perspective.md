# Base Perspective（共用模組）

> 視角基礎結構：定義視角的標準格式和 Prompt 生成規則

## 概述

視角（Perspective）是多 Agent 工作流的核心概念，每個視角代表一個專門的觀點或角色。

**此為共用模組**，各 skill 可定義自己的視角集合。

## 視角定義格式

### 標準結構

```yaml
perspective:
  id: string                   # 唯一識別符（如 architect）
  name: string                 # 顯示名稱（如 系統架構師）
  role: string                 # 角色描述
  focus_areas:                 # 聚焦領域列表
    - string
  research_method: string      # 研究/工作方法（deep | search | observe）
  agent_type: string           # Task API agent 類型
  priority_weight: number      # 在矛盾解決中的權重（0-1）
```

### 範例：架構分析師

```yaml
perspective:
  id: architect
  name: 系統架構師
  role: 專注於系統結構和設計模式的技術專家
  focus_areas:
    - 系統結構設計
    - 設計模式選擇
    - 可擴展性評估
    - 技術債務分析
  research_method: deep
  agent_type: general-purpose
  priority_weight: 0.9
```

## Prompt 生成規則

### 基礎 Prompt 模板

```markdown
## 任務

你是一位 {role}。

### 背景
{context}

### 主題/目標
{topic}

### 你的聚焦領域
{focus_areas 列表}

### 研究/工作方法
{research_method_description}

### 輸出要求
請產出一份結構化報告：

1. **核心發現/建議**（3-5 點）
   - 每點包含：標題、描述、信心度（高/中/低）

2. **詳細分析**
   - 按聚焦領域組織
   - 包含具體證據或案例

3. **建議與洞察**
   - 可行的行動建議
   - 潛在風險提醒

4. **相關資源**（如適用）

### 格式
使用 Markdown 格式，清晰分段
```

### 方法描述對應

| 方法 | 描述 |
|------|------|
| `deep` | 進行深度思考和分析，不需要搜尋外部資源 |
| `search` | 搜尋網路或程式碼庫以獲取最新資訊 |
| `observe` | 觀察和監督，提供即時回饋 |

### Agent 類型對應

| agent_type | Task API subagent_type |
|------------|------------------------|
| `general-purpose` | `general-purpose` |
| `explore` | `Explore` |
| `plan` | `Plan` |

## 預設視角集

### research skill 預設視角

| ID | 名稱 | 聚焦 | 方法 |
|----|------|------|------|
| `architecture` | 架構分析師 | 系統結構、設計模式 | deep |
| `cognitive` | 認知科學研究員 | 方法論、思維模式 | deep |
| `workflow` | 工作流設計師 | 執行流程、整合策略 | deep |
| `industry` | 業界實踐研究員 | 現有框架、最佳實踐 | search |

### plan skill 預設視角

| ID | 名稱 | 聚焦 | 方法 |
|----|------|------|------|
| `architect` | 系統架構師 | 技術可行性、組件設計 | deep |
| `risk-analyst` | 風險分析師 | 潛在風險、失敗場景 | deep |
| `estimator` | 估算專家 | 工作量評估、優先順序 | deep |
| `ux-advocate` | UX 倡導者 | 使用者體驗、API 設計 | deep |

### review skill 預設視角

| ID | 名稱 | 聚焦 | 方法 |
|----|------|------|------|
| `code-quality` | 程式碼品質審查員 | 風格一致性、設計模式 | explore |
| `test-coverage` | 測試覆蓋審查員 | 測試品質、邊界案例 | explore |
| `documentation` | 文檔審查員 | API 文檔、註解 | explore |
| `integration` | 整合審查員 | 向後相容、API 契約 | explore |

### verify skill 預設視角

| ID | 名稱 | 聚焦 | 方法 |
|----|------|------|------|
| `functional-tester` | 功能測試員 | 核心功能、Happy Path | deep |
| `edge-case-hunter` | 邊界獵人 | 極端輸入、錯誤處理 | deep |
| `regression-checker` | 回歸檢查員 | 現有功能、向後相容 | explore |
| `acceptance-validator` | 驗收驗證員 | 需求符合度、DoD | deep |

### implement skill 預設視角

| ID | 名稱 | 聚焦 | 方法 |
|----|------|------|------|
| `tdd-enforcer` | TDD 守護者 | 測試先行、覆蓋率 | observe |
| `performance-optimizer` | 效能優化師 | 時間複雜度、記憶體 | observe |
| `security-auditor` | 安全審計員 | OWASP、輸入驗證 | observe |
| `maintainer` | 維護性專家 | 可讀性、重構友善 | observe |

## 自訂視角

### 定義方式

在各 skill 的 `01-perspectives/_base/custom-perspectives.md` 中定義：

```yaml
custom_perspectives:
  - id: my-perspective
    name: 我的視角
    role: 專注於...的專家
    focus_areas:
      - 領域 1
      - 領域 2
    research_method: deep
    agent_type: general-purpose
    priority_weight: 0.8
```

### 覆蓋預設視角

可以透過相同 ID 覆蓋預設視角的部分屬性：

```yaml
overrides:
  architect:
    focus_areas:
      - 微服務架構
      - 事件驅動設計
    priority_weight: 1.0
```

## 視角選擇邏輯

### 模式對應

| 模式 | 視角數 | 選擇邏輯 |
|------|--------|----------|
| quick | 2 | 選擇權重最高的 2 個 |
| normal | 4 | 使用預設 4 個 |
| deep | 6 | 預設 4 個 + 自訂 2 個 |
| custom | N | 完全自訂 |

### 動態調整

根據主題自動調整視角權重：

```yaml
topic_adjustments:
  - pattern: "安全|security|auth"
    boost:
      security-auditor: 1.5
  - pattern: "效能|performance|優化"
    boost:
      performance-optimizer: 1.5
```

## 配置參數

```yaml
perspectives:
  default_set: [id1, id2, id3, id4]
  mode: quick | normal | deep | custom
  custom_perspectives: []
  overrides: {}
  topic_adjustments: []
```
