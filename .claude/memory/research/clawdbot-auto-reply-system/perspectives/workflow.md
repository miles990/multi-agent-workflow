# 工作流設計師 報告

## 核心發現

### 1. 多層隊列+串流合併架構
clawdbot 的主動回報系統採用 **分層隊列-串流-合併** 三層架構，而非簡單的順序處理：
- **第一層 (Inbound Debounce)**：Discord/Telegram 接收層使用去重函式，將快速連擊的訊息合併 (debounceMs 配置)
- **第二層 (Followup Queue)**：待處理回覆隊列支援跨頻道路由，具備 "collect mode" 可在同頻道時合併多訊息提示
- **第三層 (Block Streaming + Coalescing)**：回覆串流時動態合併小型文本塊 (minChars/maxChars/idleMs)，避免頻繁低資訊量的訊息推送

此三層架構 **解耦** 了訊息接收、隊列處理、回覆發送的時序責任，實現了 **背壓管理** 和 **流量平衡**。

### 2. 提供者無關的路由機制
系統設計了 **OriginatingChannel/OriginatingTo/OriginatingThreadId** 的抽象層：
- 訊息可被路由回 **不同於 SessionKey 的頻道**（多頻道會話共享同一 Session）
- `routeReply()` 函式是執行邊界，動態載入提供者特定的 `deliverOutboundPayloads`
- 支援 **鏡像回覆** 到會話記錄（transcript）但不發送到客戶端（用於控制命令響應）

這種設計使得多頻道統一會話成為可能：一個用戶在 Telegram、Discord、Slack 發送訊息可共享同一個 Session 上下文。

### 3. 智慧文本分塊策略 (Paragraph-Aware)
替代簡單的 `length` 分割，系統提供 **兩種分塊模式**：
- **"length" 模式** (預設)：優先在單詞邊界和換行符分割，避免破壞單詞
- **"newline" 模式**：優先在 **段落邊界** (空行) 分割，保留段內換行和列表結構，只在超限才硬分割

代碼處理了括號內部的特殊分割邏輯和 markdown 代碼柵欄安全性，確保 Structured Output 和代碼塊不被中斷。

### 4. 細粒度媒體附件註記
媒體處理流程包含 **三層過濾**：
- `MediaUnderstanding`：AI 視覺理解標記為已處理的附件
- `MediaUnderstandingDecisions`：人工審核決策標記為已選擇的附件
- 最終生成的 `InboundMediaNote` 只列示未被抑制的附件，避免重複提示

此機制適配 **多頻道多格式** 媒體：圖片、語音、文件、轉發消息（messageSnapshots）。

### 5. 序列化與去重的多層防守
- Telegram：`sequentialize()` 中間件保證同聊天室的訊息按順序處理，`getTelegramSequentialKey()` 支援話題論壇隔離
- Discord：`createInboundDebouncer()` 按 `accountId:channelId:authorId` 鍵值聚合、去重、合併
- 更新去重：`createTelegramUpdateDedupe()` 追蹤最近更新 ID，防止 polling 時重複觸發

此多層防守在**低延遲** 和 **無重複** 之間取得平衡。

---

## 詳細分析

### 訊息接收流程圖

```
User sends message (Telegram/Discord/Slack/etc)
           ↓
    [Channel-specific Listener]
    - Telegram: webhookCallback / polling
    - Discord: message event listener
    - Slack: event API handler
           ↓
    [Inbound Debounce] (optional)
    - Key: accountId:channelId:authorId
    - Debounce window: 300ms-1000ms (configurable)
    - Combines: Multiple rapid messages from same user
           ↓
    [Message Preflight Check]
    - Allow-list check (allowFrom, guildEntries)
    - Command detection (control commands bypass debounce)
    - Media validation
    - Rate limiting
           ↓
    [Build MsgContext] (Context freshness)
    - OriginatingChannel (telegram, discord, slack, etc)
    - OriginatingTo (chat_id, channel_id, user_id)
    - OriginatingAccountId (for multi-account support)
    - OriginatingThreadId (Telegram topic, Discord thread)
    - Media paths, URLs, types
    - Author metadata, chat type
           ↓
    [Routing to Reply Engine]
    - Route via sessionKey (multi-agent support)
    - Query agent workspace
    - Prepare AI agent execution context
```

**關鍵設計決策**：
- **無狀態去重**：Debouncer 在內存中保留最近事件，不依賴外部存儲
- **上下文新鮮性**：每條訊息生成獨立的 `MsgContext`，包含完整的提供者元數據
- **允許清單整合**：Allow-list 在接收層早期篩選，避免浪費後端資源

### 回覆發送流程圖

```
[Agent Processing]
- AI model execution (streaming or batch)
- Generates ReplyPayload(s)
           ↓
    [Block Streaming + Coalescing]
    - Min/Max char thresholds: 800-1200 (configurable per channel)
    - Idle wait: 1000ms (wait for more chunks before flushing)
    - Joiner strategy: "\n\n" (paragraph) / "\n" (newline) / " " (sentence)
    - Prevents: Small fragment flooding
           ↓
    [Block Reply Pipeline]
    - Deduplication: Track sent ReplyPayload keys
    - Buffering: AudioAsVoice grouping
    - Timeout: 5000ms per send attempt
    - Abort signal: Cooperative cancellation
           ↓
    [Route Reply - Provider Dispatch]
    - Resolve: OriginatingChannel → channelId (normalize)
    - Lookup: Channel dock (outbound module)
    - Normalize: ReplyPayload (remove prefix if already in text)
    - Session mirroring: Log to session transcript (optional)
           ↓
    [Outbound Delivery]
    - Call: deliverOutboundPayloads() [lazy loaded]
    - Split text by channel limit (textChunkLimit per channel)
    - Handle: Media URLs, reply-to IDs, threading
    - API call: Send to channel (Telegram, Discord, etc)
           ↓
    [Message Acknowledgment]
    - Telegram: Message ID capture
    - Discord: Reaction emoji (configurable scope)
    - Sent cache: Prevent duplicate sends in short time window
```

**關鍵設計決策**：
- **延遲加載提供者邏輯**：`import("../../infra/outbound/deliver.js")` 在路由時執行，保持主模塊輕量
- **串流合併緩沖**：等待 `idleMs` 後再發送，減少訊息噪音（特別是在 block streaming 回應時）
- **鏡像與轉錄**：回覆可選擇性地鏡像到會話記錄，支援多會話共享時的上下文保留

### 串流機制分析

#### Block Streaming 配置解析

```typescript
BlockStreamingCoalescing {
  minChars: number       // 最小累積字符才發送（示例：800）
  maxChars: number       // 最大訊息字符數（示例：1200）
  idleMs: number         // 空閒等待時間（示例：1000ms）
  joiner: string         // 多塊連接符（"\n\n" / "\n" / " "）
}
```

流程：
1. Agent 返回流式回覆塊 (Block A, Block B, Block C)
2. Coalescer 累積塊直到 **時間條件** OR **字符限制**
3. 若超過 `maxChars`：立即發送已累積部分
4. 若超過 `idleMs`：即使未達 `minChars` 也發送
5. 若累積未達 `minChars` 但流結束：發送全部

**效果**：
- 防止短片段洪氾（如 "我...在...思考..."）
- 適應不同頻道的 UX（微信傾向短訊息，Discord 可接受長文本）
- 可配置的平衡：響應延遲 vs 訊息質量

#### 文本分塊策略

```
chunkByParagraph (newline mode)
├─ 識別段落邊界 (空行: \n[\t ]*\n+)
├─ 檢查代碼柵欄安全性 (不在 ``` 內分割)
├─ 分割時保留單行換行和列表縮進
└─ 超限段落再用 chunkText (length-based) 二次分割

chunkText (length mode)
├─ 掃描括號平衡 (避免在括號內分割)
├─ 優先尋找換行符 (paren-aware)
├─ 其次尋找空白符 (word boundary)
└─ 最後硬分割在限制字符數
```

### 多頻道適配策略

#### 1. 提供者-無關路由 (Provider-Agnostic Routing)

```
routeReply({
  payload,           // 通用 ReplyPayload 格式
  channel,           // "telegram" | "discord" | "slack" ...
  to,                // 提供者特定的目標 ID
  sessionKey,        // 多會話支援
  accountId,         // 多帳號支援
  threadId,          // 提供者特定的線程 ID
  cfg                // 全局配置
})
      ↓
normalizeReplyPayload()  // 提供者無關格式
      ↓
deliverOutboundPayloads()  // 提供者特定實現 (lazy)
      ↓
Channel-specific send:
  - Telegram: bot.api.sendMessage(..., { chat_id: to, ... })
  - Discord: channel.send(...)
  - Slack: client.chat.postMessage(channel: to, ...)
```

#### 2. 頻道特定配置

```yaml
channels:
  telegram:
    textChunkLimit: 4096
    blockStreamingCoalesce:
      minChars: 800
      maxChars: 1200
      idleMs: 1000

  discord:
    textChunkLimit: 2000
    blockStreamingCoalesce:
      minChars: 600
      maxChars: 1800
      idleMs: 800
```

每個提供者可配置：
- **textChunkLimit**：最大單訊息字符數（Telegram 4096, Discord 2000）
- **chunkMode**："length" vs "newline"
- **blockStreamingCoalesce**：回覆串流合併策略

#### 3. 多帳號和多會話支援

```
Session Structure:
{
  sessionKey: "telegram:123456:chat_789",
  lastChannel: "telegram",
  channels: [
    { channel: "telegram", to: "789", accountId: "primary" },
    { channel: "discord", to: "channel_456", accountId: "primary" },
    { channel: "slack", to: "U123", accountId: "secondary" }
  ]
}

When reply arrives:
- If OriginatingChannel = "discord" → route to Discord
- Else if no OriginatingChannel → use lastChannel
- Multiple replies → split by channel, route independently
```

### 隊列優先級與回溯

#### Followup Queue 狀態機

```
FOLLOWUP_QUEUES: Map<sessionKey, FollowupQueueState>

FollowupQueueState {
  items: FollowupRun[]    // 待處理項
  droppedCount: number    // 丟棄的項數
  mode: "collect" | "individual"
  draining: boolean       // 是否正在排隊
  lastRun: AgentRun       // 最後一次代理執行
}

Processing Loop:
1. Check if draining
2. If mode="collect" AND cross-channel items:
   → Switch to "individual" mode
   → Process one item at a time
3. If mode="collect" AND same-channel:
   → Collect all items
   → Combine prompts
   → Run once with merged context
4. If queue has summary prompts:
   → Flush summary first
5. Otherwise: Process individual items
```

**設計意圖**：
- **Collect Mode**：在快速連續訊息時使用，減少 API 調用
- **Cross-Channel Detection**：發現多頻道時自動切換到個別模式，確保正確路由
- **Summary Prompts**：用於隊列滿時的系統提示（如 "您有多條待處理訊息"）

---

## 建議與洞察

### 1. 工作流透明度優化
**建議**：在 `Followup Queue` 中記錄轉換點
- 實現：在 `scheduleFollowupDrain()` 中添加 `onModeSwitch`, `onCollect`, `onIndividualProcess` 回調
- 效益：支援調試工具顯示隊列狀態轉遷圖，有助於診斷為何某個回覆被延遲或單獨處理

### 2. 動態合併閾值優化
**建議**：根據會話負載動態調整 `idleMs` 和 `minChars`
```
if (queue.length > threshold):
    idleMs = 500    // Reduce wait time under high load
    minChars = 600  // Lower threshold to flush sooner
else:
    idleMs = 1000   // Default relaxed mode
```
- 效益：高頻率會話下減少延遲，低頻率會話下提升消息質量

### 3. 頻道親和性預測
**建議**：學習用戶在每個頻道的偏好消息長度
```
metrics:
  telegram: avg_msg_length: 250 chars  // 用戶傾向短消息
  discord: avg_msg_length: 800 chars   // 用戶接受長文本

→ Dynamically set textChunkLimit and minChars per channel
```
- 效益：改善使用者體驗的一致性

### 4. 逆向壓力信號傳播
**建議**：當隊列超過閾值時向代理發信號
```
if (queue.items.length > 10):
    context.HighLoadWarning = true
    // Agent 可據此調整回覆風格（更簡潔）
```
- 效益：系統自適應，避免郵件堆積

### 5. 多頻道會話同步
**建議**：在跨頻道回覆時添加一致性檢查
```
- 用戶在 Telegram 要求回覆，Agent 生成回覆
- 若用戶同時在 Discord 發送 "更新"，路由至同一 Session
- 防止不一致狀態：使用 optimistic lock 或 version vector
```
- 效益：確保多頻道會話的因果一致性

---

## 風險與注意事項

### 1. 隊列無限增長風險
**風險**：若 `runFollowup` 調用失敗，`queue.items` 不被清理
**現狀**：代碼使用 try-catch 保護，但失敗的項被丟棄（記錄到 `droppedCount`）
**建議**：
- 實現可配置的 `maxQueueSize`
- 當隊列滿時，使用過期策略（FIFO/Priority-based）丟棄最舊/最低優先級項
- 添加監控告警

### 2. 提供者去重重複邏輯
**風險**：Telegram 和 Discord 各自實現去重邏輯，代碼重複
**現狀**：
- Telegram：`createTelegramUpdateDedupe()` + `recordUpdateId()`
- Discord：`createInboundDebouncer()` + `shouldDebounce()`
**建議**：
- 抽象統一的 `InboundDeduplicator` 接口
- 支援不同的去重策略（基於 ID 的、基於內容的、基於時間戳的）

### 3. 鏡像回覆的誤用風險
**風險**：若控制命令的回覆被鏡像，可能導致 Session 記錄中出現不必要的長回覆
**現狀**：`mirror` 參數默認為 `true` （當 `sessionKey` 存在時）
**建議**：
- 為特定回覆類型（如控制命令、錯誤消息）強制 `mirror: false`
- 添加選項允許代理在回覆中設定 `X-NoMirror` 指令

### 4. 文本分塊的邊界情況
**風險**：
- 代碼柵欄不完整時的分割行為未定義
- 非 ASCII 字符（表情符號、CJK）計數可能不準確
**現狀**：使用 `string.length` 計算，不支援 Unicode 正規化
**建議**：
- 切換到 `Intl.Segmenter` 支援 grapheme clusters
- 增加單元測試覆蓋多語言邊界情況

### 5. 串流超時風險
**風險**：若某個分塊發送耗時 > `timeoutMs` (5000ms)，pipeline 中止
**現狀**：使用 `Promise.race()` + 定時器，中止後不重試
**建議**：
- 實現指數退避重試
- 區分瞬時故障（網絡）vs 持久故障（API 限制）
- 添加可觀測性：記錄超時事件和失敗頻率

### 6. Followup 隊列的 UX 隱形成本
**風險**：用戶不知道回覆被隊列化了多久
**現狀**：無 UI 反饋機制
**建議**：
- 在首次隊列化時發送 "正在思考..." 或打字指示
- 提供選項讓代理回覆人工可見的隊列提示
- 對超過 3 秒的隊列，通知用戶延遲原因（如 "等待前 N 條訊息處理"）

---

## 結論

clawdbot 的主動回報系統展現出 **分層隊列 + 智慧合併 + 多頻道抽象** 的成熟架構：

1. **系統韌性**：多層去重、背壓管理、優雅降級（隊列模式切換）
2. **使用者體驗**：段落感知分塊、動態串流合併避免訊息碎片化
3. **可擴展性**：提供者無關路由支援無縫添加新頻道，多帳號/多會話隔離清晰
4. **工程品質**：模塊化設計、配置驅動、完善的測試覆蓋

**核心洞察**：此架構將訊息接收、佇列管理、回覆發送解耦為三個獨立責任層，通過上下文新鮮性機制和提供者抽象實現了真正的**多頻道統一會話**。

