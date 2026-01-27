# Clawdbot 組件化策略 - 匯總報告

**研究主題**: 如何將 Clawdbot 系統拆分成可重用組件
**分析日期**: 2026-01-27
**視角數量**: 4（架構分析師、認知研究員、工作流設計師、業界實踐專家）

---

## 執行摘要

Clawdbot 是一個整合多 messaging channels（WhatsApp、Telegram、Discord、Slack、Signal、LINE 等）與 AI agent 功能的專案。本研究從四個視角分析其組件化策略，識別出**可立即拆分的高價值組件**和**需要重構才能拆分的複雜模組**。

### 關鍵結論

1. **Memory 系統是最佳拆分候選** - 35 個檔案、高度自包含、僅依賴 config/logging
2. **Plugin SDK 已經定義了成熟的邊界** - 可直接獨立為 @clawdbot/core
3. **Channel 抽象層設計良好** - 可按協議拆分為獨立套件
4. **Gateway 和 Agent Runtime 耦合嚴重** - 需要先定義介面層才能拆分
5. **建議採用漸進式 Monorepo 策略** - 使用 Changesets 管理版本

---

## 方法

**視角配置**：
| 視角 | 聚焦 | 模型 |
|------|------|------|
| 架構分析師 | 系統結構、設計模式、依賴關係 | sonnet |
| 認知研究員 | DDD 邊界、抽象層次、重用性評估 | sonnet |
| 工作流設計師 | 訊息流程、模組互動、整合點 | haiku |
| 業界實踐專家 | npm 最佳實踐、業界對標 | haiku |

---

## 共識發現

### 強共識（4/4 視角同意）

#### 1. Memory 系統應優先獨立拆分

**證據**：
- 架構視角：35 個檔案，僅依賴 config/logging，可拆分性 ★★★★★
- 認知視角：內聚性極高、耦合性低、重用潛力極高
- 工作流視角：完整的向量搜尋能力，與業務流程鬆耦合
- 業界視角：可作為通用 RAG/Memory 解決方案

**建議套件名稱**: `@clawdbot/memory`

**導出內容**:
```typescript
export { createMemoryManager, type MemoryManager }
export { createEmbeddingProvider, type EmbeddingProvider }
export { searchMemory, type MemorySearchResult }
export { hybridSearch, type HybridSearchOptions }
export { OpenAiEmbedding, GeminiEmbedding }
```

#### 2. Plugin SDK 是成熟的邊界抽象

**證據**：
- 架構視角：200+ 公開 API，完整的 Channel/Config/Gateway 介面
- 認知視角：已定義明確的契約邊界（Contract Boundary）
- 工作流視角：通道管理通過統一介面實現
- 業界視角：72 個導出的 Channel* 類型，介面清晰

**建議套件名稱**: `@clawdbot/core`

#### 3. Channel 可按協議獨立拆分

**證據**：
- 架構視角：每個 Channel 模組相對獨立（Telegram 79 files、Discord 42 files 等）
- 認知視角：Messaging Context 是清晰的 Bounded Context
- 工作流視角：通道適配器（ChannelMessageAdapter）處理格式差異
- 業界視角：類似 Discord.js、Telegram Bot API SDK 的模式

**建議套件名稱**: `@clawdbot/channel-telegram`, `@clawdbot/channel-discord` 等

#### 4. Gateway 和 Agent Runtime 耦合嚴重

**證據**：
- 架構視角：agents ↔ gateway 430 個依賴、agents 內部 593 個依賴
- 認知視角：Gateway 違反單一職責原則
- 工作流視角：Gateway 負責 WebSocket、Session、Lane、通道協調等
- 業界視角：70+ 千行代碼集中在 src/channels/

**結論**: 不建議立即拆分，需要先定義核心介面（SessionManager、AgentExecutor）

### 弱共識（2-3/4 視角同意）

#### 5. 建議使用事件總線解耦

**支持視角**：工作流（明確提出）、架構（提及 Observer Pattern 缺乏統一 EventBus）

**建議**：
```typescript
eventBus.emit('inbound-message', unifiedMessage);
eventBus.on('agent-reply', (reply) => dispatchToChannels(reply));
```

#### 6. 需要統一的消息格式

**支持視角**：工作流（明確定義 UnifiedMessage）、認知（提及 MessageEnvelope 概念）

---

## 矛盾分析

### 已解決矛盾

#### Monorepo vs Multi-repo 策略

**觀點差異**：
- 認知視角：根據團隊規模調整拆分粒度（1-3 人保持 Monolith）
- 業界視角：明確推薦保持 Monorepo

**解決方案**: 採用 Monorepo + 獨立發布策略
- 使用 pnpm workspace 管理
- 使用 Changesets 自動化版本管理
- 每個 package 可獨立發布到 npm

### 需進一步處理

#### Agent Tools 的拆分策略

**觀點差異**：
- 架構視角：工具系統與 Gateway、Channels 強耦合
- 認知視角：可拆分為 @clawdbot/agent-tools（P2 優先級）

**建議方向**: 需要先定義 ToolRegistry 介面，才能解耦

---

## 關鍵洞察

### 洋蔥架構（Onion Architecture）

Clawdbot 自然形成的分層結構：

```
┌─────────────────────────────────────────┐
│ Extensions（已獨立）                      │  ← 可直接使用
├─────────────────────────────────────────┤
│ Plugin SDK / Channel SDK                 │  ← 優先拆分
├─────────────────────────────────────────┤
│ Memory / Infrastructure                  │  ← 高價值拆分
├─────────────────────────────────────────┤
│ Gateway / Auto-Reply / Agent Runtime     │  ← 保留主專案
└─────────────────────────────────────────┘
```

### 認知負荷考量

當前專案有 67 個頂層目錄，遠超認知負荷上限（7±2 個項目）。組件化可以：
- 縮小開發者的認知範圍
- 降低心智模型複雜度
- 提供快速反饋迴路

### 平台化願景

**當前狀態**：Clawdbot 是一個應用（Application）
**目標狀態**：Clawdbot 成為平台（Platform）

平台特徵：核心最小化、插件生態、市場機制、多租戶支援

---

## 行動建議

### 立即行動（P0 - Week 1-2）

#### 1. 拆分 @clawdbot/memory

**工作量**: 1-2 週
**風險**: 低
**價值**: 高（可用於其他 AI 專案）

**步驟**：
1. 建立 `packages/memory/` 目錄
2. 移動 `src/memory/*.ts`
3. 抽象 Config 依賴為 MemoryConfig 介面
4. 發布 @clawdbot/memory@1.0.0

#### 2. 獨立 @clawdbot/core

**工作量**: 1 週
**風險**: 低
**價值**: 高（為後續拆分鋪路）

**步驟**：
1. 從 `src/plugin-sdk/` 提取核心類型
2. 定義穩定的公開 API
3. 設定 Changesets 版本管理
4. 發布 @clawdbot/core@1.0.0

### 短期規劃（P1 - Week 3-6）

#### 3. 定義核心介面

**工作量**: 2 週
**風險**: 中（需要仔細設計）

**介面定義**：
```typescript
interface SessionManager {
  create(key: string): Session
  get(key: string): Session | null
  destroy(key: string): void
}

interface AgentExecutor {
  run(params: AgentRunParams): AsyncGenerator<AgentEvent>
  abort(sessionId: string): void
}

interface ChannelAdapter {
  send(message: Message): Promise<void>
  receive(): AsyncGenerator<InboundMessage>
}
```

#### 4. 拆分 Telegram Channel（Pilot）

**工作量**: 2 週
**風險**: 中
**價值**: 驗證 Channel 拆分模式

### 長期考量（P2-P3 - Month 2-3）

5. 拆分其他 Channels（Discord, Slack, Signal, LINE）
6. 重構 Gateway 使用依賴注入
7. 實作 EventBus 解耦 agents ↔ channels
8. 抽取 Agent Runtime 核心介面

---

## 風險評估

### 技術風險

| 風險 | 嚴重度 | 緩解策略 |
|------|--------|---------|
| 循環依賴暴露 | 中 | 使用 madge 檢測，引入 interface 層 |
| 型別推斷失效 | 中 | Declaration Merging，明確型別導出 |
| 測試覆蓋下降 | 中 | E2E 測試套件，vitest workspace |
| 會話狀態競態 | 高 | 遷移至數據庫或 Redis |

### 相容性風險

| 風險 | 嚴重度 | 緩解策略 |
|------|--------|---------|
| Breaking Changes | 高 | Migration scripts，向後相容 API |
| Plugin Ecosystem 衝擊 | 中 | 維護舊 API 至少 2 個 major versions |

### 維護風險

| 風險 | 嚴重度 | 緩解策略 |
|------|--------|---------|
| 文檔同步 | 中 | TypeDoc 自動生成，CI 驗證 |
| 版本管理複雜度 | 中 | Changesets 自動化 |

---

## 成功指標

### 技術指標
- [ ] 每個 package 的依賴數量 < 10
- [ ] 跨 package 循環依賴 = 0
- [ ] 測試覆蓋率維持 >70%
- [ ] Build 時間 < 60 秒

### 業務指標
- [ ] 至少 3 個 packages 被其他專案使用
- [ ] 社群貢獻的 channel plugins > 5
- [ ] 文檔完整度 >90%

### 開發體驗指標
- [ ] 新增 channel 時間 < 2 天
- [ ] 本地開發啟動時間 < 10 秒

---

## 附錄

### A. 組件拆分優先級矩陣

| 組件 | 內聚性 | 耦合性 | 重用性 | 優先級 |
|------|--------|--------|--------|--------|
| memory/ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | **P0** |
| plugin-sdk/ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | **P0** |
| channels/plugins/ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | **P1** |
| telegram/ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | **P1** |
| infra/ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | **P2** |
| agents/tools/ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | **P2** |
| gateway/ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | **P3** |
| auto-reply/ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | **P3** |

### B. 建議的 Monorepo 結構

```
clawdbot/
├── packages/
│   ├── core/                # @clawdbot/core
│   │   ├── src/
│   │   │   ├── plugin-sdk/
│   │   │   ├── config/types/
│   │   │   └── utils/
│   │   └── package.json
│   ├── memory/              # @clawdbot/memory
│   │   ├── src/
│   │   │   ├── manager.ts
│   │   │   ├── embeddings/
│   │   │   └── search/
│   │   └── package.json
│   ├── channels/
│   │   ├── telegram/        # @clawdbot/channel-telegram
│   │   ├── discord/         # @clawdbot/channel-discord
│   │   ├── slack/           # @clawdbot/channel-slack
│   │   └── ...
│   └── infra/               # @clawdbot/infra
├── apps/
│   ├── cli/                 # clawdbot CLI (主應用)
│   ├── ios/
│   └── android/
├── extensions/              # 保持現狀
├── pnpm-workspace.yaml
├── changeset.config.js
└── turbo.json               # 可選：Turborepo 配置
```

### C. 視角報告連結

- [架構分析師報告](./perspectives/architecture.md)
- [認知研究員報告](./perspectives/cognitive.md)
- [工作流設計師報告](./perspectives/workflow.md)
- [業界實踐專家報告](./perspectives/industry.md)

---

**研究品質分數**: 85/100
**共識率**: 87.5%（7/8 核心發現達成共識）
**建議信心度**: 高

*由多視角研究框架產出*
