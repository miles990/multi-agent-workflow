# 認知研究員 報告

**視角 ID**: cognitive
**執行時間**: 2026-01-27
**主題**: clawdbot 記憶系統認知設計分析

## 核心發現

1. **雙重記憶模型（Dual Memory Architecture）**: clawdbot 實現了類似人類記憶系統的雙層結構 - 短期記憶（daily logs in `memory/YYYY-MM-DD.md`）和長期記憶（curated `MEMORY.md`），模擬工作記憶與語義記憶的認知區分。

2. **語義相似性的向量編碼（Semantic Embedding）**: 系統使用 embeddings 將文本轉換為高維向量空間，捕捉語義關係而非僅依賴字面匹配，反映人類語言理解的分散表徵（distributed representation）認知模型。

3. **混合檢索的認知互補（Hybrid Retrieval Complementarity）**: 結合向量相似性（語義理解）與 BM25 關鍵字檢索（精確匹配），模擬人類記憶檢索的雙重路徑 - 基於概念的聯想檢索與基於線索的直接存取。

4. **上下文維護的自動化機制（Automated Context Preservation）**: 通過 session-memory hook 和 automatic memory flush，系統在上下文窗口接近壓縮時主動提示 Agent 儲存重要資訊，類似人類短期記憶到長期記憶的主動鞏固過程。

5. **分塊與重疊的記憶編碼（Chunking with Overlap）**: 文本分塊（~400 token chunks, 80 token overlap）反映人類記憶編碼的組塊策略和情節重疊，確保語義連貫性不因分割而丟失。

## 詳細分析

### 認知模型對照

#### Atkinson-Shiffrin 多重記憶模型映射

| 記憶類型 | Clawdbot 對應 | 說明 |
|---------|--------------|------|
| 感覺記憶 | Session Transcript (.jsonl) | 原始、未過濾的資訊流 |
| 工作記憶 | Active Context Window | 有容量限制，觸發 memory flush |
| 長期記憶 - 情節 | `memory/YYYY-MM-DD.md` | 時間標記的日常記錄 |
| 長期記憶 - 語義 | `MEMORY.md` | 精煉的事實、偏好、決策 |

#### 記憶鞏固理論（Memory Consolidation）

系統的 **automatic memory flush** 機制反映記憶鞏固理論：

```javascript
{
  memoryFlush: {
    enabled: true,
    softThresholdTokens: 4000,
    systemPrompt: "Session nearing compaction. Store durable memories now.",
    prompt: "Write any lasting notes to memory/YYYY-MM-DD.md"
  }
}
```

**認知對應**:
- **臨界點觸發**：context 接近容量時觸發，類似大腦在認知負荷高時主動鞏固記憶
- **選擇性編碼**：Agent 決定哪些資訊值得儲存，反映人類記憶的注意力過濾機制
- **主動鞏固**：系統主動提示而非被動等待，類似自我解釋策略

### 語義理解機制

#### 向量空間的分散表徵

系統使用三種 embedding 來源：
- **OpenAI** (`text-embedding-3-small`): 1536 維
- **Gemini** (`gemini-embedding-001`): 768 維
- **Local** (`embeddinggemma-300M-GGUF`): 可變維度

**認知神經科學視角**:
- 高維向量空間類似大腦的分散式神經表徵
- 每個維度捕捉語義特徵的一個面向
- 相似概念在向量空間中距離接近（cosine similarity）

#### 語義相似性計算

```typescript
score: 1 - row.dist  // where dist = vec_distance_cosine(v.embedding, query)
```

**認知意義**:
- Cosine similarity 測量向量方向而非大小，反映語義關係的本質
- 這與人類語義記憶的組織方式一致：根據概念關係而非字面相似性檢索

### 檢索策略分析

#### Hybrid Search 的雙重處理理論

系統實現的混合檢索與 Kahneman 的雙系統理論有結構對應：

| System | 對應檢索 | 特性 | 適用場景 |
|--------|---------|------|---------|
| System 1（快速、直覺） | BM25 Keyword Search | 規則驅動 | IDs、變數名、錯誤訊息 |
| System 2（慢速、分析） | Vector Semantic Search | 計算密集 | 概念關聯、同義改寫 |

#### 權重融合策略

```typescript
finalScore = vectorWeight * vectorScore + textWeight * textScore
// Default: vectorWeight: 0.7, textWeight: 0.3
```

**認知分析**:
- 70% 語義，30% 關鍵字反映日常檢索以語義為主的現實
- Candidate multiplier (4x) 確保合併前有足夠候選池，類似記憶提取的擴散激活

### 上下文管理

#### Session Memory Hook 的情節記憶捕捉

```typescript
// 1. Extract recent conversation (last 15 lines)
const recentLines = lines.slice(-15);

// 2. Generate descriptive slug via LLM
slug = await generateSlugViaLLM({ sessionContent, cfg });

// 3. Create dated memory file
const filename = `${dateStr}-${slug}.md`;
```

**認知設計亮點**:
- **Recency window (15 lines)**: 類似人類記憶的近因效應
- **LLM-generated slug**: 使用語言模型生成語義標籤，反映人類為情節記憶創建"標題"的傾向
- **時間戳結構**: `YYYY-MM-DD` 前綴支援時間線檢索，符合情節記憶的時空組織

#### 分塊與重疊的記憶組織

```typescript
const maxChars = Math.max(32, chunking.tokens * 4);  // ~400 tokens
const overlapChars = Math.max(0, chunking.overlap * 4);  // ~80 tokens
```

**認知策略**:
- **組塊大小**: ~400 tokens ≈ 工作記憶容量（Miller's 7±2 或現代理論的 4±1 chunks）
- **重疊窗口**: 80 tokens 重疊確保跨邊界的語義連貫性

### 遺忘機制

#### 缺乏明確的遺忘策略

**觀察**: 代碼中沒有明確的記憶衰減或淘汰機制

**認知視角分析**:
- **永久性儲存模式**: 所有寫入的記憶都保持可檢索
- **依賴檢索過濾**: 通過 `maxResults` 限制和相關性排序來過濾
- **手動管理**: 用戶需主動編輯 `MEMORY.md` 來移除過時資訊

#### 隱式遺忘的可能性

1. **重新索引觸發**: embedding provider/model 改變時整個索引重建
2. **優先權排序**: 相關性評分自然讓低相關記憶"沉沒"
3. **日期組織**: `memory/YYYY-MM-DD.md` 結構允許基於時間的手動清理

### 與認知架構比較

| 認知架構元素 | Clawdbot 對應 | 契合度 |
|-------------|--------------|-------|
| ACT-R Declarative memory | `MEMORY.md` + vector index | ✅ 高 |
| ACT-R Procedural memory | 無技能學習 | ❌ 無 |
| ACT-R Activation spreading | Vector similarity search | ✅ 中 |
| Soar Working memory | Session context window | ✅ 高 |
| Soar Episodic memory | Daily logs with timestamps | ✅ 高 |

## 建議與洞察

### 1. 實現基於頻率的激活權重
**建議**: 追蹤記憶存取頻率，提升常用記憶的檢索排名
```typescript
activation = baseLevel + contextualRelevance
baseLevel = ln(Σ(t_i^(-d)))  // ACT-R 激活理論
```

### 2. 引入語義標籤系統
**建議**: 自動生成主題標籤，支援基於概念的組織

### 3. 實現遺忘曲線模擬
**建議**: 可選的記憶衰減機制
```typescript
function memoryStrength(chunk, now) {
  const ageInDays = (now - chunk.creationDate) / (1000 * 60 * 60 * 24);
  return Math.exp(-ageInDays / retentionConstant);
}
```

### 4. 支援多層次摘要
**建議**: 為長記憶文件生成多層次摘要（構造層次理論）

## 風險/注意事項

1. **語義漂移風險**: Embedding 模型更新可能改變語義空間
2. **上下文窗口壓縮損失**: 自動壓縮可能遺失細微但重要的上下文細節
3. **冷啟動問題**: 新 Agent 或空記憶庫的檢索效能差
4. **記憶品質無保證**: 錯誤或過時資訊污染記憶庫
5. **缺乏解釋性**: 用戶不理解為何某記憶被檢索或忽略

## 信心度

高

---
*由認知研究員視角產出*
