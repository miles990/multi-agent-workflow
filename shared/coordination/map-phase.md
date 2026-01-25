# Map Phase（共用模組）

> 並行執行階段：多 Agent 同時處理不同視角/任務

## 概述

Map Phase 是多 Agent 工作流的核心階段，透過 Task API 啟動多個並行 Agent，每個 Agent 負責一個視角的專門工作。

**此為共用模組**，被以下 skill 引用：
- `skills/research/` - 多視角研究
- `skills/plan/` - 多視角規劃
- `skills/implement/` - 監督式實作
- `skills/review/` - 多視角審查
- `skills/verify/` - 多視角驗證

## 模型路由

每個視角根據任務複雜度使用不同的模型，最大化效率和品質。

### 模型配置

```yaml
# 配置來源：shared/config/model-routing.yaml
視角類型          模型      原因
───────────────  ────────  ─────────────────────
深度分析類       sonnet    需要複雜推理與洞察
流程整理類       haiku     較機械性任務/快速反應
關鍵決策類       opus      最高品質要求/複雜決策
```

### 在 Task 中指定模型

```javascript
// 使用模型路由
const modelConfig = loadConfig('shared/config/model-routing.yaml');
const model = modelConfig.routing[STAGE][perspective] || 'sonnet';

Task({
  description: `${perspective} 視角分析`,
  model: model,  // 指定模型
  prompt: perspectivePrompt
});
```

→ 完整配置：[../config/model-routing.yaml](../config/model-routing.yaml)

## 執行流程

```
┌─────────────────────────────────────────────────────────────────┐
│  準備階段                                                        │
│  1. 載入視角配置（由各 skill 提供）                              │
│  2. 為每個視角生成專屬 prompt                                    │
│  3. 準備 Task API 呼叫                                           │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│  並行啟動                                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Task #1        Task #2        Task #3        Task #4     │   │
│  │ (視角 A)       (視角 B)       (視角 C)       (視角 D)    │   │
│  │                                                           │   │
│  │ 各 Agent 獨立運作，互不干擾                               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│  同步檢查點（可選）                                              │
│  S1 (50%): 確認方向正確                                          │
│  S2 (80%): 驗證初步成果                                          │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│  收集結果                                                        │
│  等待所有 Task 完成，收集視角報告                                │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│  保存視角報告（重要！）                                          │
│  將每個視角的報告寫入檔案：                                      │
│  .claude/memory/{type}/{id}/perspectives/{perspective_id}.md    │
└─────────────────────────────────────────────────────────────────┘
```

## Task API 呼叫模式

### 並行啟動

```javascript
// 概念示意（實際使用 Claude Code Task tool）
const tasks = perspectives.map(perspective => ({
  description: `${perspective.name} 處理 ${topic}`,
  prompt: generatePrompt(perspective, topic, config),
  subagent_type: selectAgentType(perspective),
  model: selectModelForPerspective(perspective)  // 根據視角選擇模型
}))

// 並行執行所有 Task
await Promise.all(tasks.map(task => executeTask(task)))
```

### 模型選擇流程

```
1. 讀取 shared/config/model-routing.yaml
   ↓
2. 根據 STAGE + perspective 類型查找推薦模型
   ↓
3. 如未找到配置，使用預設 sonnet
   ↓
4. 如遇錯誤 2 次以上（timeout、rate-limit），
   自動升級到更強模型（sonnet → opus）
   ↓
5. 將選定的模型傳入 Task
```

**自動升級邏輯**：
- 第 1 次失敗：重試相同模型
- 第 2 次失敗：升級到更強模型 + 重試
- 第 3 次失敗：升級至 opus（最高層）或標記失敗

### Agent 類型選擇

| 視角類型 | subagent_type | 適用場景 |
|----------|---------------|----------|
| 探索型 | `Explore` | 需要搜尋程式碼/檔案 |
| 分析型 | `general-purpose` | 深度思考分析 |
| 規劃型 | `Plan` | 需要設計實作計劃 |

### 通用 Prompt 結構

```markdown
## 任務

你是一位 {角色描述}。

### 主題/目標
{topic}

### 你的聚焦領域
{focus_points}

### 輸出要求
請產出一份結構化報告：

1. **核心發現/建議**（3-5 點）
2. **詳細分析**
3. **建議與洞察**
4. **風險/注意事項**（如適用）

### 格式
使用 Markdown 格式，清晰分段
```

## 同步檢查點

### S1: 進度確認 (50%)

**目的**：確保方向正確

檢查項目：
- [ ] Agent 正在處理正確的主題
- [ ] 深度符合預期
- [ ] 沒有偏離核心問題

如果偏離：
- 終止該 Agent
- 調整 prompt
- 重新啟動

### S2: 成果驗證 (80%)

**目的**：確認初步成果的品質

檢查項目：
- [ ] 發現/建議有足夠支持
- [ ] 結論合理
- [ ] 可以進入整合階段

## 失敗處理

### Agent 超時

```
如果 Agent 超過預期時間：
1. 記錄已有的部分結果
2. 標記為「部分完成」
3. 繼續整合流程（降級處理）
```

### Agent 錯誤

```
如果 Agent 回報錯誤：
1. 記錄錯誤類型
2. 嘗試一次重啟（相同配置）
3. 如仍失敗，使用備用視角或跳過
```

## 並行度控制

| 模式 | 並行 Agent 數 | 適用場景 |
|------|--------------|---------|
| quick | 2 | 快速處理 |
| normal | 4 | 標準處理 |
| deep | 6 | 深度處理 |

### 記憶體考量

每個 Agent 獨立運作，不共享上下文。這確保：
- 視角獨立性（不互相影響）
- 資源隔離（一個失敗不影響其他）
- 可擴展性（可輕易增加視角數）

## 配置參數

各 skill 可透過配置客製化 Map Phase：

```yaml
map_config:
  parallelism: 4              # 並行度
  timeout_minutes: 10         # 單一 Agent 超時
  checkpoints:
    enabled: true             # 是否啟用同步檢查點
    s1_threshold: 0.5         # S1 觸發點
    s2_threshold: 0.8         # S2 觸發點
  retry:
    max_attempts: 2           # 最大重試次數
    on_failure: skip          # 失敗策略：skip | abort | fallback
```

## 保存視角報告

**重要**：每個 Agent 完成後，必須將其報告寫入檔案，而非只保留在記憶體中。

### 保存路徑

```
.claude/memory/{type}/{id}/perspectives/{perspective_id}.md

範例：
.claude/memory/research/user-auth/perspectives/architecture.md
.claude/memory/plans/user-auth/perspectives/risk-analyst.md
.claude/memory/reviews/user-auth/perspectives/code-quality.md
```

### 保存流程

```
每個 Agent 完成時：
    ↓
1. 確認輸出目錄存在
   mkdir -p .claude/memory/{type}/{id}/perspectives/
    ↓
2. 將報告寫入檔案
   Write → perspectives/{perspective_id}.md
    ↓
3. 記錄指標（如啟用）
   <!-- METRICS: record_agent perspective_id={id} output_path={path} -->
    ↓
4. 繼續等待其他 Agent
```

### 報告檔案格式

每個視角報告應包含：

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

### ⚠️ 報告長度限制

**重要**：為確保 REDUCE 階段能正常讀取所有視角報告，每份報告應控制在合理長度。

| 項目 | 建議限制 | 說明 |
|-----|---------|------|
| **單一報告** | ≤ 300 行 | 約 5000 tokens |
| **核心發現** | ≤ 50 行 | 最重要，必須精煉 |
| **詳細分析** | ≤ 150 行 | 可適度精簡 |
| **附錄** | ≤ 50 行 | 非必要可省略 |

**在 Agent Prompt 中加入限制**：

```markdown
### 輸出要求

請產出一份結構化報告，**總長度不超過 300 行**：

1. **核心發現**（3-5 點，必須精煉）
2. **詳細分析**（聚焦關鍵點）
3. **建議與洞察**
4. **風險/注意事項**（如適用）

⚠️ 優先保證核心發現的完整性，詳細分析可精簡。
```

**如果主題複雜需要更長報告**：

1. 將詳細內容放在 `## 附錄` section
2. 在 `## 核心發現` 保持精煉摘要
3. 在 `## Cross-Reference Notes` 標記關鍵點供 REDUCE 階段使用

這樣 REDUCE 階段可以只讀取前 100 行獲取核心資訊。

### 為什麼要保存？

1. **可追溯性**：可以回頭查看每個視角的原始分析
2. **除錯**：匯總有問題時可以檢查個別視角
3. **復用**：其他工作流可以引用特定視角的報告
4. **透明度**：使用者可以看到完整的分析過程

## 下一步

Map Phase 完成後，進入 [Reduce Phase](./reduce-phase.md) 進行整合。
