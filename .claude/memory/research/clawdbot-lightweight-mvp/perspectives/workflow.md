# 工作流設計師報告

**研究主題**: Clawdbot 輕量 MVP 工作流與執行流程分析
**視角 ID**: workflow
**執行時間**: 2026-01-27
**專案**: /Users/user/Workspace/clawdbot

## 核心發現

1. **消息處理流程有 6 層權限檢查** - 從 Telegram 收到消息到回覆，經過身份驗證、DM/群組策略、allowlist 檢查、命令解析、工具權限、回覆策略等多層檢查。MVP 可以通過快速失敗機制優化，但核心檢查不能移除。

2. **Claude Code 整合涉及 5 個層級** - 消息解析 → 權限檢查 → Session 路由 → Agent 執行 → 回覆傳遞。整合時需要在「Agent 執行」這一層切入，替換 Pi Agent 為 Claude Code Task API。

3. **5 個不可移除的核心步驟** - Token 驗證、發送者身份檢查、上下文構建、路由決策、回覆傳遞。這些步驟是任何 Telegram Bot 都需要的基礎設施。

4. **4 個主要簡化機會** - 移除多頻道支援、簡化配置系統、簡化會話管理（記憶體取代 SQLite）、移除高級流式傳輸。

5. **分層權限檢查架構值得保留** - 快速失敗層（Token、基礎配置）→ 緩存層（allowlist lookup）→ 複雜檢查層（動態策略），這種分層設計可以顯著提高效能。

## 詳細分析

### 1. 完整消息處理流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    Telegram 消息進入                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: Grammy Bot 初始化                                      │
│ - bot.ts: 驗證 botToken                                         │
│ - 建立長輪詢連線                                                 │
│ - 解析 Update 結構                                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2: 消息分類與分發                                          │
│ - bot-handlers.ts: 區分 DM/群組/頻道                             │
│ - 處理 /start, /help 等原生命令                                  │
│ - 檢測 @mention 和 reply-to-bot                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3: 權限檢查                                               │
│ - command-auth.ts: resolveCommandAuthorization()               │
│   ├─ 檢查 senderId 是否在 allowFrom                             │
│   ├─ 檢查 DM Policy (pairing/allowlist/open)                   │
│   └─ 檢查 Group Policy (allowlist/disabled)                    │
│ - mention-gating.ts: 群組必須 @bot 才回應                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 4: Session 路由                                           │
│ - session-key.ts: 生成 session key                              │
│   格式: agent:{agentId}:telegram:{dm|group}:{chatId}           │
│ - resolve-route.ts: 決定使用哪個 Agent                          │
│ - agent-scope.ts: 載入 Agent 配置                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 5: Agent 執行 (MVP 切入點)                                │
│ 原有: pi-embedded-runner.ts                                     │
│   ├─ 載入 Pi Agent                                              │
│   ├─ 執行工具調用                                                │
│   └─ 生成回覆                                                   │
│ MVP: claude-code-adapter.ts                                     │
│   ├─ 轉發消息到 Claude Code                                     │
│   ├─ 映射工具調用                                                │
│   └─ 收集回覆                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 6: 回覆傳遞                                               │
│ - reply.ts: 格式化回覆                                          │
│ - chunk.ts: 長文本分塊 (預設 4000 字元)                          │
│ - send.ts: 發送到 Telegram                                      │
│   ├─ Markdown → Telegram HTML 轉換                              │
│   ├─ 媒體附件處理                                                │
│   └─ 錯誤重試機制                                                │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Claude Code 整合流程

#### 整合架構

```
┌─────────────────────────┐
│   Telegram User         │
│   發送消息               │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│   Grammy Bot (Gateway)  │
│   - 接收 Update         │
│   - 權限檢查            │
│   - Session 路由        │
└───────────┬─────────────┘
            ↓
┌─────────────────────────────────────────┐
│   Claude Code Adapter                    │
│   ┌─────────────────────────────────┐   │
│   │ 1. 建立 Task (TaskCreate)       │   │
│   │ 2. 等待執行完成                  │   │
│   │ 3. 處理工具調用請求              │   │
│   │ 4. 收集最終回覆                  │   │
│   └─────────────────────────────────┘   │
└───────────┬─────────────────────────────┘
            ↓
┌─────────────────────────┐
│   Claude Code Runtime   │
│   - Agent 推理          │
│   - 工具執行            │
│   - 回覆生成            │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│   回覆傳遞              │
│   - 格式化              │
│   - 分塊                │
│   - 發送                │
└─────────────────────────┘
```

#### 工具調用映射

```typescript
// Gateway 提供的工具 API
interface GatewayToolAPI {
  // 檔案系統工具
  'fs.read': (path: string) => Promise<string>;
  'fs.write': (path: string, content: string) => Promise<void>;
  'fs.list': (path: string) => Promise<string[]>;

  // 執行工具
  'exec.bash': (command: string) => Promise<{ stdout: string; stderr: string; }>;

  // Session 工具
  'session.history': () => Promise<Message[]>;
  'session.clear': () => Promise<void>;

  // Telegram 工具
  'telegram.send': (chatId: string, text: string) => Promise<void>;
  'telegram.sendMedia': (chatId: string, media: Media) => Promise<void>;
}
```

### 3. 權限檢查流程優化

#### 現有流程（6 步）

```
1. Token 驗證 (bot.ts)
2. 消息類型檢查 (bot-handlers.ts)
3. DM/Group Policy 檢查 (command-auth.ts)
4. Allowlist 檢查 (command-auth.ts)
5. Mention Gating (mention-gating.ts)
6. Tool Policy 檢查 (tool-policy.ts)
```

#### 優化後流程（3 步 + 2 可選）

```
必要步驟:
1. Token + 基礎配置驗證 (快速失敗)
2. Allowlist 檢查 (緩存查找)
3. Policy 檢查 (DM/Group/Tool)

可選步驟:
4. Mention Gating (群組專用)
5. 動態權限檢查 (進階場景)
```

#### 實作建議

```typescript
// src/security/permission-check.ts

export async function checkPermission(ctx: MessageContext): Promise<PermissionResult> {
  // 快速失敗層
  if (!ctx.botToken) return { allowed: false, reason: 'NO_TOKEN' };
  if (!ctx.senderId) return { allowed: false, reason: 'NO_SENDER' };

  // 緩存查找層
  const allowlist = await getAllowlist(ctx.channel);
  if (!allowlist.includes(ctx.senderId)) {
    return { allowed: false, reason: 'NOT_IN_ALLOWLIST' };
  }

  // Policy 檢查層
  const policy = await getPolicy(ctx.channel, ctx.chatType);
  if (!policy.evaluate(ctx)) {
    return { allowed: false, reason: 'POLICY_DENIED' };
  }

  return { allowed: true };
}
```

### 4. 部署和運維流程

#### 啟動流程

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 配置載入                                                     │
│    - 讀取 config.json5                                          │
│    - 環境變數覆蓋                                                │
│    - 配置驗證 (Zod schema)                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. 插件註冊                                                     │
│    - 註冊 Telegram Channel                                      │
│    - 註冊工具 (Bash, Read, Write)                               │
│    - 註冊 Hooks (Audit Logger)                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. Gateway 啟動                                                 │
│    - WebSocket Server 初始化                                    │
│    - Session Store 初始化                                       │
│    - 健康檢查端點啟動                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. Channel 啟動                                                 │
│    - Telegram Bot 連線                                          │
│    - 長輪詢開始                                                  │
│    - 心跳檢測啟動                                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. 就緒                                                         │
│    - 記錄啟動日誌                                                │
│    - 發送健康狀態                                                │
└─────────────────────────────────────────────────────────────────┘
```

#### 配置熱重載

```typescript
// 監聽配置變更
fs.watch('config.json5', async () => {
  const newConfig = await loadConfig();
  const validation = validateConfig(newConfig);

  if (validation.success) {
    // 熱重載安全的配置項
    updateAllowlist(newConfig.channels.telegram.allowFrom);
    updatePolicies(newConfig.channels.telegram.policies);

    // 需要重啟的配置項
    if (newConfig.channels.telegram.botToken !== currentConfig.botToken) {
      logger.warn('Bot token changed, restart required');
    }
  } else {
    logger.error('Config validation failed', validation.errors);
  }
});
```

### 5. 開發工作流

#### 本地開發環境

```bash
# 1. 安裝依賴
pnpm install

# 2. 配置環境變數
cp .env.example .env
# 編輯 .env 設定 TELEGRAM_BOT_TOKEN

# 3. 啟動開發模式
pnpm dev

# 4. 運行測試
pnpm test                    # 單元測試
pnpm test:e2e                # 端對端測試
CLAWDBOT_LIVE_TEST=1 pnpm test  # 真實 API 測試
```

#### 測試流程

```
┌─────────────────────────────────────────────────────────────────┐
│ 單元測試 (Vitest)                                               │
│ - 每個模組獨立測試                                               │
│ - Mock 外部依賴                                                 │
│ - 覆蓋率目標: 70%                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 整合測試                                                        │
│ - Gateway + Channel 組合                                        │
│ - 使用測試 Bot Token                                            │
│ - 驗證消息流程                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 端對端測試                                                       │
│ - 真實 Telegram API                                             │
│ - 完整消息收發                                                   │
│ - 權限檢查驗證                                                   │
└─────────────────────────────────────────────────────────────────┘
```

#### 部署流程

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 構建                                                         │
│    pnpm build                                                   │
│    - TypeScript 編譯                                            │
│    - 類型檢查                                                    │
│    - 產出 dist/                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. Docker 打包                                                  │
│    docker build -t clawdbot-mvp .                               │
│    - 多階段構建                                                  │
│    - 只包含運行時依賴                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. 部署                                                         │
│    docker run -d --env-file .env clawdbot-mvp                   │
│    - 環境變數注入                                                │
│    - 健康檢查配置                                                │
│    - 日誌輸出配置                                                │
└─────────────────────────────────────────────────────────────────┘
```

## 建議與洞察

### 1. MVP 消息流程簡化

```
簡化前: 6 層 × 多個子步驟 = ~15 個處理點
簡化後: 4 層 × 精簡子步驟 = ~8 個處理點

保留:
├── 消息接收 (Grammy Bot)
├── 權限檢查 (合併為單一函數)
├── Agent 執行 (Claude Code Adapter)
└── 回覆傳遞 (直接發送)

移除/合併:
├── 多 Channel 路由 (只有 Telegram)
├── 複雜 Session Scope (只用 main)
├── 高級流式傳輸 (簡單 chunking)
└── 動態插件加載 (靜態註冊)
```

### 2. 可靠性設計

```typescript
// 錯誤處理策略
interface ErrorHandlingStrategy {
  // 重試配置
  retry: {
    maxAttempts: 3,
    backoff: 'exponential',
    initialDelay: 1000,
  };

  // 降級策略
  fallback: {
    onAgentFailure: 'return_error_message',
    onNetworkFailure: 'queue_for_retry',
    onRateLimitFailure: 'delay_and_retry',
  };

  // 監控
  monitoring: {
    logLevel: 'info',
    alertThreshold: {
      errorRate: 0.05,  // 5% 錯誤率告警
      latency: 5000,    // 5 秒延遲告警
    },
  };
}
```

### 3. 會話管理選擇

| 方案 | 優點 | 缺點 | 適用場景 |
|------|------|------|---------|
| 記憶體 Map | 快速、簡單 | 重啟丟失 | MVP 原型 |
| JSON 檔案 | 持久化、易除錯 | I/O 開銷 | 開發環境 |
| SQLite | 查詢能力、原子性 | 複雜度增加 | 生產環境 |
| Redis | 高性能、分散式 | 基礎設施成本 | 大規模部署 |

**MVP 建議**: 使用記憶體 Map + JSON 持久化（shutdown 時寫入）

### 4. 日誌和監控

```typescript
// 結構化日誌格式
interface LogEntry {
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  component: 'gateway' | 'telegram' | 'agent' | 'tools';
  event: string;
  context: {
    sessionId?: string;
    userId?: string;
    chatId?: string;
    messageId?: string;
  };
  metadata?: Record<string, unknown>;
}

// 關鍵指標
interface Metrics {
  messagesReceived: Counter;
  messagesProcessed: Counter;
  messageLatency: Histogram;
  agentExecutionTime: Histogram;
  toolInvocations: Counter;
  errors: Counter;
}
```

### 5. 可擴充性設計

```typescript
// Channel 抽象介面
interface Channel {
  id: string;
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  onMessage(handler: MessageHandler): void;
  send(chatId: string, message: OutboundMessage): Promise<void>;
}

// Agent 抽象介面
interface Agent {
  id: string;
  execute(input: AgentInput): Promise<AgentOutput>;
  getTools(): Tool[];
}

// 中間件鏈
type Middleware = (ctx: Context, next: () => Promise<void>) => Promise<void>;

interface MiddlewareChain {
  use(middleware: Middleware): void;
  execute(ctx: Context): Promise<void>;
}
```

## 風險與注意事項

### 1. 消息丟失風險

**風險**: 長輪詢斷線時可能丟失消息
**緩解**:
- 使用 Telegram 的 `offset` 機制確認已處理消息
- 實作本地消息佇列作為緩衝
- 定期心跳檢測連線狀態

### 2. Claude Code 延遲風險

**風險**: Agent 執行時間過長導致用戶體驗下降
**緩解**:
- 設定執行超時（建議 60 秒）
- 實作「思考中...」狀態指示
- 長任務異步處理，完成後主動通知

### 3. 權限繞過風險

**風險**: 權限檢查邏輯分散可能導致繞過
**緩解**:
- 集中化權限檢查為單一函數
- 所有路徑都必須經過權限檢查
- 添加審計日誌記錄所有決策

### 4. 配置錯誤風險

**風險**: 配置錯誤可能導致安全問題
**緩解**:
- 啟動時嚴格驗證配置
- 預設安全配置（deny by default）
- 敏感配置項加密存儲

### 5. 資源耗盡風險

**風險**: 大量消息湧入可能耗盡資源
**緩解**:
- 實作請求限流（rate limiting）
- 消息佇列限制最大長度
- 監控記憶體和 CPU 使用率

### 6. 開發建議

**MVP 路線圖**:
```
Week 1: 最小 Telegram → Claude Code 流程
Week 2: 添加授權和會話支持
Week 3: 運維和可靠性（日誌、監控）
Week 4: 優化和可擴充性準備
```

---

**信心度**: 高

*由工作流設計師視角產出*
