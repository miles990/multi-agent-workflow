# Clawdbot MVP 里程碑規劃（更新版）

**版本**: 2.0
**日期**: 2026-01-27
**更新**: 納入完整記憶系統和 Session 管理

---

## 里程碑總覽

```
Week 1-2    Week 3-4    Week 5      Week 6-7    Week 8      Week 9      Week 10
  │           │           │           │           │           │           │
  ▼           ▼           ▼           ▼           ▼           ▼           ▼
┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐
│M1+M2│───▶│ M3  │───▶│ M4  │───▶│ M5  │───▶│ M6  │───▶│ M7  │───▶│ M8  │
│Skel.│    │Mem. │    │Sess.│    │Core │    │Integ│    │Feat.│    │Rel. │
│+Sec │    │     │    │     │    │     │    │     │    │     │    │     │
└─────┘    └─────┘    └─────┘    └─────┘    └─────┘    └─────┘    └─────┘
```

---

## M1: Skeleton

**週次**: Week 1
**估算工時**: 24 小時
**目標**: 專案基礎建設完成

### 交付物

| 交付物 | 驗收標準 |
|--------|---------|
| 專案結構 | 目錄結構符合設計 |
| 配置系統 | 可載入 YAML 配置 |
| CI/CD | GitHub Actions 通過 |
| SQLite 基礎 | better-sqlite3 + sqlite-vec 可用 |

### 任務清單

- [ ] 初始化 pnpm 專案
- [ ] 配置 TypeScript (tsconfig.json)
- [ ] 配置 ESLint + Prettier
- [ ] 建立目錄結構
- [ ] 實作配置 Schema (Zod)
- [ ] 實作配置載入器
- [ ] 設定 GitHub Actions CI
- [ ] 安裝 better-sqlite3 + sqlite-vec
- [ ] 建立 SQLite 基礎表結構

---

## M2: Security

**週次**: Week 2
**估算工時**: 58 小時
**目標**: 權限系統完成

### 交付物

| 交付物 | 驗收標準 |
|--------|---------|
| Allowlist | 可配置、可查詢 |
| DM Pairing | 配對流程可用 |
| PermissionChecker | 集中化檢查 |
| AuditLogger | 日誌可寫入 |

### 任務清單

- [ ] 實作 Allowlist 管理
- [ ] 實作 DM Pairing
- [ ] 實作 PermissionChecker
- [ ] 實作 AuditLogger
- [ ] 安全測試（100% 覆蓋）

---

## M3: Memory（新增）

**週次**: Week 3-4
**估算工時**: 80 小時
**目標**: 記憶系統完成

### 交付物

| 交付物 | 驗收標準 |
|--------|---------|
| MemoryIndexManager | 可索引、可搜尋 |
| Hybrid Search | 向量 + BM25 搜尋 |
| Multi-Provider | OpenAI/Gemini/Local Fallback |
| Memory Flush | Compaction 前觸發 |

### 任務清單

- [ ] 移植 MemoryIndexManager 核心
- [ ] 實作 sqlite-vec 向量存儲
  - [ ] 表結構（chunks, chunks_vec）
  - [ ] 向量 CRUD 操作
- [ ] 實作 FTS5 全文搜尋
  - [ ] 表結構（chunks_fts）
  - [ ] BM25 搜尋
- [ ] 實作 Hybrid Search
  - [ ] 向量搜尋（70%）
  - [ ] BM25 搜尋（30%）
  - [ ] 結果合併
- [ ] 實作 Embedding Provider
  - [ ] OpenAI Provider
  - [ ] Gemini Provider
  - [ ] Local Provider (node-llama-cpp)
  - [ ] Fallback 機制
- [ ] 實作 Embedding Cache
  - [ ] Hash-based 變化偵測
  - [ ] 避免重複嵌入
- [ ] 實作 Memory Flush Hook
- [ ] 記憶系統測試

### 驗收檢查

```bash
# 驗收命令
pnpm test:memory  # 記憶系統測試通過

# 手動驗收
# 1. 索引文字 → 可搜尋
# 2. Hybrid Search 結果合理
# 3. Provider Fallback 正常
```

---

## M4: Session（新增）

**週次**: Week 5
**估算工時**: 56 小時
**目標**: Session 管理完成

### 交付物

| 交付物 | 驗收標準 |
|--------|---------|
| Session Store | 可讀寫 Session |
| Transcript Store | 可記錄對話 |
| Session Compaction | 長對話可壓縮 |
| LRU Cache | 快取有效 |

### 任務清單

- [ ] 實作 SessionEntry 類型
- [ ] 實作 Session Store
  - [ ] CRUD 操作
  - [ ] 持久化（JSON）
- [ ] 實作 Transcript Store
  - [ ] JSONL 追加
  - [ ] 讀取歷史
  - [ ] Delta Tracking
- [ ] 實作 Session Compaction
  - [ ] Token 計數
  - [ ] 壓縮閾值檢查
  - [ ] 觸發 Memory Flush
  - [ ] Transcript 壓縮
- [ ] 實作 LRU Cache
  - [ ] TTL 機制（45s）
  - [ ] 容量限制
  - [ ] 自動清理
- [ ] 實作檔案鎖定
  - [ ] proper-lockfile 整合
  - [ ] 並發控制
- [ ] 實作 Session Memory Hook
- [ ] Session 系統測試

### 驗收檢查

```bash
# 驗收命令
pnpm test:session  # Session 測試通過

# 手動驗收
# 1. Session 重啟後保留
# 2. Transcript 可查詢
# 3. Compaction 在閾值觸發
# 4. 並發寫入不衝突
```

---

## M5: Core

**週次**: Week 6-7
**估算工時**: 80 小時
**目標**: Claude Code 整合完成

### 交付物

| 交付物 | 驗收標準 |
|--------|---------|
| Claude Adapter | 可調用 Claude Code |
| Context Builder | 整合 Memory 搜尋 |
| Tool API | HTTP 端點可用 |
| Response Streaming | 可串流回覆 |

### 任務清單

- [ ] 設計 Adapter 介面
- [ ] 實作 subprocess spawn
- [ ] 實作 Context Builder
  - [ ] 整合 Session 上下文
  - [ ] 整合 Memory 搜尋結果
  - [ ] 構建完整 prompt
- [ ] 實作 Tool API HTTP 端點
- [ ] 實作 Response Streaming
- [ ] 實作錯誤處理
- [ ] 整合測試

### 驗收檢查

```bash
# 驗收命令
pnpm test:integration  # 整合測試通過

# 手動驗收
# 1. API 成功調用 Claude Code
# 2. Context 包含相關記憶
# 3. Tool 回調正常
```

---

## M6: Integration

**週次**: Week 8
**估算工時**: 46 小時
**目標**: Telegram Bot 上線

### 交付物

| 交付物 | 驗收標準 |
|--------|---------|
| Grammy Bot | Long Polling 運作 |
| 消息處理 | 可處理文字訊息 |
| 命令處理 | /start, /pair, /help |
| Typing 控制 | 顯示「正在輸入」 |

### 任務清單

- [ ] Grammy Bot 設定
- [ ] 消息處理器（整合完整流程）
- [ ] 命令處理器
- [ ] Typing 控制
- [ ] 整合測試

---

## M7: Feature Complete

**週次**: Week 9
**估算工時**: 40 小時
**目標**: 所有功能完成

### 交付物

| 交付物 | 驗收標準 |
|--------|---------|
| CLI 工具 | start, config check |
| 文檔 | README, 架構文檔 |
| 整合測試 | 核心流程通過 |

### 任務清單

- [ ] CLI 工具
- [ ] README.md
- [ ] architecture.md
- [ ] deployment.md
- [ ] 整合測試

---

## M8: Release

**週次**: Week 10
**估算工時**: 50 小時
**目標**: 生產就緒

### 交付物

| 交付物 | 驗收標準 |
|--------|---------|
| E2E 測試 | 核心流程通過 |
| 效能測試 | 符合 SLA |
| 安全測試 | 無高危漏洞 |
| 部署指南 | 可依指南部署 |

### 發布標準

| 檢查項 | 通過標準 |
|--------|---------|
| 測試覆蓋 | > 80% |
| E2E 測試 | 100% 通過 |
| 效能 | P95 < 10s |
| 安全 | 無 HIGH/CRITICAL |
| Memory Search | Recall > 80% |

---

## 工時總結

| 里程碑 | 工時 | 週數 |
|--------|------|------|
| M1: Skeleton | 24h | W1 |
| M2: Security | 58h | W2 |
| M3: Memory | 80h | W3-4 |
| M4: Session | 56h | W5 |
| M5: Core | 80h | W6-7 |
| M6: Integration | 46h | W8 |
| M7: Feature Complete | 40h | W9 |
| M8: Release | 50h | W10 |
| **總計** | **434h** | **10 週** |

---

**規劃更新時間**: 2026-01-27
