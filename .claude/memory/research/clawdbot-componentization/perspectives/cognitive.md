# 認知研究員 報告

**視角 ID**: cognitive
**執行時間**: 2026-01-27
**主題**: Clawdbot 組件化策略 - 方法論與思維框架視角

## 核心發現

### 1. 系統呈現清晰的洋蔥架構（Onion Architecture）特徵

Clawdbot 的組件結構展現了從核心領域邏輯向外延伸的分層模式：
- **核心層（Core）**：`src/channels/plugins/types.ts`、`src/memory/`、`src/agents/` 定義了系統的領域概念
- **適配層（Adapters）**：`src/channels/plugins/` 提供通道抽象，`src/infra/` 處理基礎設施關注點
- **應用層（Application）**：`src/gateway/`、`src/auto-reply/` 協調業務流程
- **擴展層（Extensions）**：`extensions/` 提供可插拔的通道實現

這種架構暗示了**可以沿著同心圓邊界進行組件切割**。

### 2. Plugin SDK 已經是一個成熟的邊界抽象

`src/plugin-sdk/index.ts`（371 行）是系統最大的匯出模組之一，它暴露了：
- 完整的 Channel Plugin 介面（`ChannelPlugin`、`ChannelAdapter` 系列）
- 配置 Schema 建構工具（`buildChannelConfigSchema`）
- 工具與 Hook 系統（`ClawdbotPluginToolFactory`、`HookEntry`）
- 跨通道的正規化函數（`normalizeChannelId`、`resolveChannelEntryMatch`）

**洞察**：這個 SDK 已經定義了明確的**契約邊界（Contract Boundary）**。

### 3. Memory 系統展現獨立子系統特徵

`src/memory/` 模組（35 個檔案）包含完整的向量搜尋能力、多提供者嵌入抽象、Session 與檔案同步機制。幾乎不依賴其他業務邏輯，是**獨立套件（Standalone Package）**的理想候選。

### 4. Gateway 是系統的編排核心，但承載過多職責

`src/gateway/` 目錄負責 WebSocket 協議處理、Session 管理、Lane 與並發控制、通道協調等，違反了**單一職責原則（Single Responsibility Principle）**。

### 5. Extensions 機制驗證了外掛化架構的可行性

分析 29 個 `extensions/` 目錄發現每個擴展都是獨立的 npm package，通過 `clawdbot.extensions` 字段聲明入口點，依賴 `clawdbot` 的 `plugin-sdk` 匯出。

### 6. Auto-Reply 系統是高耦合的流程協調器

`src/auto-reply/` 強烈依賴 `agents/`、`channels/`、`config/`、`memory/`，是**跨領域協調（Cross-Domain Orchestration）**的體現，不適合獨立打包。

## 詳細分析

### 領域邊界識別（Bounded Contexts）

應用 **Domain-Driven Design（DDD）**的 Bounded Context 概念：

#### 1. Messaging Context（訊息上下文）
- **邊界標記**：`src/channels/`、`extensions/*/`
- **核心概念**：`ChannelPlugin`、`ChannelAdapter`、`MessageEnvelope`
- **內聚性**：高
- **重用潛力**：**高** - 可作為 `@clawdbot/channels-core` 獨立套件

#### 2. Memory & Search Context（記憶與搜尋上下文）
- **邊界標記**：`src/memory/`
- **核心概念**：`MemoryManager`、`EmbeddingProvider`、`VectorIndex`
- **內聚性**：極高
- **重用潛力**：**極高** - 可作為 `@clawdbot/memory` 獨立套件

#### 3. Agent Runtime Context（Agent 執行時上下文）
- **邊界標記**：`src/agents/`（292 個檔案）
- **核心概念**：`AgentTool`、`ModelConfig`、`AuthProfile`、`Sandbox`
- **內聚性**：中
- **重用潛力**：**中** - 需要進一步拆分

#### 4. Gateway & Protocol Context（閘道與協議上下文）
- **邊界標記**：`src/gateway/`
- **內聚性**：低（混合協議、編排、策略）
- **重用潛力**：**低** - 是應用特定的編排層

#### 5. Infrastructure Context（基礎設施上下文）
- **邊界標記**：`src/infra/`
- **內聚性**：低（雜項工具集合）
- **重用潛力**：**高** - 可拆分為多個小型工具庫

### 抽象層次分析

#### 層次 1：Protocol & Primitives
- **穩定性**：極高（變更頻率低）
- **建議**：保持在核心，通過 SDK 暴露

#### 層次 2：Domain Logic
- **穩定性**：中（隨功能演進）
- **建議**：**優先組件化目標**

#### 層次 3：Application Orchestration
- **穩定性**：低（頻繁變更）
- **建議**：保留在主專案

#### 層次 4：Infrastructure Adapters
- **穩定性**：高
- **建議**：可選擇性外掛化

## 組件化思維框架

### 框架 1：洋蔥剝離法（Onion Peeling Strategy）

**原則**：從外層向內層依次剝離可獨立組件。

```
┌─────────────────────────────────────────┐
│ Extensions（已獨立）                      │
├─────────────────────────────────────────┤
│ Plugin SDK（可獨立） ← 下一步             │
├─────────────────────────────────────────┤
│ Domain Services（Memory, Channels）       │
│ ← 重點拆分層                              │
├─────────────────────────────────────────┤
│ Application Core（Gateway, Auto-Reply）   │
│ ← 保留主專案                              │
└─────────────────────────────────────────┘
```

### 框架 2：Strangler Fig Pattern（絞殺者模式）

**適用場景**：漸進式重構，避免大爆炸式改寫。

```
主專案（Clawdbot）
  ├─ 新套件 @clawdbot/memory （新實現）
  │   └─ 舊程式碼逐步遷移
  └─ src/memory/ （舊實現，逐步移除）
      └─ 透過 facade 轉發到新套件
```

### 框架 3：Contract-First Design（契約優先設計）

**原則**：在拆分前先定義清晰的公開 API。

```typescript
// @clawdbot/memory/contract.ts
export interface MemoryService {
  search(query: string, options?: SearchOptions): Promise<SearchResult[]>;
  index(documents: Document[]): Promise<void>;
  configure(config: MemoryConfig): void;
  initialize(): Promise<void>;
  dispose(): Promise<void>;
}
```

### 框架 4：三維度評估框架

#### 維度 1：內聚性（Cohesion）
**問題**：這些程式碼是否因為「相同原因」而變更？

#### 維度 2：耦合性（Coupling）
**問題**：拆分後需要多少依賴注入？
- 耦合度 < 3 個主要依賴：可直接拆分
- 耦合度 > 5 個：需要先解耦

#### 維度 3：重用性（Reusability）
**問題**：其他專案是否可能需要這個組件？

### 重用性評估矩陣

| 組件 | 內聚性 | 耦合性 | 重用性 | 拆分優先級 |
|------|--------|--------|--------|-----------|
| `src/memory/` | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | **P0** |
| `src/channels/plugins/` | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | **P1** |
| `src/plugin-sdk/` | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | **P0** |
| `src/agents/tools/` | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | **P2** |
| `src/infra/` | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | **P2** |
| `src/gateway/` | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | **P3** |
| `src/auto-reply/` | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | **P3** |

## 建議與洞察

### 階段性拆分路線圖

#### Phase 1：基礎建設（1-2 週）
1. 建立 Monorepo 結構
2. 設定 Workspace 工具鏈
3. 建立 CI/CD Pipeline

#### Phase 2：Memory 組件化（2-3 週）
1. 定義契約
2. 建立套件骨架
3. 遷移核心功能
4. 處理依賴
5. 發布與整合

#### Phase 3：Plugin SDK 分離（1-2 週）
1. 提取 SDK
2. 版本策略
3. 文檔與範例

#### Phase 4：Channels SDK（2-3 週）
1. 整合現有通道
2. 標準化介面
3. 文檔化最佳實踐

### 關鍵成功因素

1. **介面穩定性承諾** - 使用 `@beta`、`@experimental` 標記不穩定 API
2. **測試覆蓋率要求** - 每個套件獨立測試覆蓋率 > 80%
3. **文檔驅動開發** - API 文檔必須在程式碼前完成
4. **向後相容性保證** - 主版本號不變時不破壞 API

### 認知負荷理論考量

每個開發者的工作記憶有限（約 7±2 個項目）。當前專案有 67 個頂層目錄，遠超認知負荷上限。

**組件化好處**：
- 開發者只需理解自己工作的套件
- 清晰的介面契約降低心智模型複雜度
- 獨立測試提供快速反饋迴路

### 康威定律考量

根據團隊規模調整拆分粒度：
- 1-3 人：保持 Monolith，僅拆分 Memory + Plugin SDK
- 4-8 人：完整拆分
- 8+ 人：可考慮 Microservices

### 長期願景：平台化

**當前狀態**：Clawdbot 是一個應用
**目標狀態**：Clawdbot 成為平台

**平台特徵**：
1. 核心最小化
2. 插件生態
3. 市場機制
4. 多租戶支援

## 信心度

高 - 基於 DDD 方法論和認知負荷理論分析

---
*由認知研究員視角產出*
