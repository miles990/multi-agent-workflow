# 架構分析師報告

**研究主題**: Clawdbot 輕量 MVP 架構分析
**視角 ID**: architecture
**執行時間**: 2026-01-27
**專案**: /Users/user/Workspace/clawdbot

## 核心發現

1. **插件化架構是核心基礎設施** - Clawdbot 使用完整的插件註冊系統，所有 Channel 通過 `PluginRegistry` 註冊，支援動態加載和卸載。Channel、Provider、Tool、Hook 都是插件形式存在。移除其他 channel 時不會破壞架構，但需要保留插件系統本身。

2. **Telegram 通道依賴鏈清晰且獨立** - 核心檔案 `src/telegram/bot.ts`, `bot-handlers.ts` 依賴模組包括 `channels/registry.ts`、`auto-reply/`、`routing/`、`agents/agent-scope.ts`、`config/`。Telegram 實作與其他 channel 高度解耦，可以獨立運行。

3. **Agent 系統與 Claude Code Tasks 整合路徑明確** - 現有 Agent 系統使用 Pi Agent，可透過 Claude Code Task API 完全替代。保留 Session 管理層（routing, session-key, agent-scope），移除 pi-embedded-* 系列檔案。

4. **權限系統分散但可整合** - 現有檢查點包括 `command-auth.ts`（命令授權）、`bot.ts`（Telegram 特定權限）、`types.telegram.ts`（allowFrom/groupAllowFrom 配置）。可以集中化為統一的權限策略引擎。

5. **可擴充性已經內建** - 插件擴展點完善，未來添加新 Channel 只需實作 `ChannelPlugin` 介面、註冊到 PluginRegistry、配置 routing 和 allowFrom 規則，零核心代碼修改。

## 詳細分析

### 1. 核心架構層次

```
┌─────────────────────────────────────────────┐
│          CLI Interface (src/cli/)          │
├─────────────────────────────────────────────┤
│      Gateway (src/gateway/)                │
│  - WebSocket 控制平面                        │
│  - Session 管理                             │
│  - Event 分發                               │
├─────────────────────────────────────────────┤
│    Plugin System (src/plugins/)            │
│  - PluginRegistry (runtime.ts)             │
│  - Channel/Tool/Hook 註冊                   │
├─────────────────────────────────────────────┤
│  Channel Layer (src/channels/)             │
│  ├─ Telegram (src/telegram/)  ✓ 保留        │
│  ├─ WhatsApp (可移除)                       │
│  ├─ Discord (可移除)                        │
│  └─ ... (其他 7 個可移除)                    │
├─────────────────────────────────────────────┤
│  Routing Layer (src/routing/)              │
│  - resolve-route.ts (Agent 路由)           │
│  - session-key.ts (Session 識別)           │
├─────────────────────────────────────────────┤
│  Auto-Reply Engine (src/auto-reply/)       │
│  - command-auth.ts (權限檢查)               │
│  - reply.ts (回覆生成)                      │
│  - dispatch.ts (消息分發)                   │
├─────────────────────────────────────────────┤
│  Agent System (src/agents/)                │
│  - agent-scope.ts (Agent 配置) ✓ 保留       │
│  - pi-embedded-runner.ts ⚠️ 替換為 Claude   │
│  - clawdbot-tools.ts ⚠️ 映射到 Claude 工具   │
├─────────────────────────────────────────────┤
│  Config System (src/config/)               │
│  - config.ts (配置加載)                     │
│  - types.*.ts (類型定義)                    │
└─────────────────────────────────────────────┘
```

### 2. Telegram 通道隔離分析

**必須保留**：
- `src/telegram/bot.ts` - Telegram Bot 主邏輯
- `src/telegram/bot-handlers.ts` - 消息處理器
- `src/telegram/bot-message.ts` - 消息處理流程
- `src/telegram/accounts.ts` - 帳號管理
- `src/telegram/pairing-store.ts` - DM 配對存儲
- `src/channels/registry.ts` - Channel 註冊（只註冊 Telegram）
- `src/channels/dock.ts` - Channel Dock 系統

**可完全移除**：
- `src/whatsapp/`, `src/discord/`, `src/slack/`, `src/signal/`, `src/imessage/`, `src/googlechat/`, `src/line/`
- `src/channels/plugins/` 中其他 channel 的實作

**依賴基礎設施（必須保留）**：
- `src/auto-reply/` - 自動回覆引擎（所有 channel 共用）
- `src/routing/` - 路由系統（session 管理核心）
- `src/config/` - 配置系統（全局配置加載）
- `src/plugins/` - 插件系統（channel 註冊基礎）
- `src/infra/` - 基礎設施（events, logging, storage）

### 3. Claude Code 整合設計

#### 架構映射

```
現有 Clawdbot Agent          →  Claude Code MVP
─────────────────────────────────────────────────
pi-embedded-runner.ts        →  Claude Code Task API
  ├─ runEmbeddedPiAgent()    →  TaskCreate()
  ├─ session 管理             →  CLAUDE_CODE_TASK_LIST_ID
  └─ tool execution          →  原生 Bash/Read/Write 工具

clawdbot-tools.ts            →  映射層
  ├─ SessionsReset           →  TaskUpdate (清除任務)
  ├─ SessionsSwitch          →  切換 TASK_LIST_ID
  ├─ Bash 工具                →  直接使用 Claude Code Bash
  └─ 自定義工具               →  通過 Skill 擴展

agent-scope.ts               →  保留 (配置解析)
routing/session-key.ts       →  保留 (session 識別)
```

#### 實作策略

**階段 1：保留 Session 層**
```typescript
// 保留這些檔案
src/routing/resolve-route.ts
src/routing/session-key.ts
src/agents/agent-scope.ts
src/config/sessions.ts

// 新增映射層
src/agents/claude-code-adapter.ts
```

**階段 2：移除 Pi Agent**
```typescript
// 移除這些檔案
src/agents/pi-embedded-runner.ts
src/agents/pi-embedded-subscribe.ts
src/agents/pi-embedded-utils.ts
src/agents/pi-embedded-helpers/
src/agents/pi-tools.ts
```

**階段 3：工具映射**
```typescript
// src/agents/claude-code-adapter.ts

export async function executeWithClaudeCode(params: {
  sessionKey: string;
  message: string;
  tools: string[];
}) {
  const taskListId = hashSessionKey(params.sessionKey);

  // 設定環境變數
  process.env.CLAUDE_CODE_TASK_LIST_ID = taskListId;

  // 建立任務
  await TaskCreate({
    subject: `Process message: ${params.message.slice(0, 50)}...`,
    description: params.message,
    activeForm: "Processing Telegram message",
  });
}
```

### 4. 權限系統重構

#### 現有權限檢查點

1. **命令層級** (`src/auto-reply/command-auth.ts`)
   - `resolveCommandAuthorization()` - 檢查發送者是否在 allowFrom
   - 支援 `*` 通配符（開放模式）
   - 支援 E.164 電話號碼格式

2. **Channel 層級** (`src/telegram/bot.ts`)
   - `allowFrom` 和 `groupAllowFrom` 解析
   - 群組權限檢查
   - 原生命令啟用檢查

3. **配置層級** (`src/config/types.telegram.ts`)
   ```typescript
   allowFrom?: Array<string | number>;
   groupAllowFrom?: Array<string | number>;
   dmPolicy?: "open" | "pairing" | "disabled";
   groupPolicy?: "open" | "disabled" | "allowlist";
   ```

#### 加強方案

**集中化權限引擎**：
```typescript
// src/security/permission-engine.ts

export type Permission = {
  resource: "command" | "tool" | "channel" | "agent";
  action: "execute" | "read" | "write" | "admin";
  subject: string; // senderId
  object: string;  // resource identifier
};

export interface PermissionPolicy {
  evaluate(permission: Permission): Promise<{
    allowed: boolean;
    reason?: string;
    auditLog?: AuditEntry;
  }>;
}
```

**審計日誌**：
```typescript
// src/security/audit-logger.ts

export interface AuditEntry {
  timestamp: string;
  permissionId: string;
  subject: string;
  resource: string;
  action: string;
  allowed: boolean;
  reason?: string;
  metadata?: Record<string, unknown>;
}

// 所有權限決策寫入
.claude/audit/permissions-YYYY-MM-DD.jsonl
```

### 5. MVP 最小化架構

**保留模組（核心 30%）**：
```
src/
├── cli/                 # CLI 介面
├── config/              # 配置系統
├── gateway/             # Gateway 控制平面
├── plugins/             # 插件系統
├── channels/
│   └── registry.ts      # Channel 註冊（只保留基礎）
├── telegram/            # 唯一 Channel
├── routing/             # Session 路由
├── auto-reply/          # 自動回覆引擎
├── agents/
│   ├── agent-scope.ts   # Agent 配置
│   └── claude-code-adapter.ts  # 新增：Claude Code 整合
├── infra/               # 基礎設施
└── security/            # 新增：權限引擎
```

**移除模組（70%）**：
```
src/
├── whatsapp/
├── discord/
├── slack/
├── signal/
├── imessage/
├── googlechat/
├── line/
├── agents/pi-embedded-*
├── agents/pi-tools.*
├── browser/
├── canvas-host/
├── macos/
├── tts/
└── ...
```

## 建議與洞察

### 1. Claude Code 整合優先級

**P0 - 基礎整合**：
- Session 管理映射（sessionKey → TASK_LIST_ID）
- 基礎工具映射（Bash, Read, Write）
- 消息傳遞流程（Telegram → Claude Code → Telegram）

**P1 - 進階功能**：
- 工具執行狀態同步（TaskUpdate）
- 多 Agent 支援（跨 TASK_LIST_ID）
- 錯誤處理與重試

**P2 - 優化**：
- 工具調用快取
- 並行執行優化
- Context 壓縮

### 2. 權限管控快速啟動

**第一階段（最小化）**：
- 保留現有 `allowFrom` 機制
- 添加審計日誌（所有命令執行記錄）
- 添加 `dmPolicy="pairing"` 強制執行

**第二階段（增強）**：
- 細粒度命令權限（YAML 配置）
- 工具級別權限（Bash 需要明確授權）
- 審批流程（高風險操作需要 approve）

**第三階段（完整）**：
- 時間窗口限制（只在特定時間段執行）
- 資源配額（Token 限制、API 調用限制）
- 多因素驗證（敏感操作需要額外驗證）

### 3. 可移植性保障

**配置驅動**：
- 所有 Channel 配置在 `config.json5`
- 權限規則在 `permissions.yaml`
- 零硬編碼依賴

**狀態隔離**：
- Session 存儲在 `.claude/sessions/`
- 配置存儲在 `.claude/config.json5`
- 審計日誌在 `.claude/audit/`

**Docker 支援**：
```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY src/ ./src/
RUN pnpm build

ENV CLAWDBOT_CHANNELS=telegram
ENV CLAWDBOT_AGENT_MODE=claude-code

CMD ["node", "dist/entry.js", "gateway"]
```

## 風險與注意事項

### 1. 架構風險

**風險：Plugin 系統過度設計**
- **影響**：MVP 不需要動態插件加載
- **緩解**：保留 PluginRegistry 結構，但簡化為靜態註冊
- **建議**：未來擴展時再啟用動態加載

**風險：Session 管理複雜度**
- **影響**：`routing/session-key.ts` 支援多種 session scope
- **緩解**：MVP 只使用 `main` scope（最簡單模式）
- **建議**：保留代碼但配置只使用單一模式

### 2. Claude Code 整合風險

**風險：API 穩定性**
- **影響**：Claude Code Task API 可能變更
- **緩解**：建立 adapter 層，隔離 API 變更影響
- **建議**：版本鎖定 Claude Code，定期測試相容性

**風險：工具映射不完整**
- **影響**：Clawdbot 自定義工具無法直接映射
- **緩解**：優先使用 Claude Code 原生工具，自定義工具通過 Skill 擴展
- **建議**：建立工具相容性矩陣

### 3. 權限系統風險

**風險：向後相容性**
- **影響**：現有 `allowFrom` 配置可能不相容新系統
- **緩解**：建立遷移腳本，自動轉換舊配置
- **建議**：保留舊配置格式支援（deprecation 警告）

**風險：審計日誌隱私**
- **影響**：日誌可能包含敏感消息內容
- **緩解**：可配置脫敏策略（hash 消息內容）
- **建議**：預設只記錄 metadata，不記錄完整消息

### 4. 移除依賴風險

**風險：隱性依賴遺漏**
- **影響**：移除 WhatsApp 等 channel 後，可能影響共用基礎設施
- **緩解**：建立依賴分析工具，檢測跨模組依賴
- **建議**：漸進式移除，每次移除後執行完整測試

**風險：配置類型錯誤**
- **影響**：移除 channel 後，TypeScript 類型定義可能不一致
- **緩解**：保留類型定義但標記為 deprecated
- **建議**：使用條件類型，根據啟用 channel 動態生成類型

### 5. 效能風險

**風險：Claude Code IPC 延遲**
- **影響**：Telegram → Claude Code → Telegram 往返延遲
- **緩解**：使用 WebSocket 而非 HTTP 輪詢
- **建議**：實作消息佇列，非同步處理長時間任務

**風險：Session 存儲膨脹**
- **影響**：長期運行後 `.claude/sessions/` 可能過大
- **緩解**：實作自動清理策略（30 天未活動自動歸檔）
- **建議**：使用 SQLite 替代 JSON 檔案存儲

---

**信心度**: 高

*由架構分析師視角產出*
