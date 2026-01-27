# 工作流設計師 報告

**視角 ID**: workflow
**執行時間**: 2026-01-27
**主題**: clawdbot 記憶系統工作流程分析

## 核心發現

1. **雙層記憶來源架構**: clawdbot 採用兩層記憶來源設計 - Memory Files（持久性 Markdown 文件）和 Session Files（自動化 JSONL 轉錄），通過 `syncMemoryFiles` 和 `syncSessionFiles` 分別管理。

2. **批量嵌入隊列系統**: 系統支援遠程批量處理（OpenAI Batch API + Gemini Batch API）和本地嵌入，最多 50,000 請求/批次，自動分組，具備智能失敗恢復機制。

3. **即時同步與記憶刷新**: 在自動壓縮前，通過 `memory-flush.ts` 的預壓縮記憶刷新機制，確保 Agent 有機會將臨時知識轉存到磁盤。

4. **CLI + Agent 工具集成**: `memory-cli.ts` 和 `memory-tool.ts` 提供統一的命令行和 Agent 集成（status、index、search 命令）。

5. **混合搜索能力**: 系統整合向量搜索、FTS 全文搜索和 BM25 排序，通過 `hybrid.ts` 合併結果。

## 詳細分析

### 寫入流程圖

```
User/Agent Input
    ↓
[Memory Tool] → memory_tool.ts (Agent-facing API)
    ↓
getMemorySearchManager()
    ↓
MemoryIndexManager (核心引擎)
    ├─ readFile() 或 search()
    ├─ 檢查嵌入快取
    ├─ 調用嵌入提供者
    └─ 返回搜索結果

並行寫入路徑（Pre-Compaction Memory Flush）：
    ↓
[Session 達到 Token 閾值]
    ↓
shouldRunMemoryFlush() 檢查觸發條件
    ├─ totalTokens > (contextWindow - reserveFloor - softThreshold)
    ├─ 檢查未執行過 flush
    └─ 返回 boolean
    ↓
Agent 收到 memory-flush 系統提示
    ↓
Agent 將臨時知識寫入 memory/*.md
    ↓
syncMemoryFiles() 檢測新文件
    ├─ listMemoryFiles() → 掃描工作區
    ├─ buildFileEntry() → 計算文件 hash
    ├─ 與 DB 比較（hash 匹配跳過）
    └─ indexFile() → 分塊+嵌入
```

### 檢索流程圖

```
Agent 調用 memory_search 工具
    ↓
createMemorySearchTool.execute()
    ├─ 讀取查詢參數 (maxResults, minScore)
    ├─ 解析 agentId
    └─ 檢查配置合法性
    ↓
manager.search(query, options)
    ↓
[多路並行檢索]
    ├─ searchVector()：向量相似度搜索
    │   ├─ 嵌入查詢文本
    │   ├─ 查詢 chunks_vec 表
    │   └─ 返回向量結果 + score
    │
    ├─ searchKeyword()：BM25 + FTS 搜索
    │   ├─ buildFtsQuery() 轉換查詢
    │   ├─ chunks_fts 表查詢
    │   └─ bm25RankToScore() 計算分數
    │
    └─ mergeHybridResults()
        ├─ 合併結果（去重）
        ├─ 規範化分數
        ├─ 按綜合分排序
        └─ 返回 top-N 結果
    ↓
為每個結果取片段 (snippet)
    ├─ readFile() 讀原文件
    ├─ 提取 startLine-endLine
    └─ 截斷至 700 字符
    ↓
返回 MemorySearchResult[] (path, snippet, score, source)
```

### 同步機制分析

#### File Hash 變化檢測

```typescript
const record = db.prepare(`SELECT hash FROM files WHERE path = ? AND source = ?`)
                .get(entry.path, "memory");
if (!needsFullReindex && record?.hash === entry.hash) {
  // 跳過：未變化
} else {
  // 執行：indexFile(entry)
}
```

**優勢**：
- O(1) 變化檢測，避免重複嵌入
- 支持全量索引強制刷新 (`needsFullReindex`)

#### Session 檔案 Dirty 追蹤

```typescript
const indexAll = params.needsFullReindex || params.dirtyFiles.size === 0;
if (!indexAll && !params.dirtyFiles.has(absPath)) {
  // 跳過：不在 dirty set 中
}
```

**工作流**：
1. Session 更新事件觸發 → 檔案路徑加入 `dirtyFiles`
2. 5 秒去抖 (`SESSION_DIRTY_DEBOUNCE_MS`)
3. 批量同步時掃描 dirty set
4. 同步完成後清空 set

### 批次嵌入工作流程

#### OpenAI Batch 流程

```
1. splitOpenAiBatchRequests(requests)
   └─ 最多 50,000 請求/組

2. 對每組：submitOpenAiBatch()
   ├─ 轉換為 JSONL 格式
   ├─ 上傳至 /v1/files
   ├─ 建立 batch 作業 (/v1/batches)
   └─ 返回 batchId + status

3. waitForOpenAiBatch()
   ├─ 輪詢狀態 (pollIntervalMs)
   ├─ 狀態轉移：submitted → processing → completed
   └─ 若失敗，讀取 error_file_id 詳情

4. fetchOpenAiFileContent(outputFileId)
   └─ 逐行解析 JSONL，提取 embedding

5. byCustomId: Map<string, number[]>
   └─ 返回自訂 ID → 向量映射
```

#### Gemini Batch 流程

類似 OpenAI，但差異：
- uploadUrl：`/upload/v1beta/files`（多部分編碼）
- batchEndpoint：`/{modelPath}:asyncBatchEmbedContent`
- 狀態值：SUCCEEDED, COMPLETED, DONE

### CLI 命令整理

| 命令 | 功能 | 選項 |
|------|------|------|
| `memory status` | 顯示記憶系統狀態 | `--agent`, `--deep`, `--index`, `--json` |
| `memory index` | 索引記憶文件 | `--force`, `--verbose` |
| `memory search <query>` | 搜索記憶 | `--max-results`, `--min-score` |

#### `memory status` 流程
```
runMemoryStatus(options)
├─ 掃描 memory/ 目錄
├─ 掃描 sessions/ 目錄
├─ 檢查向量可用性 (probeVectorAvailability)
├─ 檢查嵌入提供者 (probeEmbeddingAvailability)
└─ 輸出格式化報告
```

#### `memory index` 流程
```
runMemoryIndex(options)
├─ 掃描變化
├─ manager.sync({reason, force, progress})
├─ 逐檔案並發索引 (concurrency=4)
└─ 報告進度 (elapsed time, ETA)
```

## 建議與洞察

### 工作流優化建議

1. **非同步批次預熱**: 在後台定期提交小批次嵌入，降低延遲峰值
2. **多層快取策略**:
   - L1：嵌入快取（內存 + SQLite）
   - L2：FTS 索引（SQLite）
   - L3：向量索引（sqlite-vec 擴展）
3. **混合搜索權重調整**: 考慮使用用戶反饋調整 BM25/Vector 權重

### 架構強度分析

**優勢**：
- 多來源統一索引（Memory + Sessions）
- 智能變化偵測（hash-based）
- 遠程/本地嵌入無縫切換
- Agent 預壓縮記憶刷新
- 混合搜索（向量 + 關鍵字）
- 批次失敗恢復（失敗限制 = 2）

**潛在改進**：
- 批次 timeout 可配置化
- 加強事件遺漏時的全量重索機制
- 嵌入快取 maxEntries 監控

## 風險/注意事項

### 1. 批次失敗降級
```typescript
if (batchFailureCount >= BATCH_FAILURE_LIMIT) {
  // 自動降級至本地嵌入或其他提供者
}
```
- **風險**: 本地嵌入模型未預載，降級失敗會拋出例外
- **緩解**: 提前配置備用提供者

### 2. Memory Flush 條件邊界
```typescript
const threshold = Math.max(0, contextWindow - reserveTokens - softThreshold);
if (totalTokens < threshold) return false;
```
- **風險**: `reserveTokensFloor` 配置過大，Flush 永不觸發
- **緩解**: 驗證配置合理性

### 3. Dirty Set 去抖延遲
- **風險**: Session 更新頻繁時，索引延遲最多 5 秒
- **影響**: 搜索可能返回過時結果

### 4. Vector 擴展加載失敗
- **風險**: 向量搜索不可用，系統降級至 FTS + BM25
- **檢查**: `manager.status().vector.loadError`

### 5. FTS 方言相容性
- SQLite FTS5 不支持複雜 AND/OR/NOT 語法
- `buildFtsQuery()` 處理轉換，但複雜查詢可能失效

## 信心度

高

---
*由工作流設計師視角產出*
