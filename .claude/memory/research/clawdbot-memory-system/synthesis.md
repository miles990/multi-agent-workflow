# Clawdbot 記憶系統 - 匯總報告

## 摘要

Clawdbot 的記憶系統是一個**認知工程傑作**，採用三層架構（Plugin → Core → Storage）實現了類似人類記憶的雙重結構。系統透過 Hybrid Search（向量 + BM25）、多 Provider 支援（OpenAI/Gemini/Local）、自動記憶鞏固機制，提供了業界領先的 AI Agent 記憶能力。

## 方法

- **視角**：架構分析師、認知研究員、工作流設計師、業界實踐專家
- **日期**：2026-01-27
- **模式**：default（4 視角並行）
- **研究對象**：`/Users/user/Workspace/clawdbot` 記憶系統

## 共識發現

### 強共識（4/4 視角同意）

1. **三層架構設計完善**
   - Plugin Layer（memory-core、memory-lancedb 可切換）
   - Core Layer（Manager + Embeddings + Search）
   - Storage Layer（SQLite + sqlite-vec + FTS5）
   - **認知對應**：類似人類記憶的感覺→工作→長期記憶分層

2. **Hybrid Search 是核心優勢**
   - 向量語義搜索（70%）+ BM25 關鍵字搜索（30%）
   - 解決純向量搜索的精確匹配弱點
   - **認知對應**：模擬人類記憶的聯想檢索 + 直接存取雙路徑
   - **業界對照**：符合 RAG 最佳實踐

3. **多 Provider Fallback 策略提升可用性**
   - 支援 OpenAI → Gemini → Local (node-llama-cpp) 自動降級
   - 確保 API 故障時系統仍可運作
   - Batch API 整合降低成本 50%

4. **自動記憶鞏固機制**
   - Memory Flush 在 context 接近壓縮時主動觸發
   - Session Memory Hook 自動保存重要對話
   - **認知對應**：類似人類短期→長期記憶的主動鞏固過程

### 弱共識（2-3/4 視角同意）

1. **增量索引機制高效**（架構 + 工作流）
   - Hash-based 變化偵測，避免重複嵌入
   - Session Delta Tracking 優化大型 transcript 索引

2. **插件架構支持擴展**（架構 + 業界）
   - `ClawdbotPluginApi` 提供清晰擴展點
   - 可透過 `slots.memory` 切換實現

## 矛盾分析

### 已解決

1. **L2 距離 vs Cosine Similarity**
   - 架構視角指出使用 Cosine Similarity
   - 業界視角指出 LanceDB 實際使用 L2 距離
   - **解決**：代碼確認 memory-core 使用 cosine，memory-lancedb 使用 L2（技術上都正確，L2 適合正規化向量）

### 需進一步處理

1. **memory-lancedb 的 Provider 限制**
   - 業界視角指出 memory-lancedb 僅支援 OpenAI（供應商鎖定風險）
   - memory-core 支援多 Provider
   - **建議**：統一 Provider 支援，或明確文檔說明差異

## 關鍵洞察

### 架構洞察

```
┌─────────────────────────────────────────────────────────────┐
│                    Clawdbot Memory System                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ memory-core │  │memory-lance │  │   Session Memory    │  │
│  │ (Markdown)  │  │   (Vector)  │  │     (Hooks)         │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│         └────────────────┼─────────────────────┘             │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              MemoryIndexManager                          ││
│  │  • Hybrid Search (Vector 70% + BM25 30%)                ││
│  │  • Multi-Provider (OpenAI/Gemini/Local)                 ││
│  │  • Batch API + Embedding Cache                          ││
│  │  • Safe Reindex (atomic swap)                           ││
│  └─────────────────────────────────────────────────────────┘│
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              SQLite Storage                              ││
│  │  • chunks + chunks_vec (sqlite-vec) + chunks_fts (FTS5) ││
│  │  • embedding_cache + files + meta                       ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 認知洞察

| 人類記憶系統 | Clawdbot 對應 | 實現狀態 |
|-------------|--------------|---------|
| 感覺記憶 | Session Transcript (.jsonl) | ✅ 完整 |
| 工作記憶 | Active Context Window | ✅ 完整 |
| 情節記憶 | `memory/YYYY-MM-DD.md` | ✅ 完整 |
| 語義記憶 | `MEMORY.md` + Vector Index | ✅ 完整 |
| 記憶鞏固 | Memory Flush + Session Hooks | ✅ 完整 |
| 遺忘機制 | — | ❌ 缺失 |
| 頻率效應 | — | ❌ 缺失 |

### 業界對照

| 特性 | Clawdbot | LangChain | LlamaIndex | 評價 |
|------|----------|-----------|-----------|------|
| 自動捕捉 | ✅ 規則+語義 | ❌ 手動 | ❌ 手動 | **領先** |
| 混合搜索 | ✅ Vector+BM25 | ⚠️ 僅 Vector | ✅ 支援 | 符合標準 |
| 去重機制 | ✅ 0.95 閾值 | ❌ 無 | ⚠️ 元數據 | **領先** |
| 多 Provider | ✅ 3 種 | ✅ 可插拔 | ✅ 可插拔 | 符合標準 |
| 生產成熟度 | ⚠️ 新興 | ✅ 成熟 | ✅ 成熟 | 需改進 |

## 行動建議

### 1. 立即行動（High Priority）

- [ ] **統一 Provider 支援**：memory-lancedb 應支援 Gemini + Local，消除供應商鎖定
- [ ] **添加 Query 監控**：記錄 recall precision、embedding 成本、cache hit rate
- [ ] **修復潛在 SQL Injection**：部分位置使用字符串拼接，改用參數化查詢

### 2. 短期規劃（Medium Priority）

- [ ] **實現記憶衰減機制**：可選的 Ebbinghaus 遺忘曲線模擬
- [ ] **添加頻率效應權重**：追蹤記憶存取頻率，提升常用記憶排名
- [ ] **批量嵌入優化**：memory-lancedb 應支援 Batch API
- [ ] **Reranking 階段**：添加 cross-encoder 重排序提升精度

### 3. 長期考量（Low Priority）

- [ ] **Vector Store 抽象層**：統一介面支援 Qdrant/Milvus/Pinecone
- [ ] **多模態記憶**：支援圖像、語音
- [ ] **知識圖譜整合**：實體中心的檢索能力
- [ ] **分散式部署**：多 Agent 共享記憶

## 風險摘要

| 風險類別 | 風險項目 | 嚴重度 | 緩解建議 |
|---------|---------|-------|---------|
| 安全 | SQL Injection | 中 | 使用參數化查詢 |
| 可用性 | Provider Fallback 失敗 | 中 | 預載本地模型 |
| 性能 | 大文件 OOM | 中 | 添加文件大小檢查 |
| 供應商 | OpenAI 鎖定 (lancedb) | 高 | 擴展 Provider 支援 |
| 數據 | 記憶品質無保證 | 中 | 添加時效性標記 |

## 附錄

### 視角報告連結

- [架構分析師報告](./perspectives/architecture.md)
- [認知研究員報告](./perspectives/cognitive.md)
- [工作流設計師報告](./perspectives/workflow.md)
- [業界實踐專家報告](./perspectives/industry.md)

### 關鍵代碼路徑

| 模組 | 路徑 |
|------|------|
| Core Manager | `/Users/user/Workspace/clawdbot/src/memory/manager.ts` |
| Embeddings | `/Users/user/Workspace/clawdbot/src/memory/embeddings.ts` |
| Search | `/Users/user/Workspace/clawdbot/src/memory/search-manager.ts` |
| Hybrid | `/Users/user/Workspace/clawdbot/src/memory/hybrid.test.ts` |
| CLI | `/Users/user/Workspace/clawdbot/src/cli/memory-cli.ts` |
| Agent Tool | `/Users/user/Workspace/clawdbot/src/agents/tools/memory-tool.ts` |
| LanceDB Plugin | `/Users/user/Workspace/clawdbot/extensions/memory-lancedb/index.ts` |
| Session Hook | `/Users/user/Workspace/clawdbot/src/hooks/bundled/session-memory/handler.ts` |
| 文檔 | `/Users/user/Workspace/clawdbot/docs/concepts/memory.md` |

---

**報告生成時間**: 2026-01-27
**品質分數**: 82/100
**共識率**: 85%
**視角數**: 4/4 完成

*由 Multi-Agent Research Framework v3.2.0 生成*
