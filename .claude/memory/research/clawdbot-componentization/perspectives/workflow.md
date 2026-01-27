# 工作流設計師 報告

**視角 ID**: workflow
**執行時間**: 2026-01-27
**主題**: Clawdbot 訊息流程與組件化整合策略

## 核心發現

### 1. 訊息處理三層架構

Clawdbot 採用明確的分層訊息流程：
- **入站層（Inbound）**：通過 `auto-reply/dispatch.ts` 和 `inbound-debounce.ts` 管理訊息接收、去重、範本化
- **處理層（Processing）**：`auto-reply/reply.ts` 和 `agent-runner-*.ts` 系列處理命令檢測、AI 代理執行、模型選擇
- **出站層（Outbound）**：通過 `gateway/server-channels.ts` 和 `infra/outbound/channel-adapters.ts` 支援多通道適配

### 2. 多通道整合設計

系統支援 WhatsApp、Signal、Discord、Slack、iMessage、LINE 等 6+ 通道：
- 通道管理通過 `ChannelManager` 實現統一的生命週期管理
- 每個通道有獨立的 `ChannelAccountSnapshot` 狀態追蹤
- 通道適配器（`ChannelMessageAdapter`）處理格式差異

### 3. 會話與狀態管理

- 通過 `session-utils.ts` 實現會話持久化與版本管理
- `ChatRunRegistry` 和 `ChatRunState` 管理進行中的 AI 運行
- 支援會話壓縮、記憶體管理、上下文追蹤

## 詳細分析

### 訊息流程追蹤

```
入站訊息 → dispatchInboundMessage()
    ↓
finalizeInboundContext() [正規化文本、設置 Body/RawBody]
    ↓
dispatchReplyFromConfig() [配置檢查、命令偵測]
    ↓
buildMentionRegexes() / resolveGroupRequireMention() [群組規則檢查]
    ↓
runReplyAgent() [AI 代理執行]
    ├─ runAgentTurnWithFallback() [帶模型回退的代理運行]
    ├─ runEmbeddedPiAgent() / runCliAgent() [LLM 執行]
    ├─ runMemoryFlushIfNeeded() [會話記憶壓縮]
    └─ buildReplyPayloads() [回覆負載構建]
    ↓
createBlockReplyPipeline() [流式回覆管理]
    ↓
通道適配器 → 多通道發送
```

### 模組互動分析

**核心模組依賴圖：**

1. **auto-reply/** (訊息派發與回覆邏輯)
   - `dispatch.ts` → 主入口，協調上下文、配置、派發器
   - `reply.ts` → 導出高級 API（指令提取、回覆取得）
   - `commands-registry.ts` → 命令註冊與偵測（80+ 內置命令）
   - `templating.ts` → 訊息上下文範本化
   - `reply/agent-runner.ts` → AI 代理執行主邏輯
   - `reply/block-reply-pipeline.ts` → 流式回覆管理

2. **gateway/** (伺服器與會話管理)
   - `server.impl.ts` → 啟動點，初始化所有子系統
   - `server-chat.ts` → WebChat 廣播與聊天事件
   - `server-channels.ts` → 通道生命週期管理
   - `session-utils.ts` → 會話 CRUD 操作
   - `hooks-mapping.ts` → 外部 Hook 整合

3. **agents/** (AI 模型與執行)
   - `model-selection.js` → 模型路由（OpenAI/Anthropic/Gemini）
   - `model-auth.js` → 認證配置解析
   - `cli-runner.js` / `pi-embedded.js` → LLM 執行適配器
   - `auth-profiles/` → 多個認證檔案管理

4. **channels/** (通道插件系統)
   - `plugins/index.ts` → 通道發現與註冊
   - 每個通道有 `status.ts`、`config.ts`、`gateway.ts`
   - `gateway.startAccount()` → 通道特定的啟動邏輯

### 關鍵整合點

| 整合點 | 實現 | 責任 |
|------|------|------|
| 訊息入站 | `dispatchInboundMessage()` | 正規化、去重、上下文準備 |
| 命令偵測 | `detectCommand()` / `parseCommandArgs()` | 文本解析、授權檢查 |
| AI 執行 | `runAgentTurnWithFallback()` | 模型選擇、錯誤恢復、流式回覆 |
| 會話管理 | `loadSessionEntry()` / `updateSessionStore()` | 狀態持久化、版本控制 |
| 通道發送 | `ChannelManager.startChannel()` + 適配器 | 多通道適配與發送 |
| Hook 整合 | `resolveHookMappings()` / `dispatchHookAction()` | 外部事件觸發 |
| 流式回覆 | `BlockReplyPipeline` + `onBlockReply()` | 增量訊息推送 |

## 整合策略建議

### 1. 組件邊界劃分（6 個核心組件）

```
┌─────────────────────────────────────────────────────────┐
│                     CLI / Gateway Layer                   │
│  (entry.ts → server.impl.ts → server-chat.ts)           │
└─────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
    ┌─────────────────┬──────────────────┬──────────────────┐
    │  1. Message     │  2. Command      │  3. Agent        │
    │  Router         │  Registry        │  Executor        │
    └─────────────────┴──────────────────┴──────────────────┘
         ↓                    ↓                    ↓
    ┌─────────────────┬──────────────────┬──────────────────┐
    │  4. Session     │  5. Channel      │  6. Hook         │
    │  Manager        │  Adapters        │  Dispatcher      │
    └─────────────────┴──────────────────┴──────────────────┘
```

### 2. 通道間通信協議

**消息格式標準化：**
```typescript
interface UnifiedMessage {
  id: string;
  from: string;
  to: string;
  body: string;
  mediaUrls?: string[];
  chatType: 'direct' | 'group' | 'channel';
  timestamp: number;
  channel: ChannelId;
  accountId: string;
  metadata?: Record<string, unknown>;
}

interface UnifiedReply {
  text: string;
  embeds?: unknown[]; // 通道特定格式
  reaction?: string;
  thread?: string;
  channel: ChannelId;
  accountId: string;
}
```

### 3. 依賴反轉模式

為了解耦組件，建議：
- **消息總線模式**：通過事件發射器替代直接函數調用
  ```typescript
  eventBus.emit('inbound-message', unifiedMessage);
  eventBus.on('agent-reply', (reply) => dispatchToChannels(reply));
  ```
- **適配器工廠**：動態創建通道適配器
  ```typescript
  const adapter = channelAdapterFactory.create(channelId);
  await adapter.send(reply);
  ```
- **配置注入**：通過 DI 容器管理依賴

### 4. 會話狀態同步機制

建議實現：
- **樂觀鎖**：並發執行時的會話版本檢查
- **事件溯源**：記錄所有會話變更，支援重現
- **分佈式鎖**：多實例部署時的會話互斥

### 5. 可觀測性與監控

集成點需要：
- **結構化日誌**：每個組件邊界記錄入出消息
- **追蹤上下文**：使用 `runId` 穿越全流程
- **度量指標**：訊息延遲、命令執行時間、模型調用成本

## 風險與注意事項

### 高風險項

1. **會話狀態一致性**（中-高風險）
   - 當前設計依賴文件系統，高並發下可能出現競態
   - **建議**：遷移至關鍵路徑的數據庫或 Redis
   - **影響**：多並發訊息時可能丟失會話更新

2. **通道適配器的格式不匹配**（中風險）
   - Discord 支援嵌入，但其他通道不支持
   - **建議**：定義通道能力矩陣，回覆時主動降級
   - **影響**：跨通道轉發時可能丟失格式信息

3. **命令權限檢查分散**（低-中風險）
   - 授權邏輯分散在多個文件
   - **建議**：集中權限管理層（RBAC 或屬性策略）
   - **影響**：難以審計、容易出現授權繞過

### 中等風險項

4. **Agent 回退機制的複雜性**（中風險）
   - `runAgentTurnWithFallback()` 實現了複雜的回退邏輯
   - **建議**：提取為專用組件，增加可測試性

5. **Hook 系統的同步/非同步模糊**（低-中風險）
   - Hook 映射支持異步變換但沒有超時控制
   - **建議**：所有外部調用加超時與重試

### 低風險項

6. **記憶體管理與 cleanup**（低風險）
   - `ChatRunState` 中的緩衝區可能無限增長
   - **建議**：實現 LRU 淘汰或基於時間的 cleanup

## 實作路線圖（分階段拆分）

**第 1 階段**（基礎層 - 2 周）
- 提取統一消息格式 → `message-types.ts`
- 建立消息總線 → `event-bus.ts`
- 實現通道能力檢查 → `channel-capabilities.ts`

**第 2 階段**（適配器層 - 3 周）
- 為每個通道創建適配器類
- 統一錯誤處理 → `channel-error-handler.ts`
- 實現重試與熔斷 → `channel-resilience.ts`

**第 3 階段**（編排層 - 2 周）
- 重構訊息派發為管道模式
- 實現權限檢查中間件
- 添加可觀測性

**第 4 階段**（測試與優化 - 3 周）
- 集成測試各組件邊界
- 性能基準測試
- 文檔化 APIs 與契約

## 信心度

中 - 基於訊息流程追蹤和模組互動分析

---
*由工作流設計師視角產出*
