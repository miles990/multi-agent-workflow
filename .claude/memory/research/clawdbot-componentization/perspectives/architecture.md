# 架構分析師 報告

**視角 ID**: architecture
**執行時間**: 2026-01-27
**主題**: Clawdbot 組件化拆分策略

## 核心發現

1. **高度模組化的 Channel Plugin 架構** - 專案已經實現了良好的 Channel 抽象層，所有 messaging channels（Telegram、Discord、Slack、Signal、iMessage、WhatsApp、LINE）都透過統一的 `ChannelPlugin` 介面實作，具備高度可拆分性。

2. **清晰的分層架構** - 系統採用典型的三層架構：
   - **基礎設施層** (`infra/`) - 系統級功能（ports、env、state、heartbeat、discovery）
   - **核心業務層** (`agents/`, `gateway/`, `channels/`, `auto-reply/`) - Agent 執行、Gateway server、Channel 抽象
   - **整合層** (`plugins/`, `telegram/`, `discord/`, `slack/` 等) - 具體實作與第三方整合

3. **Plugin SDK 已經存在** - 專案已經導出 `plugin-sdk` 模組（見 `package.json` exports），提供了 200+ 個公開 API，包括完整的 Channel、Config、Gateway 介面。

4. **強耦合的 Agent 執行引擎** - `agents/` 模組包含 292 個檔案，與 Pi Agent Core 深度整合，依賴關係複雜（593 個跨模組 import），是組件化的最大挑戰。

## 詳細分析

### 1. 核心模組邊界識別

專案包含 49 個第一層模組，可分為以下核心群組：

#### A. Channel 抽象層（可拆分性：★★★★★）
```
channels/
├── plugins/          # Channel plugin 註冊與類型定義
│   ├── types.plugin.ts    # ChannelPlugin 介面
│   ├── types.adapters.ts  # 16 種 Adapter 介面
│   ├── types.core.ts      # 核心類型
│   └── catalog.ts         # Plugin 註冊機制
├── dock.ts           # 輕量級 Channel metadata
├── registry.ts       # Channel 註冊表
└── allowlists/       # 存取控制抽象
```

**關鍵發現**：
- 所有 Channel 都實作 `ChannelPlugin<ResolvedAccount>` 介面
- 提供 17 種 Adapter（Auth, Config, Gateway, Messaging, Security, Streaming, Threading 等）
- 已經有清晰的邊界，64 個檔案中僅 195 個跨模組依賴
- `plugin-sdk/index.ts` 已導出完整 Channel API

#### B. 具體 Channel 實作（可拆分性：★★★★☆）
```
telegram/      # 79 files
discord/       # 42 files
slack/         # 36 files
line/          # 36 files
signal/        # 24 files
imessage/      # 15 files
whatsapp/      # 4 files (抽象定義，實作在 web/)
```

#### C. Gateway Server（可拆分性：★★★☆☆）
- 127 個檔案，499 個跨模組依賴（高耦合）
- 核心職責：WebSocket server、session 管理、agent 調度
- 與 `agents/`、`channels/`、`plugins/` 深度整合

#### D. Agent 執行引擎（可拆分性：★☆☆☆☆）
- 292 個檔案，593 個跨模組依賴（最高）
- 與 `@mariozechner/pi-agent-core` 深度綁定
- 工具系統（`tools/`）與 Gateway、Channels 強耦合

#### E. 基礎設施層（可拆分性：★★★★☆）
- 149 個檔案，相對獨立
- 提供系統級功能，可重用性高

#### F. Memory 系統（可拆分性：★★★★★）
- 35 個檔案，高度自包含
- 支援 OpenAI、Gemini embeddings
- 可獨立拆分為 memory/RAG library
- 僅依賴 `config/` 和 `logging/`

### 2. 依賴關係分析

#### 依賴矩陣（跨模組 import 數量）
```
             gateway  channels  agents  infra  auto-reply
gateway         -       116      215     64      13
channels       64        -       195     28      19
agents        215       195       -      148     72
infra          -         28      148     -       8
auto-reply    13        19       72      8       -
```

#### 高耦合區域
1. **agents ↔ gateway**（215 + 215 = 430 個依賴）
2. **agents ↔ channels**（195 + 195 = 390 個依賴）
3. **agents 內部複雜度**（593 個內部依賴）

#### 低耦合模組（獨立性高）
1. **memory/** - 僅依賴 config、logging
2. **infra/net/ssrf.ts** - SSRF 防護，完全獨立
3. **infra/ports.ts** - Port 管理，可獨立拆分
4. **logging/** - 日誌系統，僅依賴 tslog

### 3. 可拆分組件識別

#### 立即可拆分（低風險）

##### 3.1 Memory/RAG Library
**套件名稱**: `@clawdbot/memory`
- 獨立的 RAG/Memory 解決方案
- 支援 hybrid search（BM25 + Vector）
- 可用於其他 AI 專案

##### 3.2 Infrastructure Utilities
**套件名稱**: `@clawdbot/infra`
- 通用的系統工具集
- 可重用於任何 Node.js 專案

##### 3.3 Channel Plugin SDK
**套件名稱**: `@clawdbot/channel-sdk`
- 讓第三方開發自定義 Channel plugin
- 統一的 Channel 開發介面

#### 中等複雜度拆分

##### 3.4 各 Channel 實作
**套件名稱**: `@clawdbot/channel-telegram`, `@clawdbot/channel-discord` 等
- 每個 Channel 模組相對獨立
- 需要 `channels/` 抽象層作為 peer dependency

#### 高複雜度拆分

##### 3.5 Gateway Server Core
- 與 `agents/` 深度耦合
- 需要定義 `SessionManager`、`PluginLoader` 介面
- 預估工作量: 4-6 週

##### 3.6 Agent Execution Engine
- 292 個檔案，593 個內部依賴
- 需要定義 `AgentExecutor`、`ToolRegistry` 介面
- 預估工作量: 8-12 週

### 4. 設計模式分析

#### 4.1 Plugin Architecture
專案使用 **Plugin Registry** 模式，支援動態載入 plugins

#### 4.2 Adapter Pattern
Channel 系統使用 **Adapter Pattern**，統一介面抽象不同 messaging platforms

#### 4.3 Factory Pattern
Agent tools 使用 **Factory Pattern**，支援延遲初始化和依賴注入

#### 4.4 Observer Pattern
使用事件系統處理跨模組通知，但缺乏統一的事件匯流排

## 組件化建議

### 階段 1：立即可執行（1-2 週）
1. 拆分 `@clawdbot/memory`
2. 拆分 `@clawdbot/infra`
3. 擴充 `@clawdbot/plugin-sdk`

### 階段 2：中期重構（4-6 週）
4. 定義核心介面（`SessionManager`, `AgentExecutor`, `ChannelAdapter`）
5. 重構 Gateway Server 使用依賴注入
6. 拆分 Telegram Channel（作為 pilot）

### 階段 3：長期架構升級（8-12 週）
7. 拆分其他 Channels
8. 實作 EventBus 解耦 agents ↔ channels
9. 抽取 Agent Runtime 核心介面

### 建議的 Monorepo 結構
```
clawdbot/
├── packages/
│   ├── core/              # 核心介面與類型
│   ├── gateway/           # Gateway server
│   ├── agent-runtime/     # Agent 執行引擎
│   ├── memory/            # Memory/RAG
│   ├── infra/             # Infrastructure utilities
│   ├── plugin-sdk/        # Plugin 開發 SDK
│   ├── channel-sdk/       # Channel 開發 SDK
│   ├── channel-telegram/  # Telegram channel
│   ├── channel-discord/   # Discord channel
│   └── ...
├── apps/
│   ├── cli/               # clawdbot CLI
│   ├── ios/               # iOS app
│   └── android/           # Android app
└── pnpm-workspace.yaml
```

## 風險與注意事項

### 技術風險

1. **循環依賴問題** - 拆分過程中可能暴露隱藏的循環依賴
   - 解決方案：使用 madge 檢測，引入 interface 層打破循環

2. **型別系統複雜度** - TypeScript 型別推斷在跨 package 時可能失效
   - 解決方案：使用 Declaration Merging，提供明確的型別導出

3. **測試覆蓋率下降** - 拆分後整合測試可能失效
   - 解決方案：建立 E2E 測試套件，使用 vitest workspace 模式

### 相容性風險

1. **Breaking Changes** - 既有用戶的配置可能失效
   - 解決方案：提供 migration scripts，維持向後相容的 API

2. **Plugin Ecosystem 衝擊** - 第三方 plugins 可能失效
   - 解決方案：維護舊 API 至少 2 個 major versions

### 維護風險

1. **文檔同步** - 多 packages 的文檔容易過期
2. **版本管理複雜度** - Monorepo 中多 packages 的版本同步困難

## 組件化成功指標

### 技術指標
- ✅ 每個 package 的依賴數量 < 10
- ✅ 跨 package 循環依賴 = 0
- ✅ 測試覆蓋率維持 >70%

### 業務指標
- ✅ 至少 3 個 packages 被其他專案使用
- ✅ 社群貢獻的 channel plugins > 5

### 開發體驗指標
- ✅ 新增 channel 時間 < 2 天（之前需 1 週）
- ✅ 本地開發啟動時間 < 10 秒

## 信心度

高 - 基於實際程式碼結構分析

---
*由架構分析師視角產出*
