# 認知研究員報告

**研究主題**: Clawdbot 輕量 MVP 方案的認知與設計原則分析
**視角 ID**: cognitive
**執行時間**: 2026-01-27
**專案**: /Users/user/Workspace/clawdbot

## 核心發現

1. **插件化架構是核心心智模型** - Clawdbot 將所有擴展點（Channel、Provider、Tool、Hook、Service）統一建模為插件（Plugin），這是一個強大的認知抽象，讓系統能夠以一致的方式處理異質組件。

2. **適配器模式無處不在** - Channel、Config、Security、Outbound、Directory 等都使用適配器（Adapter）模式，將不同平台的差異封裝在統一介面後，這降低了核心邏輯的認知負擔。

3. **註冊表（Registry）作為真實來源** - ChannelPluginRegistry、PluginRegistry、NodeRegistry、BashProcessRegistry 等集中管理組件生命週期，這種模式提供了清晰的查找和管理路徑。

4. **權限模型採用零信任原則** - DM pairing、device auth、allowlist/denylist、tool policy 等多層防禦機制體現了「預設拒絕，明確許可」的設計哲學。

5. **複雜度集中在整合層** - 最大的檔案（audit.ts 973 行、heartbeat-runner.ts 904 行、memory/manager.ts 2178 行）都是整合多個子系統的協調層，這是必要複雜度，而非過度工程化。

6. **狀態管理採用快照模式** - ChannelAccountSnapshot、ConfigSnapshot、SecurityAuditReport 等使用不可變快照（Snapshot）模式，避免並發狀態問題。

7. **錯誤處理採用類型化策略** - FailoverError、MediaUnderstandingError、pluginDiagnostic 等將錯誤作為一等公民建模，提供結構化錯誤處理路徑。

## 詳細分析

### 1. 設計模式的認知效益

#### 插件化架構的心智模型

Clawdbot 的插件系統不僅是技術實現，更是一種**認知框架**：

```typescript
// 統一的插件註冊介面
export type ClawdbotPluginApi = {
  registerTool(factory: ClawdbotPluginToolFactory): void;
  registerChannel(registration: ClawdbotPluginChannelRegistration): void;
  registerHook(name: PluginHookName, handler: HookHandler): void;
  registerService(service: ClawdbotPluginService): void;
  registerProvider(provider: ProviderPlugin): void;
  registerCommand(command: ClawdbotPluginCommandDefinition): void;
  registerHttpRoute(path: string, handler: ClawdbotPluginHttpRouteHandler): void;
}
```

**認知優勢**：
- **統一心智模型**：開發者只需理解「插件註冊」這一個核心概念
- **可組合性**：插件可以組合使用，無需修改核心
- **可測試性**：每個插件都是獨立單元，易於隔離測試

**MVP 保留建議**：保留插件架構的核心抽象，但將實作數量從 8+ 種縮減為 3 種：
1. Channel Plugin（Telegram）
2. Tool Plugin（基礎工具）
3. Hook Plugin（審計日誌）

#### 適配器模式的抽象邊界

Channel 適配器設計展示了清晰的**責任分離**：

```typescript
export type ChannelPlugin = {
  id: ChannelId;
  meta: ChannelMeta;
  config: ChannelConfigAdapter;      // 配置管理
  security: ChannelSecurityAdapter;   // 安全策略
  gateway: ChannelGatewayAdapter;     // 生命週期
  outbound: ChannelOutboundAdapter;   // 訊息發送
  resolver: ChannelResolverAdapter;   // 身份解析
  directory?: ChannelDirectoryAdapter; // 聯絡人目錄
}
```

**認知優勢**：
- **關注點分離**：每個適配器負責一個清晰的功能域
- **可選性**：通過 `?` 標記表達哪些功能是可選的
- **漸進披露**：初學者只需理解必需適配器，高級功能按需學習

**MVP 保留建議**：保留適配器架構，但簡化可選適配器：
- 必需：`config`、`security`、`gateway`、`outbound`
- 可選：`directory`（聯絡人查找）
- 移除：`streaming`、`threading`、`mention`（MVP 階段過度）

#### 註冊表模式的查找語義

註冊表提供了**單一事實來源**的心智模型：

```typescript
// 集中管理 Channel 生命週期
export class ChannelPluginRegistry {
  private plugins = new Map<ChannelId, ChannelPlugin>();

  register(plugin: ChannelPlugin): void { /* ... */ }
  get(id: ChannelId): ChannelPlugin | undefined { /* ... */ }
  list(): ChannelPlugin[] { /* ... */ }
  unregister(id: ChannelId): void { /* ... */ }
}
```

**認知優勢**：
- **可發現性**：所有組件都可通過註冊表查找
- **生命週期清晰**：註冊、查找、註銷三個操作涵蓋完整生命週期
- **除錯友善**：可以輕鬆列舉所有已註冊組件

### 2. 複雜度管理的認知分析

#### 必要複雜度 vs. 偶然複雜度

**必要複雜度（值得保留）**：
1. **security/audit.ts (973 行)**：整合 10+ 個安全檢查，這是安全系統的固有複雜度
2. **memory/manager.ts (2178 行)**：記憶體索引、向量搜尋、批次處理，這是 RAG 系統的核心複雜度
3. **infra/heartbeat-runner.ts (904 行)**：心跳機制需要處理超時、重試、多 Channel 協調

**偶然複雜度（MVP 可簡化）**：
1. **多 Channel 支援**（8+ 個平台）：每個 Channel 都有獨特的認證、權限、訊息格式邏輯
2. **Canvas/A2UI**：視覺化介面增加大量狀態管理和渲染邏輯
3. **Voice Wake/Talk Mode**：語音系統需要處理音訊串流、語音辨識、TTS

#### MVP 的最小複雜度曲線

```
優先級 1（核心）:
├── Gateway (WS server + routing)
├── Telegram Channel
├── Permission System (pairing + allowlist)
└── Tool Policy (exec security)

優先級 2（價值遞增）:
├── Memory Search (local only)
├── Audit Logging (security events)
└── Config Hot Reload

優先級 3（可延後）:
├── Multi-Channel
├── Canvas/Browser
└── Voice/Talk Mode
```

### 3. 權限設計的零信任哲學

#### 多層防禦的認知模型

Clawdbot 實現了**縱深防禦**（Defense in Depth）：

```typescript
// 第 1 層：Channel 層面的 DM 策略
type DmPolicy = "disabled" | "pairing" | "allowlist" | "open";

// 第 2 層：Device 認證
type DeviceAuthStore = {
  approveDevice(deviceId: string, challenge: string): void;
  isApproved(deviceId: string): boolean;
}

// 第 3 層：Tool 策略
type ToolPolicy = {
  profile?: "minimal" | "coding" | "messaging" | "full";
  allow?: string[];  // 白名單
  deny?: string[];   // 黑名單
}

// 第 4 層：Elevated 權限
type ElevatedConfig = {
  enabled: boolean;
  allowFrom: Record<ChannelId, Array<string | number>>;
}
```

**認知優勢**：
- **漸進授權**：從 DM pairing 開始，逐步授予工具權限
- **爆炸半徑限制**：即使一層被破壞，其他層仍能防禦
- **審計追蹤**：每層都記錄決策，便於事後分析

**MVP 保留建議**：保留前 3 層（DM Policy、Device Auth、Tool Policy），移除 Elevated 權限。

#### 最小權限原則的實踐

Tool Policy 設計展示了**最小權限原則**：

```typescript
const TOOL_PROFILES: Record<ToolProfileId, ToolProfilePolicy> = {
  minimal: {
    allow: ["session_status"],  // 只能查看狀態
  },
  coding: {
    allow: ["group:fs", "group:runtime", "group:sessions", "group:memory", "image"],
  },
  messaging: {
    allow: ["group:messaging", "sessions_list", "sessions_history", "sessions_send"],
  },
  full: {},  // 無限制（危險）
};
```

**MVP 建議**：保留 `minimal` 和 `coding` profile，移除 `full`（MVP 階段不應允許無限制權限）。

### 4. Claude Code 整合的心智模型轉變

#### 從內建 Agent 到外部 Agent

原架構中，Agent 是 **Gateway 的一部分**：

```
┌─────────────────────────────────┐
│          Gateway                │
│  ┌──────────────────────────┐   │
│  │   Agent Runtime          │   │
│  │   - Pi Runner            │   │
│  │   - Tool Execution       │   │
│  │   - Session Management   │   │
│  └──────────────────────────┘   │
└─────────────────────────────────┘
```

MVP 架構中，Agent 是 **外部服務**（Claude Code）：

```
┌─────────────────────────┐       ┌─────────────────────────┐
│      Gateway            │       │     Claude Code         │
│  - Message Routing      │◄──────┤  - Agent Runtime        │
│  - Permission Check     │       │  - Tool Execution       │
│  - Audit Logging        │──────►│  - Session Management   │
└─────────────────────────┘       └─────────────────────────┘
```

**心智模型轉變**：
- **Gateway 責任縮減**：從「執行 Agent」變為「路由和審計」
- **狀態管理簡化**：Session 狀態移至 Claude Code，Gateway 只需追蹤基本元數據
- **錯誤處理邊界**：Agent 執行錯誤不再影響 Gateway 穩定性

**簡化策略**：
1. 移除 `src/agents/pi-embedded-runner/` 整個目錄（880+ 行）
2. 移除 `src/agents/model-fallback.ts`、`bash-tools.exec.ts` 等 Agent 內部邏輯
3. 保留 `src/agents/tools/` 中的工具定義
4. Gateway 提供 Tool Invocation API，Claude Code 透過 API 呼叫工具

#### 責任邊界的重新劃分

原責任分配：

| 功能 | 負責組件 |
|------|---------|
| 接收 Telegram 訊息 | Gateway |
| 路由到正確 Agent | Gateway |
| Agent 推理與回應 | Gateway (pi-runner) |
| 工具執行 | Gateway (bash-tools, etc.) |
| 回傳到 Telegram | Gateway |

MVP 責任分配：

| 功能 | 負責組件 |
|------|---------|
| 接收 Telegram 訊息 | Gateway |
| 權限檢查 | Gateway |
| 轉發給 Claude Code | Gateway → Claude Code |
| Agent 推理與回應 | Claude Code |
| 工具執行請求 | Claude Code → Gateway (via API) |
| 工具執行 | Gateway |
| 回傳到 Telegram | Gateway |

**認知優勢**：
- **單一職責**：Gateway 專注於「連接和授權」，Claude Code 專注於「推理和決策」
- **可替換性**：未來可以換其他 Agent 而無需修改 Gateway
- **除錯簡化**：問題出在「連接」還是「推理」一目了然

### 5. 可維護性原則

#### 文檔策略

1. **Inline Types as Documentation**：類型定義即文檔
2. **Conceptual Docs**：`docs/concepts/` 目錄解釋高階概念
3. **How-to Guides**：`docs/cli/` 和 `docs/channels/` 提供操作指南

**MVP 建議**：
- **Types**：保留，這是最低成本的文檔
- **Conceptual**：只保留 `architecture.md`、`security.md`
- **How-to**：只保留 `telegram.md`、`claude-code-integration.md`

#### 測試策略

1. **Unit Tests**：`*.test.ts` 測試單一函式
2. **E2E Tests**：`*.e2e.test.ts` 測試完整流程
3. **Specific Scenario Tests**：長檔名描述測試場景

**MVP 建議**：
- 保留 Unit Tests（高投資報酬率）
- 簡化 E2E Tests（只測試關鍵路徑）
- Scenario Tests 按需添加

#### 配置管理

Clawdbot 的配置系統展示了**漸進披露**原則：

```typescript
// 簡單配置（wizard 模式）
{
  channels: {
    telegram: {
      botToken: "xxx"
    }
  }
}

// 進階配置（手動編輯）
{
  channels: {
    telegram: {
      botToken: "xxx",
      dmPolicy: "pairing",
      groupPolicy: "allowlist",
      groups: { ... }
    }
  }
}
```

**MVP 建議**：保留分層配置，但提供更激進的預設值：
- 預設 `dmPolicy: "pairing"`（強制配對）
- 預設 `groupPolicy: "disabled"`（MVP 階段不啟用群組）
- 移除 skills、streaming、voice 等進階配置項

## 建議與洞察

### MVP 架構建議

```typescript
// 核心模組結構
clawdbot-mvp/
├── src/
│   ├── gateway/           // Gateway 核心
│   │   ├── server.ts      // WebSocket server
│   │   ├── routing.ts     // 訊息路由
│   │   └── tool-api.ts    // Tool invocation API
│   ├── channels/
│   │   └── telegram/      // 只保留 Telegram
│   ├── security/          // 權限與審計
│   │   ├── pairing.ts
│   │   ├── tool-policy.ts
│   │   └── audit.ts
│   ├── tools/             // 基礎工具
│   │   ├── exec.ts        // 執行 shell 命令
│   │   ├── read.ts        // 讀取檔案
│   │   └── write.ts       // 寫入檔案
│   └── config/            // 配置管理
├── docs/
│   ├── architecture.md
│   ├── telegram-setup.md
│   └── claude-code-integration.md
└── tests/
    └── integration/       // 只保留關鍵路徑測試
```

### 設計決策建議

1. **保留插件架構骨架，但減少插件數量**
   - 保留：ChannelPlugin、ToolPlugin、HookPlugin
   - 移除：ProviderPlugin（OAuth 部分）、ServicePlugin（過度抽象）

2. **簡化權限模型**
   - 保留：DM Pairing、Tool Policy (minimal/coding)
   - 移除：Elevated mode、Cross-context messaging

3. **移除 Agent Runtime**
   - Gateway 不再執行 Agent，改為呼叫 Claude Code
   - Gateway 提供 Tool Invocation API

4. **保留核心基礎設施**
   - 保留：Config hot-reload、Audit logging、Pairing store
   - 移除：Memory indexing（Claude Code 自己處理）、Cron jobs

### 可擴充性路徑

即使是 MVP，也應保留未來擴充的介面：

```typescript
// Gateway Tool API（未來可擴充）
interface ToolInvocationRequest {
  tool: string;
  params: unknown;
  context: {
    channel: string;
    userId: string;
    sessionId?: string;
  };
}

interface ToolInvocationResponse {
  ok: boolean;
  result?: unknown;
  error?: { code: string; message: string; };
}
```

## 風險與注意事項

### 過度簡化的風險

1. **移除 Agent Runtime 可能導致整合複雜度轉移**
   - 風險：Gateway 和 Claude Code 之間的協議可能變得複雜
   - 緩解：使用標準協議（如 MCP）或簡單的 JSON-RPC

2. **只支援 Telegram 可能限制價值展示**
   - 風險：用戶可能需要 WhatsApp/Discord 支援
   - 緩解：確保 Channel 介面設計良好，未來可快速添加

3. **移除 Memory Search 可能影響使用者體驗**
   - 風險：Claude Code 的內建記憶體可能不如 vector search 精確
   - 緩解：MVP 階段使用 Claude Code 的原生記憶體功能

### 必須保留的複雜度

1. **Security Audit 系統**（~1000 行）：安全是核心需求
2. **Permission System**（~500 行）：DM pairing 和 tool policy 是核心安全機制
3. **Config Schema Validation**（~1000 行）：配置錯誤是最常見的問題來源

### 測試覆蓋率建議

| 模組 | 測試類型 | 覆蓋率目標 |
|------|---------|-----------|
| security/pairing | Unit + Integration | 95%+ |
| security/tool-policy | Unit | 90%+ |
| gateway/routing | Integration | 80%+ |
| channels/telegram | Integration | 70%+ |
| tools/* | Unit | 60%+ |

---

**信心度**: 高

*由認知研究員視角產出*
