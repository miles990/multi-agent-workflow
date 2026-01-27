# 架構分析師 報告

## 核心發現

1. **分層式管道架構（Layered Pipeline Architecture）**：系統採用清晰的三層處理架構 - Dispatch Layer（調度層）、Reply Layer（回覆層）和 Agent Runner（執行層），每層職責明確，透過統一的 `ReplyPayload` 介面串接。

2. **Queue-Based 非同步處理模型**：核心使用 Followup Queue 機制實現訊息的非同步處理，支援多種佇列模式（steer、followup、collect、interrupt、queue），配合 Dispatcher 序列化輸出，確保訊息順序和系統穩定性。

3. **多頻道抽象與跨平台路由**：透過 `OriginatingChannel` + `OriginatingTo` 的抽象設計，實現平台無關的訊息路由，支援跨平台回覆（如 Telegram 訊息透過 Slack session 處理後路由回 Telegram）。

4. **模組化的訊息處理管線**：從 Envelope Formatting → Context Finalization → Directive Resolution → Agent Execution → Block Streaming → Reply Dispatch，每個階段都是可替換的模組，支援高度客製化。

5. **高級串流處理機制**：Block Reply Pipeline 支援即時串流回覆，搭配 Coalescing（合併）、Chunking（分塊）、Human Delay（仿人類延遲）等機制，提供自然流暢的對話體驗。

## 詳細分析

### 1. 系統架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                      INBOUND MESSAGE FLOW                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  DISPATCH LAYER (dispatch.ts / dispatch-from-config.ts)         │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ 1. Context Finalization (inbound-context.ts)          │      │
│  │    - Envelope Formatting (envelope.ts)                │      │
│  │    - Media Understanding Integration                  │      │
│  │    - Deduplication Check (inbound-dedupe.ts)          │      │
│  └───────────────────────────────────────────────────────┘      │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ 2. Reply Dispatcher Creation                          │      │
│  │    - createReplyDispatcher()                          │      │
│  │    - createReplyDispatcherWithTyping()                │      │
│  └───────────────────────────────────────────────────────┘      │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ 3. Dispatch Decision                                  │      │
│  │    - Fast Abort Check (abort.ts)                      │      │
│  │    - Route vs Dispatcher Choice                       │      │
│  │    - Cross-Provider Routing Logic                     │      │
│  └───────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  REPLY LAYER (reply/get-reply.ts)                               │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ 1. Session Initialization (session.ts)                │      │
│  │    - Session Store Loading                            │      │
│  │    - Session Key Resolution                           │      │
│  │    - Reset/New Session Detection                      │      │
│  └───────────────────────────────────────────────────────┘      │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ 2. Directive Resolution (get-reply-directives.ts)     │      │
│  │    - Command Detection (commands-registry.ts)         │      │
│  │    - Model Selection (directive-handling.ts)          │      │
│  │    - Elevated/Verbose/Think Level Resolution          │      │
│  │    - Queue Mode Resolution (queue/settings.ts)        │      │
│  └───────────────────────────────────────────────────────┘      │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ 3. Inline Actions (get-reply-inline-actions.ts)       │      │
│  │    - Status Commands (/status, /model)                │      │
│  │    - Control Commands (/reset, /compact)              │      │
│  │    - Config Commands (/config)                        │      │
│  └───────────────────────────────────────────────────────┘      │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ 4. Prepared Reply (get-reply-run.ts)                  │      │
│  │    - Followup Run Creation                            │      │
│  │    - Queue Key Resolution                             │      │
│  │    - Agent Runner Invocation                          │      │
│  └───────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT RUNNER LAYER (reply/agent-runner.ts)                     │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ 1. Pre-execution Setup                                │      │
│  │    - Typing Controller (typing.ts)                    │      │
│  │    - Memory Flush (agent-runner-memory.ts)            │      │
│  │    - Session Reset Handler                            │      │
│  └───────────────────────────────────────────────────────┘      │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ 2. Agent Execution (agent-runner-execution.ts)        │      │
│  │    - runAgentTurnWithFallback()                       │      │
│  │    - Block Reply Pipeline (block-reply-pipeline.ts)   │      │
│  │    - Tool Result Handling                             │      │
│  │    - Compaction Failure Recovery                      │      │
│  └───────────────────────────────────────────────────────┘      │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ 3. Post-execution Processing                          │      │
│  │    - Payload Building (agent-runner-payloads.ts)      │      │
│  │    - Usage Tracking (session-usage.ts)                │      │
│  │    - Followup Runner (followup-runner.ts)             │      │
│  └───────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  REPLY DISPATCHER (reply/reply-dispatcher.ts)                   │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ Queue Management                                       │      │
│  │  - sendToolResult()  → tool queue                     │      │
│  │  - sendBlockReply()  → block queue (+ human delay)    │      │
│  │  - sendFinalReply()  → final queue                    │      │
│  └───────────────────────────────────────────────────────┘      │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ Delivery Pipeline                                      │      │
│  │  - Normalization (normalize-reply.ts)                 │      │
│  │  - Response Prefix Injection                          │      │
│  │  - Heartbeat Strip                                    │      │
│  │  - Sequential Delivery (sendChain)                    │      │
│  └───────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ROUTING LAYER (reply/route-reply.ts)                           │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ Channel Resolution                                     │      │
│  │  - normalizeChannelId()                               │      │
│  │  - isRoutableChannel()                                │      │
│  └───────────────────────────────────────────────────────┘      │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ Outbound Delivery                                      │      │
│  │  - deliverOutboundPayloads() [lazy import]            │      │
│  │  - Provider-specific adapters                         │      │
│  │  - Session Mirroring                                  │      │
│  └───────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  CHANNEL ADAPTERS (Telegram, Discord, Slack, WhatsApp, ...)     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PARALLEL SUBSYSTEMS                                             │
├─────────────────────────────────────────────────────────────────┤
│  FOLLOWUP QUEUE (queue/enqueue.ts, queue/state.ts)              │
│  - Mode: steer, followup, collect, interrupt, queue             │
│  - Deduplication: message-id, prompt, none                      │
│  - Drop Policy: old, new, summarize                             │
│  - Drain Scheduler (queue/drain.ts)                             │
├─────────────────────────────────────────────────────────────────┤
│  COMMANDS REGISTRY (commands-registry.ts)                        │
│  - Text Alias Mapping                                            │
│  - Native Command Specs                                          │
│  - Skill Command Definitions                                     │
│  - Command Detection & Normalization                             │
└─────────────────────────────────────────────────────────────────┘
```

### 2. 核心組件分析

#### 2.1 Dispatch Layer（調度層）

**檔案位置**：`src/auto-reply/dispatch.ts`, `dispatch-from-config.ts`

**職責**：
- 接收來自各頻道的原始訊息
- 執行前置處理：去重、封裝格式化、媒體理解
- 決定訊息處理策略（Direct Dispatch vs Cross-Provider Routing）
- 管理 Reply Dispatcher 生命週期

**關鍵設計**：
```typescript
// 跨平台路由判斷邏輯（dispatch-from-config.ts:196-198）
const shouldRouteToOriginating =
  isRoutableChannel(originatingChannel) &&
  originatingTo &&
  originatingChannel !== currentSurface;
```

這個設計讓系統能夠：
- 支援多 Agent 共享同一個 session
- 訊息從 Telegram 來，即使透過 Slack session 處理，回覆依然路由回 Telegram
- 避免訊息錯誤發送到錯誤的頻道

**入口函數**：
- `dispatchInboundMessage()`: 基礎調度
- `dispatchInboundMessageWithBufferedDispatcher()`: 帶 Typing 緩衝
- `dispatchInboundMessageWithDispatcher()`: 完整生命週期管理

#### 2.2 Reply Dispatcher（回覆調度器）

**檔案位置**：`src/auto-reply/reply/reply-dispatcher.ts`

**職責**：
- 維護三個優先序列隊列：tool → block → final
- 確保訊息按順序發送（Promise Chain）
- 提供 Idle 檢測機制
- 支援 Human Delay（仿人類打字延遲）

**關鍵機制**：
```typescript
// Sequential Delivery Chain (reply-dispatcher.ts:111-128)
sendChain = sendChain
  .then(async () => {
    if (shouldDelay) {
      const delayMs = getHumanDelay(options.humanDelay);
      if (delayMs > 0) await sleep(delayMs);
    }
    await options.deliver(normalized, { kind });
  })
  .catch((err) => options.onError?.(err, { kind }))
  .finally(() => {
    pending -= 1;
    if (pending === 0) options.onIdle?.();
  });
```

**設計亮點**：
- Promise Chain 保證嚴格的訊息順序（即使是非同步環境）
- `pending` 計數器實現精確的 Idle 檢測
- 在 Block Reply 間注入隨機延遲（800-2500ms），模擬人類打字節奏

#### 2.3 Agent Runner（AI 執行層）

**檔案位置**：`src/auto-reply/reply/agent-runner.ts`

**職責**：
- 管理 AI Agent 的完整執行生命週期
- 處理 Memory Flush（自動壓縮）
- Session Reset 容錯機制
- Block Streaming 管線
- Usage Tracking 與成本計算

**核心流程**：
```typescript
// 簡化版執行流程（agent-runner.ts:301-509）
1. Typing Signal 啟動
2. Memory Flush（如需要）
3. Agent Turn Execution（含 Fallback）
4. Block Reply Pipeline Flush
5. Usage Persistence
6. Payload Building
7. Followup Handling
8. Typing Cleanup
```

**容錯設計**：
- `resetSessionAfterCompactionFailure()`: 壓縮失敗時自動重置 session
- `resetSessionAfterRoleOrderingConflict()`: 角色順序衝突時重啟 session（含清理 transcript）
- Fallback Provider/Model 機制

#### 2.4 Followup Queue（後續任務佇列）

**檔案位置**：`src/auto-reply/reply/queue/`

**職責**：
- 管理非同步的 AI 執行任務
- 支援多種佇列模式（steer、followup、collect、interrupt、queue）
- 去重機制（message-id、prompt）
- 容量限制與 Drop Policy

**佇列模式說明**：

| 模式 | 行為 | 使用場景 |
|------|------|---------|
| `steer` | 立即排隊，不執行當前請求 | Pi Embedded Message 導向 |
| `followup` | 排隊並繼續執行當前請求 | 一般後續任務 |
| `collect` | 僅收集，不自動執行 | 批次處理 |
| `steer-backlog` | 導向 + 積壓處理 | 高負載場景 |
| `interrupt` | 中斷當前任務 | 緊急命令 |
| `queue` | 標準佇列處理 | 預設模式 |

**去重機制**：
```typescript
// queue/enqueue.ts:9-22
function isRunAlreadyQueued(run, items, allowPromptFallback) {
  // 1. 優先使用 messageId 去重
  if (messageId) return items.some(item =>
    item.messageId === messageId && hasSameRouting(item)
  );
  // 2. Fallback 使用 prompt 去重
  if (allowPromptFallback) return items.some(item =>
    item.prompt === run.prompt && hasSameRouting(item)
  );
}
```

#### 2.5 Block Reply Pipeline（串流回覆管線）

**檔案位置**：`src/auto-reply/reply/block-reply-pipeline.ts`

**職責**：
- 接收 AI 模型的串流輸出
- 實現 Coalescing（文字合併）
- 管理 Timeout（15 秒未發送則強制 flush）
- 支援 Audio as Voice Buffer（語音優化）

**Coalescing 策略**：
```typescript
// block-streaming.ts
export type BlockStreamingCoalescing = {
  minChars: number;      // 最小字元數（才發送）
  maxChars: number;      // 最大字元數（強制發送）
  breakPreference: "paragraph" | "newline" | "sentence";
};
```

這個設計確保：
- 串流輸出不會因為太碎片化而導致訊息洪水
- 在自然斷點（段落、句子）分割訊息
- 長訊息不會超過平台限制

#### 2.6 Commands Registry（命令註冊中心）

**檔案位置**：`src/auto-reply/commands-registry.ts`

**職責**：
- 管理所有可用命令（Text Commands + Native Commands + Skill Commands）
- 提供 Text Alias 映射（如 `/s` → `/status`）
- 支援 Fuzzy Matching（模糊匹配）
- Native Command Specs 生成（供平台註冊斜線命令）

**命令類型**：

| 類型 | 範例 | 來源 |
|------|------|------|
| Text Command | `/reset`, `/model opus` | Text Alias |
| Native Command | Telegram Bot Command | Platform Native |
| Skill Command | `/research`, `/plan` | Plugin System |

**Normalization 流程**：
```typescript
// commands-registry.ts:312-350
normalizeCommandBody(raw) {
  1. 移除前導空白
  2. 處理冒號語法 (/model: opus → /model opus)
  3. 移除 Bot Username Mention (/status@mybot → /status)
  4. Text Alias 查找與替換
  5. 參數解析
}
```

### 3. 設計模式識別

#### 3.1 Pipeline Pattern（管道模式）

整個系統是一個多階段的管道：

```
Envelope → Finalize → Directives → Actions → Agent → Payloads → Dispatch → Route → Deliver
```

每個階段都有明確的輸入/輸出介面，可獨立測試和替換。

#### 3.2 Strategy Pattern（策略模式）

**應用場景**：
- Queue Mode 選擇（steer vs followup vs collect...）
- Drop Policy 選擇（old vs new vs summarize）
- Block Streaming Coalescing 策略（paragraph vs newline vs sentence）
- Routing 策略（Direct Dispatcher vs Cross-Provider Route）

#### 3.3 Chain of Responsibility（責任鏈模式）

**Directive Resolution 流程**：
```
Command Detection → Model Selection → Elevated Check → Verbose Check →
Think Level → Queue Mode → Exec Overrides
```

每個 handler 可以決定是否繼續處理或提前返回。

#### 3.4 Observer Pattern（觀察者模式）

**Typing Controller**：
```typescript
// typing.ts
- onReplyStart() → 觸發 typing indicator
- onBlockReply() → 重置 typing timer
- markRunComplete() → 停止 typing
```

**Hook System**：
```typescript
// dispatch-from-config.ts:137-184
hookRunner?.runMessageReceived(...)  // 訊息接收事件
hookRunner?.runMessageSent(...)      // 訊息發送事件
```

#### 3.5 Factory Pattern（工廠模式）

**Dispatcher 工廠**：
```typescript
createReplyDispatcher(options)              // 基礎版
createReplyDispatcherWithTyping(options)    // 帶 Typing
```

**Typing Controller 工廠**：
```typescript
createTypingController(options)
createTypingSignaler({ typing, mode, isHeartbeat })
```

#### 3.6 State Pattern（狀態模式）

**Session State Management**：
```typescript
type SessionEntry = {
  sessionId: string;
  systemSent: boolean;         // 是否已發送 system prompt
  abortedLastRun: boolean;     // 上次執行是否被中止
  groupActivationNeedsSystemIntro: boolean;  // 群組啟動狀態
  compactionCount?: number;    // 壓縮次數
  // ...
}
```

Session 的狀態變化驅動不同的行為（如是否注入 Group Intro）。

#### 3.7 Template Method Pattern（模板方法模式）

**Agent Runner 執行流程**：
```typescript
// agent-runner.ts:47-514
async function runReplyAgent(params) {
  // 1. Setup（可覆寫）
  const typingSignals = createTypingSignaler(...);

  // 2. Pre-execution（可覆寫）
  await runMemoryFlushIfNeeded(...);

  // 3. Execution（核心流程，固定）
  const runOutcome = await runAgentTurnWithFallback(...);

  // 4. Post-execution（可覆寫）
  const payloadArray = buildReplyPayloads(...);

  // 5. Cleanup（固定）
  typing.markRunComplete();
}
```

### 4. 訊息流分析

#### 4.1 標準訊息流（Same-Provider）

```
[Telegram] → Inbound Message
           ↓
     Dispatch Layer
     - Envelope Formatting
     - Dedupe Check
     - Create Dispatcher
           ↓
     Reply Layer
     - Session Init
     - Directives Resolution
     - Inline Actions
           ↓
     Agent Runner
     - Memory Flush
     - Agent Execution
     - Block Streaming
           ↓
     Reply Dispatcher
     - tool queue
     - block queue (streaming)
     - final queue
           ↓
     Deliver (via dispatcher)
           ↓
     [Telegram] ← Outbound Reply
```

#### 4.2 跨平台訊息流（Cross-Provider）

```
[Telegram] → Inbound Message
           ↓
     Dispatch Layer
     - OriginatingChannel = "telegram"
     - OriginatingTo = "chat_123"
     - currentSurface = "slack" (shared session)
     - shouldRouteToOriginating = true
           ↓
     Reply Layer (Slack Session Context)
     - Session Init
     - Agent Execution
           ↓
     Routing Decision
     if (shouldRouteToOriginating) {
       routeReply({
         channel: "telegram",
         to: "chat_123"
       })
     }
           ↓
     [Telegram] ← Outbound Reply (routed back!)
```

**關鍵機制**：
- `OriginatingChannel` 記錄訊息來源
- `OriginatingTo` 記錄目標頻道
- Dispatch Layer 判斷是否需要跨平台路由
- Route Reply 使用 lazy import 動態載入 provider adapter

#### 4.3 Block Streaming 流程

```
Agent Model Output (streaming)
           ↓
     onBlockReply callback
           ↓
     Block Reply Pipeline
     - Accumulate text
     - Check coalescing rules
     - Timeout check (15s)
           ↓
     if (should flush) {
       Dispatcher.sendBlockReply()
             ↓
       Add to block queue
             ↓
       Human Delay (800-2500ms)
             ↓
       Sequential Delivery
     }
           ↓
     Platform Delivery
```

**Coalescing 範例**：
```
Input (streaming):
"Hello" → "Hello world" → "Hello world\nHow" → "Hello world\nHow are" →
"Hello world\nHow are you?"

With minChars=20, breakPreference="newline":
Output:
Block 1: "Hello world" (遇到 \n，超過 minChars)
Block 2: "How are you?" (結束時 flush)
```

#### 4.4 Followup Queue 處理流程

```
Primary Message Processing
           ↓
     Queue Decision
     if (shouldFollowup || mode === "steer") {
       enqueueFollowupRun(queueKey, followupRun, settings)
             ↓
       Queue State
       - Deduplicate (by messageId or prompt)
       - Apply Drop Policy (if cap exceeded)
       - Store in FOLLOWUP_QUEUES Map
             ↓
       Schedule Drain (debounced)
             ↓
       Drain Execution
       - Pop items from queue
       - Invoke Agent Runner for each
       - Route replies back to originating channel
     }
```

**Queue Key 結構**：
```typescript
// 範例：
"telegram:chat_123:agent_main"
"slack:C1234567890:agent_support"
```

這確保不同頻道、不同對話的任務隔離。

### 5. 多頻道支援抽象

#### 5.1 抽象層次

```
┌─────────────────────────────────────────┐
│  CLAWDBOT AUTO-REPLY CORE               │  ← 平台無關
│  - MsgContext (統一訊息格式)             │
│  - ReplyPayload (統一回覆格式)           │
│  - OriginatingChannel (通用路由)         │
└─────────────────────────────────────────┘
                   ↕
┌─────────────────────────────────────────┐
│  CHANNEL ABSTRACTION LAYER              │
│  - normalizeChannelId()                 │
│  - isRoutableChannel()                  │
│  - deliverOutboundPayloads()            │
└─────────────────────────────────────────┘
                   ↕
┌─────────────────────────────────────────┐
│  PROVIDER ADAPTERS                      │  ← 平台特定
│  - Telegram, Discord, Slack, WhatsApp   │
│  - Signal, iMessage, LINE, Matrix       │
└─────────────────────────────────────────┘
```

#### 5.2 統一訊息格式（MsgContext）

**關鍵欄位**：
```typescript
type MsgContext = {
  // 核心內容
  Body?: string;                    // 原始訊息
  BodyForAgent?: string;            // 給 AI 的 prompt
  CommandBody?: string;             // 命令解析用

  // 路由資訊
  From?: string;                    // 發送者 ID
  To?: string;                      // 目標 ID
  SessionKey?: string;              // Session 標識
  Provider?: string;                // 平台名稱
  Surface?: string;                 // 表面名稱（優先於 Provider）

  // 跨平台路由
  OriginatingChannel?: OriginatingChannelType;
  OriginatingTo?: string;

  // 訊息元資料
  MessageSid?: string;              // 訊息 ID
  ReplyToId?: string;               // 回覆目標 ID
  MessageThreadId?: string | number; // Thread ID

  // 多媒體
  MediaPath?: string;
  MediaUrl?: string;
  MediaType?: string;
  MediaPaths?: string[];

  // 群組支援
  ChatType?: string;                // "direct" | "group" | "channel"
  GroupSubject?: string;
  SenderName?: string;
  WasMentioned?: boolean;

  // ...
}
```

**設計亮點**：
- 使用 Optional Fields（`?:`），適應不同平台的資訊提供程度
- 多個 Body 變體（Body, BodyForAgent, CommandBody），支援不同處理階段
- `OriginatingChannel` + `OriginatingTo` 實現跨平台路由
- Thread 支援（Telegram Topics, Matrix Threads, Slack Threads）

#### 5.3 統一回覆格式（ReplyPayload）

```typescript
type ReplyPayload = {
  text?: string;                    // 文字內容
  mediaUrl?: string;                // 單一媒體
  mediaUrls?: string[];             // 多媒體
  replyToId?: string;               // 回覆目標
  audioAsVoice?: boolean;           // 語音訊息標記
  // ...
}
```

**Normalization 過程**：
```typescript
// normalize-reply.ts
normalizeReplyPayload(payload, options) {
  1. 移除 Heartbeat Strip Token
  2. 注入 Response Prefix
  3. 模板變數替換（{{Provider}}, {{Model}}）
  4. 清理空白字元
  5. 驗證必要欄位
}
```

#### 5.4 Channel Adapter Interface

**Delivery 介面**：
```typescript
// 每個 Channel Adapter 需實現
interface ChannelAdapter {
  sendMessage(params: {
    to: string;
    text?: string;
    mediaUrls?: string[];
    replyToId?: string;
    threadId?: string | number;
    // ...
  }): Promise<{ messageId?: string }>;
}
```

**Lazy Loading**：
```typescript
// route-reply.ts:113
const { deliverOutboundPayloads } = await import("../../infra/outbound/deliver.js");
```

這個設計避免在初始化時載入所有 Channel Adapters，減少啟動時間和記憶體佔用。

### 6. 進階機制

#### 6.1 Typing Indicator 管理

```typescript
// typing.ts
class TypingController {
  private interval?: NodeJS.Timer;

  async onReplyStart() {
    // 啟動 typing indicator
    this.interval = setInterval(() => {
      sendTypingIndicator();
    }, typingIntervalSeconds * 1000);
  }

  markRunComplete() {
    // 停止 typing
    if (this.interval) clearInterval(this.interval);
  }

  markDispatchIdle() {
    // Dispatcher 完成後才真正關閉 typing
    this.markRunComplete();
  }
}
```

**整合點**：
- `onReplyStart` → Agent 開始執行時觸發
- `onBlockReply` → 每次 Block 發送後重置 timer
- `markDispatchIdle` → 所有訊息發送完成後關閉

#### 6.2 Session Compaction（自動壓縮）

**觸發條件**：
```typescript
// agent-runner-memory.ts
if (shouldRunMemoryFlush) {
  // 1. Context 快用滿（例如 > 80%）
  // 2. 非 CLI Provider（Claude CLI 有自己的壓縮機制）
  // 3. 非 Heartbeat（避免干擾正常對話）
  // 4. Workspace 非 Read-only
  await runMemoryFlush(...);
}
```

**壓縮流程**：
```
1. 建立壓縮 Prompt（使用專用 Model，如 Haiku）
2. 執行 Memory Flush Turn
3. 更新 Session Metadata（compactionCount++）
4. 如果失敗 → resetSessionAfterCompactionFailure()
```

**容錯設計**：
```typescript
// agent-runner.ts:288-293
const resetSessionAfterCompactionFailure = async (reason: string) => {
  // 1. 建立新的 sessionId
  // 2. 複製 Session Entry（保留設定）
  // 3. 更新 Session Store
  // 4. 記錄錯誤日誌
  // 5. 繼續執行（不中斷使用者對話）
};
```

#### 6.3 Fast Abort 機制

**目的**：快速中止正在執行的 Subagent，避免浪費資源。

**流程**：
```typescript
// abort.ts
async function tryFastAbortFromMessage({ ctx, cfg }) {
  1. 檢查訊息是否包含 Abort Command
  2. 查找正在執行的 Subagents（從 Running Sessions）
  3. 發送 Abort Signal
  4. 等待 Subagents 停止（最多 3 秒）
  5. 返回確認訊息
}
```

**整合點**：
```typescript
// dispatch-from-config.ts:234-267
const fastAbort = await tryFastAbortFromMessage({ ctx, cfg });
if (fastAbort.handled) {
  // 直接返回確認訊息，跳過 Agent 執行
  return {
    text: formatAbortReplyText(fastAbort.stoppedSubagents)
  };
}
```

#### 6.4 Cross-Provider Session Sharing

**問題**：如何讓同一個 AI Session 同時服務多個平台？

**解決方案**：
```typescript
// 1. Session Key 設計（平台無關）
sessionKey = `agent_id:conversation_hash`
// 不包含 platform 資訊

// 2. 訊息路由（dispatch-from-config.ts）
if (originatingChannel !== currentSurface) {
  // 跨平台情況
  await routeReply({
    channel: originatingChannel,  // 路由回原始平台
    to: originatingTo
  });
} else {
  // 同平台情況
  dispatcher.sendFinalReply(payload);
}

// 3. Session Mirroring（route-reply.ts:123-132）
mirror: {
  sessionKey,
  agentId,
  text,      // 記錄回覆內容到 session transcript
  mediaUrls
}
```

**使用場景**：
- 在 Telegram 問問題
- 切換到 Slack 繼續對話
- AI 記得完整對話歷史
- 回覆自動路由回正確的平台

## 建議與洞察

### 1. 架構優勢

✅ **高內聚低耦合**：每個 Layer 職責清晰，介面明確，可獨立測試和替換。

✅ **可擴展性強**：
- 新增平台只需實作 Channel Adapter
- 新增命令只需註冊到 Commands Registry
- 新增佇列模式只需擴展 QueueMode enum

✅ **容錯能力優秀**：
- Session Reset 機制處理各種異常（壓縮失敗、角色順序衝突）
- Fallback Provider/Model 確保服務可用性
- Fast Abort 避免資源浪費

✅ **效能最佳化**：
- Lazy Loading（Channel Adapters）
- Block Streaming（減少 Latency）
- Human Delay（避免訊息洪水）
- Coalescing（減少網路請求）

### 2. 可改進之處

⚠️ **複雜度管理**：
- 超過 100 個檔案在 `auto-reply/` 目錄
- Directives Resolution 流程過長（10+ 步驟）
- 建議：考慮引入 Facade Pattern 簡化外部介面

⚠️ **狀態管理**：
- Session State 散落在多個檔案（session.ts, session-updates.ts, session-usage.ts）
- 建議：集中化 Session State Management（如使用 State Machine）

⚠️ **測試覆蓋**：
- 跨平台路由邏輯依賴 Integration Tests
- 建議：增加 Unit Tests for Route Decision Logic

⚠️ **文件完整性**：
- 缺少整體架構圖（本報告補充）
- 缺少 Sequence Diagram（訊息流程圖）
- 建議：維護 Architecture Decision Records (ADR)

### 3. 設計洞察

💡 **Pipeline + Queue 的完美結合**：
- Pipeline 確保每個訊息的處理流程標準化
- Queue 確保系統在高負載下的穩定性
- 兩者結合實現了"快速回應 + 可靠執行"

💡 **跨平台路由的精妙設計**：
- `OriginatingChannel` 不是在 Delivery 階段才決定，而是在 Dispatch 階段就確定
- 這避免了複雜的 Context 傳遞和狀態管理
- 路由邏輯與業務邏輯完全解耦

💡 **Block Streaming 的使用者體驗優化**：
- Coalescing 避免訊息碎片化
- Human Delay 讓對話感覺更自然
- Timeout 確保不會因為模型卡住而無限等待
- 這些都是深度考慮使用者體驗的設計

💡 **容錯優先的設計哲學**：
- 所有關鍵操作都有 Fallback（Session Reset, Model Fallback）
- 錯誤不會中斷使用者對話（Silent Recovery）
- 這是生產級系統的必備品質

### 4. 技術債務識別

🔴 **High Priority**：
- Dispatch Layer 與 Reply Layer 的界限模糊（部分邏輯重複）
- Session State 更新邏輯散落在多處（容易不一致）

🟡 **Medium Priority**：
- Commands Registry 的 Cache 機制未考慮 Multi-threading（但 Node.js 單執行緒，暫無問題）
- Block Reply Pipeline 的 Timeout 是硬編碼（15 秒）

🟢 **Low Priority**：
- 部分函數超過 500 行（如 `runReplyAgent`），可拆分
- Type Definitions 散落在多個檔案（types.ts, templating.ts, queue/types.ts）

### 5. 擴展建議

🚀 **如需新增平台支援（如 WeChat）**：
1. 實作 Channel Adapter（`src/channels/wechat/`）
2. 註冊到 `normalizeChannelId()`（`src/channels/plugins/index.ts`）
3. 實作 `deliverOutboundPayloads()` for WeChat
4. 新增 E2E Tests

🚀 **如需新增佇列模式（如 `priority`）**：
1. 擴展 `QueueMode` enum（`queue/types.ts`）
2. 實作 Priority Queue 邏輯（`queue/enqueue.ts`）
3. 更新 `resolveQueueSettings()`（`queue/settings.ts`）
4. 新增測試案例

🚀 **如需優化 Block Streaming 效能**：
1. 考慮使用 Incremental Coalescing（動態調整 minChars）
2. 支援 Platform-specific Chunking（Telegram 4096, Discord 2000）
3. 實作 Predictive Flush（基於句子完整性）

## 風險/注意事項

### 1. 技術風險

⚠️ **Queue State 持久化缺失**：
- 目前 `FOLLOWUP_QUEUES` 存在記憶體中（`Map`）
- 服務重啟會遺失所有待處理任務
- **建議**：實作 Queue Persistence（如 SQLite, Redis）

⚠️ **Cross-Provider Routing 的單點故障**：
- 如果 `deliverOutboundPayloads()` 失敗，訊息會遺失
- **建議**：實作 Retry Mechanism + Dead Letter Queue

⚠️ **Session Compaction 的 Race Condition**：
- 多個訊息同時觸發 Compaction 可能導致衝突
- **建議**：實作 Compaction Lock（如使用 Session-level Mutex）

⚠️ **Block Streaming 的記憶體洩漏風險**：
- `accumulatedBlockText` 在長對話中可能無限增長
- **建議**：設定 Max Accumulation Size（如 10KB）

### 2. 擴展風險

⚠️ **Typing Controller 的平台相容性**：
- 不是所有平台都支援 Typing Indicator
- **建議**：在 `createTypingController()` 中檢查平台能力

⚠️ **Human Delay 的文化差異**：
- 不同地區使用者對"自然延遲"的期待不同
- **建議**：支援 Region-specific Delay Config

⚠️ **Commands Registry 的命名衝突**：
- Skill Commands 可能與 Native Commands 重名
- **建議**：實作 Namespace（如 `/skill:research` vs `/research`）

### 3. 維護風險

⚠️ **過度依賴 Session Store**：
- 幾乎所有功能都需要 Session Entry
- Session Store 損壞會導致系統完全不可用
- **建議**：實作 Session Store Backup + Recovery

⚠️ **測試覆蓋不均**：
- E2E Tests 豐富，但 Unit Tests 不足
- Refactoring 風險高
- **建議**：提升 Unit Test Coverage to 80%+

⚠️ **文件與代碼不同步**：
- 架構演進快，但文件更新慢
- **建議**：建立 Architecture Review Process（每季度）

### 4. 效能瓶頸

⚠️ **Sequential Delivery 的延遲累積**：
- Reply Dispatcher 的 Promise Chain 是序列執行
- 大量 Block Replies 會累積延遲
- **建議**：考慮 Parallel Delivery（但需確保順序）

⚠️ **Session Store 的檔案 I/O**：
- 每次 Session Update 都寫檔案
- 高頻對話會產生大量 I/O
- **建議**：實作 Write-back Cache（批次寫入）

⚠️ **Lazy Loading 的首次載入成本**：
- 第一次跨平台路由會觸發 Dynamic Import
- 可能導致 Timeout
- **建議**：實作 Warmup Mechanism（預載常用 Adapters）

---

## 總結

Clawdbot Auto-Reply System 是一個設計精良、工程品質高的多平台 AI Agent 系統。其核心架構採用分層式管道設計，透過 Dispatch Layer、Reply Layer 和 Agent Runner 三層清晰分離關注點。Queue-Based 非同步處理模型配合 Block Streaming 機制，實現了低延遲與高可靠性的完美平衡。

跨平台路由抽象（`OriginatingChannel` + `OriginatingTo`）是整個系統最精妙的設計之一，讓多平台共享 Session 成為可能。Followup Queue 的多模式支援（steer, followup, collect...）展現了對複雜業務場景的深度思考。

建議重點關注：
1. **Queue Persistence**：避免服務重啟導致任務遺失
2. **Session State 集中化**：降低維護複雜度
3. **Test Coverage 提升**：確保 Refactoring 安全

整體而言，這是一個值得學習和參考的企業級 AI Agent 架構。

---

**報告撰寫時間**：2026-01-27
**分析檔案數量**：15+ 核心檔案
**代碼行數估算**：10,000+ LOC（僅 auto-reply 模組）
**架構成熟度評分**：9/10
