# 系統架構師視角報告

**視角**: architect
**聚焦**: 技術可行性、組件設計
**模型**: sonnet
**日期**: 2026-01-27

---

## 執行摘要

基於四份研究報告（輕量 MVP、記憶系統、自動回報、組件化策略），本報告提供 Clawdbot MVP 的技術架構設計。核心策略是「**保留骨架，精簡功能**」—— 保留 Clawdbot 經過驗證的插件架構和設計模式，移除不必要的功能實作，將 Agent 執行責任轉移給 Claude Code。

---

## 1. 架構設計

### 1.1 系統分層

```
┌─────────────────────────────────────────────────────────────┐
│                     CLAWDBOT MVP                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              TELEGRAM LAYER (Grammy)                  │   │
│  │  • Long Polling (getUpdates)                         │   │
│  │  • Telegram Bot API Client                           │   │
│  │  • Typing Indicator + Heartbeat                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              GATEWAY LAYER                            │   │
│  │  • Message Router (session-key based)                │   │
│  │  • Permission Checker (centralized)                  │   │
│  │  • Audit Logger                                      │   │
│  │  • Tool Invocation API (for Claude Code)             │   │
│  └──────────────────────────────────────────────────────┘   │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              CLAUDE CODE ADAPTER                      │   │
│  │  • Task API Integration                              │   │
│  │  • Session Context Management                        │   │
│  │  • Tool Callback Handler                             │   │
│  │  • Response Streaming                                │   │
│  └──────────────────────────────────────────────────────┘   │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              STORAGE LAYER                            │   │
│  │  • JSON File Storage (sessions, config)              │   │
│  │  • Audit Log (JSONL)                                 │   │
│  │  • Session Transcript (.jsonl)                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 目錄結構

```
clawdbot-mvp/
├── src/
│   ├── index.ts                    # 主入口
│   ├── config/
│   │   ├── schema.ts               # 配置 schema（Zod）
│   │   ├── loader.ts               # 配置載入器
│   │   └── types.ts                # 配置類型
│   ├── telegram/
│   │   ├── bot.ts                  # Grammy Bot 設定
│   │   ├── handlers.ts             # 消息處理器
│   │   ├── middleware.ts           # 權限中間件
│   │   └── types.ts                # Telegram 類型
│   ├── gateway/
│   │   ├── router.ts               # 消息路由
│   │   ├── session-key.ts          # Session Key 生成
│   │   └── tool-api.ts             # Tool Invocation API
│   ├── security/
│   │   ├── permission.ts           # 集中化權限檢查
│   │   ├── allowlist.ts            # Allowlist 管理
│   │   ├── pairing.ts              # DM 配對驗證
│   │   └── audit.ts                # 審計日誌
│   ├── agents/
│   │   ├── claude-adapter.ts       # Claude Code 整合
│   │   ├── agent-scope.ts          # Agent 配置
│   │   └── types.ts                # Agent 類型
│   ├── storage/
│   │   ├── json-store.ts           # JSON 檔案存儲
│   │   ├── session-store.ts        # Session 存儲
│   │   └── audit-store.ts          # 審計存儲
│   └── utils/
│       ├── logger.ts               # 日誌工具
│       └── errors.ts               # 錯誤定義
├── config/
│   ├── default.yaml                # 預設配置
│   └── schema.json                 # JSON Schema
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── package.json
├── tsconfig.json
└── README.md
```

### 1.3 保留/移除決策

| 類別 | 保留（Clawdbot → MVP） | 移除 |
|------|------------------------|------|
| **Channel** | telegram/ (79 files → 4 files) | whatsapp/, discord/, slack/, signal/, imessage/, googlechat/, line/, matrix/, web/ |
| **Agent** | agent-scope.ts, session-key.ts | pi-embedded-*, pi-tools.*, agent runtime |
| **Memory** | Session transcript (.jsonl) | Vector search, SQLite, embeddings, memory-lancedb |
| **Auto-Reply** | 核心流程（簡化版） | Block streaming, queue modes, compaction |
| **Security** | permission.ts, audit.ts, pairing.ts | 複雜的多層檢查 |
| **Infrastructure** | config/, utils/ | browser/, canvas-host/, macos/, tts/, hooks/ (大部分) |
| **Plugins** | 核心介面 | 完整 Plugin Registry |

---

## 2. 核心組件設計

### 2.1 Claude Code Adapter

```typescript
// src/agents/claude-adapter.ts

import { spawn } from 'child_process';

export interface ClaudeAdapterConfig {
  model: 'sonnet' | 'opus' | 'haiku';
  maxTurns: number;
  allowedTools: string[];
  workingDir: string;
}

export interface MessageContext {
  sessionKey: string;
  userId: string;
  userName: string;
  chatId: string;
  chatType: 'private' | 'group';
  message: string;
  timestamp: number;
}

export interface ToolInvocation {
  tool: string;
  params: Record<string, unknown>;
  context: ToolContext;
}

export interface ToolContext {
  sessionKey: string;
  invokedBy: 'claude-code';
  timestamp: number;
}

export class ClaudeCodeAdapter {
  private config: ClaudeAdapterConfig;
  private toolApi: ToolApi;

  constructor(config: ClaudeAdapterConfig, toolApi: ToolApi) {
    this.config = config;
    this.toolApi = toolApi;
  }

  async processMessage(ctx: MessageContext): Promise<AsyncGenerator<string>> {
    // 1. 構建 prompt
    const prompt = this.buildPrompt(ctx);

    // 2. 啟動 Claude Code subprocess
    const process = spawn('claude', [
      '-p', prompt,
      '--model', this.config.model,
      '--max-turns', String(this.config.maxTurns),
      '--output-format', 'stream-json',
    ], {
      cwd: this.config.workingDir,
      env: {
        ...process.env,
        CLAUDE_CODE_TOOL_API: this.toolApi.getEndpoint(),
      },
    });

    // 3. 處理輸出流
    return this.handleOutputStream(process);
  }

  private buildPrompt(ctx: MessageContext): string {
    return `
You are an AI assistant helping ${ctx.userName}.
Session: ${ctx.sessionKey}
Chat Type: ${ctx.chatType}

User Message:
${ctx.message}
`.trim();
  }

  private async *handleOutputStream(process: ChildProcess): AsyncGenerator<string> {
    for await (const chunk of process.stdout) {
      const data = JSON.parse(chunk.toString());
      if (data.type === 'text') {
        yield data.content;
      } else if (data.type === 'tool_use') {
        await this.handleToolInvocation(data);
      }
    }
  }

  private async handleToolInvocation(data: ToolInvocation): Promise<void> {
    const result = await this.toolApi.invoke(data);
    // Tool result 會透過 stdin 回傳給 Claude Code
  }
}
```

### 2.2 權限系統（集中化）

```typescript
// src/security/permission.ts

import { z } from 'zod';

export const PermissionResultSchema = z.object({
  allowed: z.boolean(),
  reason: z.string().optional(),
  auditId: z.string(),
});

export type PermissionResult = z.infer<typeof PermissionResultSchema>;

export interface PermissionContext {
  userId: string;
  chatId: string;
  chatType: 'private' | 'group';
  action: 'message' | 'tool' | 'admin';
  toolName?: string;
}

export class PermissionChecker {
  private allowlist: AllowlistManager;
  private pairingManager: PairingManager;
  private auditLogger: AuditLogger;
  private config: SecurityConfig;

  constructor(deps: PermissionDependencies) {
    this.allowlist = deps.allowlist;
    this.pairingManager = deps.pairingManager;
    this.auditLogger = deps.auditLogger;
    this.config = deps.config;
  }

  /**
   * 集中化權限檢查 - 單一入口點
   *
   * 檢查順序（快速失敗）：
   * 1. Allowlist 檢查（最快）
   * 2. DM Policy 檢查
   * 3. Group Policy 檢查
   * 4. Tool Policy 檢查（如適用）
   */
  async check(ctx: PermissionContext): Promise<PermissionResult> {
    const auditId = this.auditLogger.startCheck(ctx);

    try {
      // Step 1: Allowlist（快速路徑）
      const allowlistResult = this.allowlist.check(ctx.userId);
      if (allowlistResult.denied) {
        return this.deny(auditId, 'not_in_allowlist');
      }

      // Step 2: DM Policy
      if (ctx.chatType === 'private') {
        if (this.config.dmPolicy === 'pairing') {
          const paired = await this.pairingManager.isPaired(ctx.userId);
          if (!paired) {
            return this.deny(auditId, 'dm_not_paired');
          }
        }
      }

      // Step 3: Group Policy
      if (ctx.chatType === 'group') {
        if (this.config.groupPolicy === 'disabled') {
          return this.deny(auditId, 'group_disabled');
        }
      }

      // Step 4: Tool Policy（如適用）
      if (ctx.action === 'tool' && ctx.toolName) {
        const toolAllowed = this.checkToolPolicy(ctx.toolName, allowlistResult.permissions);
        if (!toolAllowed) {
          return this.deny(auditId, 'tool_denied', ctx.toolName);
        }
      }

      // 全部通過
      return this.allow(auditId);

    } catch (error) {
      return this.deny(auditId, 'check_error', error.message);
    }
  }

  private allow(auditId: string): PermissionResult {
    this.auditLogger.endCheck(auditId, { allowed: true });
    return { allowed: true, auditId };
  }

  private deny(auditId: string, reason: string, detail?: string): PermissionResult {
    this.auditLogger.endCheck(auditId, { allowed: false, reason, detail });
    return { allowed: false, reason, auditId };
  }

  private checkToolPolicy(toolName: string, userPermissions: string[]): boolean {
    // 檢查 deny list
    if (this.config.toolPolicy.deny.includes(toolName)) {
      return false;
    }

    // 檢查用戶權限
    if (userPermissions.includes('*')) {
      return true;
    }

    // 檢查 profile
    const profileTools = TOOL_PROFILES[this.config.toolPolicy.profile];
    return profileTools.includes(toolName);
  }
}

const TOOL_PROFILES = {
  minimal: ['read', 'search'],
  coding: ['read', 'write', 'edit', 'bash', 'search'],
  messaging: ['read', 'search', 'send_message'],
} as const;
```

### 2.3 記憶系統（JSON-first）

```typescript
// src/storage/session-store.ts

import fs from 'fs/promises';
import path from 'path';

export interface SessionData {
  sessionKey: string;
  userId: string;
  createdAt: number;
  lastActiveAt: number;
  messageCount: number;
  metadata: Record<string, unknown>;
}

export interface TranscriptEntry {
  timestamp: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: Record<string, unknown>;
}

export class SessionStore {
  private baseDir: string;

  constructor(baseDir: string) {
    this.baseDir = baseDir;
  }

  async getSession(sessionKey: string): Promise<SessionData | null> {
    const filePath = this.getSessionPath(sessionKey);
    try {
      const content = await fs.readFile(filePath, 'utf-8');
      return JSON.parse(content);
    } catch (error) {
      if (error.code === 'ENOENT') return null;
      throw error;
    }
  }

  async saveSession(session: SessionData): Promise<void> {
    const filePath = this.getSessionPath(session.sessionKey);
    await fs.mkdir(path.dirname(filePath), { recursive: true });
    await fs.writeFile(filePath, JSON.stringify(session, null, 2));
  }

  async appendTranscript(sessionKey: string, entry: TranscriptEntry): Promise<void> {
    const filePath = this.getTranscriptPath(sessionKey);
    await fs.mkdir(path.dirname(filePath), { recursive: true });
    await fs.appendFile(filePath, JSON.stringify(entry) + '\n');
  }

  async getTranscript(sessionKey: string, limit?: number): Promise<TranscriptEntry[]> {
    const filePath = this.getTranscriptPath(sessionKey);
    try {
      const content = await fs.readFile(filePath, 'utf-8');
      const lines = content.trim().split('\n');
      const entries = lines.map(line => JSON.parse(line));
      return limit ? entries.slice(-limit) : entries;
    } catch (error) {
      if (error.code === 'ENOENT') return [];
      throw error;
    }
  }

  private getSessionPath(sessionKey: string): string {
    return path.join(this.baseDir, 'sessions', `${sessionKey}.json`);
  }

  private getTranscriptPath(sessionKey: string): string {
    return path.join(this.baseDir, 'transcripts', `${sessionKey}.jsonl`);
  }
}
```

---

## 3. 訊息處理流程

### 3.1 簡化流程（4 層）

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  RECEIVE    │────▶│  AUTHORIZE  │────▶│   PROCESS   │────▶│   RESPOND   │
│             │     │             │     │             │     │             │
│ • Grammy    │     │ • Allowlist │     │ • Claude    │     │ • Telegram  │
│ • Parse     │     │ • DM Policy │     │   Code      │     │   API       │
│ • Validate  │     │ • Group     │     │ • Tool API  │     │ • Typing    │
│             │     │ • Audit Log │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
     ↓                    ↓                    ↓                    ↓
   ~10ms              ~5ms               ~2-10s                ~50ms
```

### 3.2 詳細流程

```typescript
// src/telegram/handlers.ts

export async function handleMessage(ctx: Context): Promise<void> {
  const startTime = Date.now();

  // 1. RECEIVE - 解析消息
  const parsed = parseMessage(ctx);
  if (!parsed.valid) {
    return; // 靜默忽略無效消息
  }

  // 2. AUTHORIZE - 權限檢查
  const permResult = await permissionChecker.check({
    userId: parsed.userId,
    chatId: parsed.chatId,
    chatType: parsed.chatType,
    action: 'message',
  });

  if (!permResult.allowed) {
    if (permResult.reason === 'dm_not_paired') {
      await ctx.reply('請先完成配對驗證。發送 /pair 開始。');
    }
    return;
  }

  // 3. PROCESS - Claude Code 處理
  const sessionKey = generateSessionKey(parsed);
  const messageCtx: MessageContext = {
    sessionKey,
    userId: parsed.userId,
    userName: parsed.userName,
    chatId: parsed.chatId,
    chatType: parsed.chatType,
    message: parsed.text,
    timestamp: Date.now(),
  };

  // 啟動 typing indicator
  const typingController = startTyping(ctx);

  try {
    // 調用 Claude Code
    const responseStream = await claudeAdapter.processMessage(messageCtx);

    // 4. RESPOND - 串流回覆
    let fullResponse = '';
    for await (const chunk of responseStream) {
      fullResponse += chunk;
      // 每 N 個字符發送一次（避免過於頻繁）
      if (fullResponse.length % 100 === 0) {
        await ctx.reply(fullResponse, { parse_mode: 'Markdown' });
      }
    }

    // 發送最終回覆
    if (fullResponse) {
      await ctx.reply(fullResponse, { parse_mode: 'Markdown' });
    }

    // 記錄 transcript
    await sessionStore.appendTranscript(sessionKey, {
      timestamp: Date.now(),
      role: 'user',
      content: parsed.text,
    });
    await sessionStore.appendTranscript(sessionKey, {
      timestamp: Date.now(),
      role: 'assistant',
      content: fullResponse,
    });

  } finally {
    typingController.stop();
    auditLogger.logRequest({
      sessionKey,
      duration: Date.now() - startTime,
      success: true,
    });
  }
}
```

---

## 4. 技術選型

### 4.1 依賴項

| 類別 | 套件 | 版本 | 用途 |
|------|------|------|------|
| **Telegram** | grammy | ^1.21 | Telegram Bot API |
| **Config** | zod | ^3.22 | Schema 驗證 |
| **Config** | yaml | ^2.3 | YAML 解析 |
| **Logging** | pino | ^8.17 | 結構化日誌 |
| **CLI** | commander | ^11.1 | CLI 工具 |
| **Testing** | vitest | ^1.2 | 單元測試 |
| **Build** | tsup | ^8.0 | 打包工具 |

### 4.2 配置 Schema

```yaml
# config/default.yaml

telegram:
  token: ${TELEGRAM_BOT_TOKEN}
  polling:
    timeout: 30
    allowed_updates: ["message", "callback_query"]

claude:
  model: sonnet
  max_turns: 10
  allowed_tools:
    - read
    - write
    - edit
    - bash
    - search

security:
  dm_policy: "pairing"      # pairing | allowlist | open
  group_policy: "disabled"   # disabled | mention_only | always_on

  allowlist:
    - user_id: "123456789"
      permissions: ["*"]
    - user_id: "987654321"
      permissions: ["read", "chat"]

  tool_policy:
    profile: "coding"        # minimal | coding | messaging
    deny:
      - "exec.dangerous"

  audit:
    enabled: true
    retention: "30d"
    redact_content: true

storage:
  base_dir: ".clawdbot"
  sessions_dir: "sessions"
  transcripts_dir: "transcripts"
  audit_dir: "audit"
```

---

## 5. 風險與緩解

### 5.1 架構風險

| 風險 | 嚴重度 | 緩解措施 |
|------|--------|---------|
| Claude Code API 變更 | 高 | Adapter 模式隔離，版本鎖定 |
| Long Polling 斷線 | 中 | Grammy 內建重試，offset 確認 |
| 權限繞過 | 高 | 集中化檢查，審計日誌 |
| Session 競態 | 中 | 檔案鎖定（fs-extra） |

### 5.2 技術決策風險

| 決策 | 風險 | 替代方案 |
|------|------|---------|
| JSON 存儲（非 SQLite） | 大量 session 時性能 | v2.0 遷移到 SQLite |
| 無向量搜尋 | 長對話的上下文檢索 | 依賴 Claude Code 內建能力 |
| Grammy Long Polling | 高負載時瓶頸 | v2.0 可選 Webhook |

---

## 6. 建議

### 6.1 立即行動

1. **Fork 基礎架構**：從 Clawdbot 提取 config/, utils/, 基礎類型
2. **實作 Claude Adapter**：Task API 整合是核心
3. **建立權限系統**：集中化設計，從第一天就正確

### 6.2 延後項目

1. **向量搜尋**：MVP 不需要，v2.0 考慮
2. **多 Channel**：保留介面，不實作
3. **Block Streaming**：簡化為基本回覆

---

**報告生成時間**: 2026-01-27
**視角**: architect
**信心度**: 高
