# 架構分析師 報告

**視角 ID**: architecture
**執行時間**: 2026-01-27
**主題**: clawdbot 記憶系統架構分析

## 核心發現

1. **三層架構設計**：Memory System 採用清晰的三層架構：Plugin Layer（擴展點）→ Core Layer（Manager + Embeddings + Search）→ Storage Layer（SQLite + Vector Extension + FTS5），支持多種向量資料庫實現。

2. **Provider 抽象 + Fallback 策略**：Embeddings 系統通過統一的 `EmbeddingProvider` 介面支持 OpenAI、Gemini、Local (node-llama-cpp) 三種提供者，具備自動降級機制（remote → local fallback），確保系統可用性。

3. **混合檢索引擎**：實現 Hybrid Search（Vector Similarity + BM25 FTS）結合語義相似和精確匹配，透過加權融合（預設 0.7 vector + 0.3 text）解決「語義模糊」與「精確查找」的雙重需求。

4. **多數據源索引**：支持 `memory` (Markdown files) 和 `sessions` (JSONL transcripts) 兩種數據源，使用 delta tracking 機制（deltaBytes/deltaMessages）實現增量索引，避免頻繁全量重建。

5. **Batch 優化 + Cache**：對 OpenAI/Gemini 提供 Batch API 支持（異步大規模索引）+ Embedding Cache（基於內容 hash），顯著降低 API 成本和延遲。

## 詳細分析

### 1. 整體架構圖

```
┌───────────────────────────────────────────────────────────────────┐
│                        Plugin Layer (Extensions)                   │
│  ┌──────────────────┐              ┌──────────────────────────┐   │
│  │  memory-core     │              │  memory-lancedb          │   │
│  │  (Default)       │              │  (Alternative)           │   │
│  └────────┬─────────┘              └──────────┬───────────────┘   │
│           │ registerTool                      │ LanceDB + Auto    │
│           │ registerCli                       │ Capture/Recall    │
└───────────┼───────────────────────────────────┼───────────────────┘
            │                                   │
            ▼                                   ▼
┌───────────────────────────────────────────────────────────────────┐
│                          Core Layer                                │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              MemoryIndexManager (manager.ts)                 │  │
│  │  - Singleton per (agentId, workspace, config)               │  │
│  │  - Lifecycle: INDEX_CACHE Map                               │  │
│  │  - search(query) → Hybrid Results                           │  │
│  │  - sync() → Incremental/Full Reindex                        │  │
│  │  - status() → Health Check                                  │  │
│  └──────────────┬─────────────────────────────┬────────────────┘  │
│                 │                             │                    │
│     ┌───────────▼──────────┐     ┌───────────▼──────────┐        │
│     │ EmbeddingProvider    │     │  Search Engine       │        │
│     │  (embeddings.ts)     │     │  (search-manager.ts) │        │
│     ├──────────────────────┤     ├──────────────────────┤        │
│     │ - OpenAI             │     │ - searchVector()     │        │
│     │ - Gemini             │     │ - searchKeyword()    │        │
│     │ - Local (llama-cpp)  │     │ - mergeHybrid()      │        │
│     │ - Auto Selection     │     │ - buildFtsQuery()    │        │
│     │ - Fallback Chain     │     └──────────────────────┘        │
│     └──────────────────────┘                                      │
└───────────────────────────────────────────────────────────────────┘
            │                                   │
            ▼                                   ▼
┌───────────────────────────────────────────────────────────────────┐
│                        Storage Layer                               │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  SQLite Database (per agent: ~/.clawdbot/memory/<id>.sqlite) │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │  Tables:                                                      │ │
│  │  - files: (path, source, hash, mtime, size)                  │ │
│  │  - chunks: (id, path, source, lines, text, embedding, ...)   │ │
│  │  - chunks_vec: (vec0 virtual table with sqlite-vec)          │ │
│  │  - chunks_fts: (fts5 full-text index)                        │ │
│  │  - embedding_cache: (provider, model, hash → embedding)      │ │
│  │  - meta: (index metadata: provider, model, chunking params)  │ │
│  └──────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
```

### 2. 核心組件分析

#### 2.1 MemoryIndexManager (manager.ts)

**職責**：
- 索引生命週期管理（sync, reindex, dirty tracking）
- 多數據源協調（memory files + session transcripts）
- 查詢路由（hybrid search orchestration）
- Provider fallback 處理
- Watch + Interval + Delta-triggered sync

**關鍵設計**：
- **Singleton Pattern**：通過 `INDEX_CACHE` Map 確保每個 `(agentId, workspace, settings)` 唯一實例
- **Lazy Initialization**：Vector extension 和資料庫連接按需加載
- **Safe Reindex**：使用臨時資料庫 + atomic swap，避免索引過程中損壞主庫
- **Concurrency Control**：`runWithConcurrency()` 限制並發 embedding 請求

#### 2.2 EmbeddingProvider (embeddings.ts)

**職責**：
- 統一 embedding 介面 (`embedQuery`, `embedBatch`)
- Provider 自動選擇（auto mode）
- Fallback 策略（primary fails → fallback provider）

**Provider 實現**：
1. **OpenAI**: 支持自定義 `baseUrl` + `headers`，Batch API 整合
2. **Gemini**: 原生 Gemini Embeddings API，Batch API 支持
3. **Local** (node-llama-cpp): 預設模型 `embeddinggemma-300M-Q8_0.gguf`

#### 2.3 Search Engine

**混合搜索流程**：
```
1. embedQuery(query) → queryVec
2. Parallel Fetch:
   - searchVector(queryVec) → SQLite chunks_vec
   - searchKeyword(query) → SQLite chunks_fts (BM25)
3. mergeHybridResults({vectorWeight: 0.7, textWeight: 0.3})
4. Filter (minScore) + Slice (maxResults)
```

### 3. 設計模式識別

| 模式 | 應用位置 | 說明 |
|------|---------|------|
| Singleton + Factory | `MemoryIndexManager.get()` | 每個 key 唯一實例 |
| Strategy Pattern | `EmbeddingProvider` | OpenAI/Gemini/Local 可互換 |
| Plugin Architecture | `memory-core`, `memory-lancedb` | 透過 API 註冊擴展 |
| Observer Pattern | FSWatcher + Event handlers | 檔案變更監聽 |
| Adapter Pattern | `createEmbeddingProvider()` | 統一不同 API 介面 |

### 4. 數據流分析

#### 索引流程
```
Trigger → sync() → needsFullReindex?
  ├─ Yes → runSafeReindex() (temp DB + swap)
  └─ No  → syncMemoryFiles() + syncSessionFiles()
    ↓
For each file:
  ├─ Check hash (skip if unchanged)
  ├─ chunkMarkdown(content, {tokens: 400, overlap: 80})
  ├─ embedChunksInBatches()
  └─ Store to SQLite (files + chunks + chunks_vec + chunks_fts)
```

#### 查詢流程
```
memory_search(query) → embedQuery() → Parallel Search
  ├─ Vector: chunks_vec MATCH
  └─ Keyword: chunks_fts BM25
    ↓
mergeHybridResults() → Filter + Sort → Return Results
```

## 建議與洞察

### 架構優勢
1. **Fallback Chain 提升可用性**：`OpenAI → Gemini → Local` 自動降級
2. **Batch API 降低成本**：OpenAI Batch API 比同步請求便宜 50%
3. **Hybrid Search 平衡語義與精確**：解決純向量搜索的精確匹配弱點
4. **Embedding Cache 顯著減少重複計算**

### 可改進點
1. **Vector Store 抽象**：支持 Qdrant/Milvus 作為可選後端
2. **可配置 Chunking 策略**：代碼文件使用 AST-based chunking
3. **Query 性能監控**：添加 tracing/metrics

## 風險/注意事項

1. **SQL Injection 風險**：部分位置使用字符串拼接，建議使用參數化查詢
2. **大文件索引 OOM**：建議添加文件大小檢查
3. **Embedding Rate Limit**：頻繁觸發可能導致索引任務超時
4. **Session Transcript 無限增長**：建議添加 retention policy

## 信心度

高

---
*由架構分析師視角產出*
