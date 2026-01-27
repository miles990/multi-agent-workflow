# Clawdbot MVP 實作計劃

**版本**: 1.0
**日期**: 2026-01-27
**狀態**: 規劃完成，待實作

---

## 1. 專案概述

### 1.1 目標

基於 Clawdbot 專案打造輕量 MVP，實現以下目標：

| 目標 | 說明 |
|------|------|
| **單一 Channel** | 僅支援 Telegram（Long Polling） |
| **Claude Code 整合** | 使用 Task API 替代內建 Agent Runtime |
| **精簡記憶系統** | JSON-first，無向量搜尋 |
| **強化權限控制** | 集中化檢查 + Allowlist + Audit |
| **保留擴展性** | 保留插件架構核心介面 |

### 1.2 非目標（明確排除）

- 多 Channel 支援（Discord, Slack 等）
- 向量搜尋 / RAG 功能
- Block Streaming / Coalescing
- 複雜的 Queue Mode
- Memory Search 功能
- 群組 AI 互動

---

## 2. 架構設計

### 2.1 系統架構

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLAWDBOT MVP                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌───────────────────────────────────────────────────────┐     │
│   │                 TELEGRAM (Grammy)                      │     │
│   │   • Long Polling          • Typing Indicator          │     │
│   │   • Message Handler       • Command Handler           │     │
│   └───────────────────────────────────────────────────────┘     │
│                              ↓                                   │
│   ┌───────────────────────────────────────────────────────┐     │
│   │                    GATEWAY                             │     │
│   │   • Permission Checker    • Message Router            │     │
│   │   • Audit Logger          • Session Key Generator     │     │
│   │   • Tool API Endpoint                                 │     │
│   └───────────────────────────────────────────────────────┘     │
│                              ↓                                   │
│   ┌───────────────────────────────────────────────────────┐     │
│   │               CLAUDE CODE ADAPTER                      │     │
│   │   • Task API Integration  • Response Streaming        │     │
│   │   • Tool Callback         • Context Management        │     │
│   └───────────────────────────────────────────────────────┘     │
│                              ↓                                   │
│   ┌───────────────────────────────────────────────────────┐     │
│   │                   STORAGE                              │     │
│   │   • Session Store (JSON)  • Transcript Store (JSONL)  │     │
│   │   • Audit Store (JSONL)   • Config Store (YAML)       │     │
│   └───────────────────────────────────────────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 目錄結構

```
clawdbot-mvp/
├── src/
│   ├── index.ts                    # 主入口
│   ├── config/                     # 配置系統
│   │   ├── schema.ts               # Zod schemas
│   │   ├── loader.ts               # 配置載入
│   │   └── types.ts                # 類型定義
│   ├── telegram/                   # Telegram 整合
│   │   ├── bot.ts                  # Grammy Bot
│   │   ├── handlers.ts             # 消息處理
│   │   ├── commands.ts             # 命令處理
│   │   ├── middleware.ts           # 中間件
│   │   └── typing.ts               # Typing 控制
│   ├── gateway/                    # Gateway 層
│   │   ├── router.ts               # 消息路由
│   │   ├── session-key.ts          # Session Key
│   │   └── tool-api.ts             # Tool API
│   ├── security/                   # 安全系統
│   │   ├── permission.ts           # 權限檢查
│   │   ├── allowlist.ts            # Allowlist
│   │   ├── pairing.ts              # DM 配對
│   │   └── audit.ts                # 審計日誌
│   ├── agents/                     # Agent 整合
│   │   ├── claude-adapter.ts       # Claude Code Adapter
│   │   ├── agent-scope.ts          # Agent 配置
│   │   └── types.ts                # Agent 類型
│   ├── storage/                    # 存儲系統
│   │   ├── json-store.ts           # JSON 存儲
│   │   ├── session-store.ts        # Session 存儲
│   │   └── audit-store.ts          # Audit 存儲
│   ├── cli/                        # CLI 工具
│   │   ├── index.ts                # CLI 入口
│   │   ├── start.ts                # start 命令
│   │   └── config-check.ts         # config check 命令
│   └── utils/                      # 工具函數
│       ├── logger.ts               # 日誌
│       └── errors.ts               # 錯誤處理
├── config/
│   ├── default.yaml                # 預設配置
│   └── schema.json                 # JSON Schema
├── tests/
│   ├── unit/                       # 單元測試
│   ├── integration/                # 整合測試
│   └── e2e/                        # E2E 測試
├── docs/
│   ├── architecture.md             # 架構文檔
│   └── deployment.md               # 部署指南
├── package.json
├── tsconfig.json
└── README.md
```

---

## 3. 核心功能設計

### 3.1 Claude Code 整合

**整合方式**: 透過 subprocess 調用 Claude Code CLI

```typescript
// src/agents/claude-adapter.ts

interface ClaudeCodeAdapter {
  processMessage(ctx: MessageContext): AsyncGenerator<string>;
  invokeToolCallback(tool: ToolInvocation): Promise<ToolResult>;
}

// 流程
// 1. Telegram 消息 → Gateway 權限檢查
// 2. Gateway → spawn('claude', [...args])
// 3. Claude Code 執行，工具調用 → Gateway Tool API
// 4. Claude Code 回覆 → Gateway → Telegram
```

**Tool API 設計**:
```typescript
// src/gateway/tool-api.ts

// HTTP 端點供 Claude Code 回調
POST /api/tools/invoke
{
  "tool": "send_telegram_message",
  "params": { "chat_id": "123", "text": "Hello" },
  "context": { "sessionKey": "abc" }
}
```

### 3.2 權限系統

**集中化設計**: 所有權限邏輯在 `PermissionChecker` 類中

```typescript
// src/security/permission.ts

class PermissionChecker {
  async check(ctx: PermissionContext): Promise<PermissionResult> {
    // 1. Allowlist 檢查（O(1)）
    // 2. DM Policy 檢查
    // 3. Group Policy 檢查
    // 4. Tool Policy 檢查
    // 全部通過 → allowed: true
  }
}
```

**Allowlist 配置**:
```yaml
security:
  allowlist:
    - user_id: "123456789"
      permissions: ["*"]
    - user_id: "987654321"
      permissions: ["read", "chat"]
```

### 3.3 記憶系統

**簡化設計**: JSON 檔案存儲，無向量搜尋

```
.clawdbot/
├── sessions/
│   └── {session-key}.json      # Session 元數據
├── transcripts/
│   └── {session-key}.jsonl     # 對話記錄
└── audit/
    └── {date}.jsonl            # 審計日誌
```

**Session 結構**:
```typescript
interface SessionData {
  sessionKey: string;
  userId: string;
  chatId: string;
  createdAt: number;
  lastActiveAt: number;
  messageCount: number;
}
```

### 3.4 消息處理流程

```
接收 → 權限檢查 → Claude Code 處理 → 回覆

詳細流程:
1. Grammy 收到 Telegram 消息
2. middleware 提取用戶資訊
3. PermissionChecker.check()
4. 生成 SessionKey
5. 啟動 TypingController
6. ClaudeAdapter.processMessage()
7. 串流回覆到 Telegram
8. 記錄到 Transcript
9. 記錄到 AuditLog
```

---

## 4. 配置設計

### 4.1 配置 Schema

```yaml
# config/default.yaml

# Telegram 設定
telegram:
  token: ${TELEGRAM_BOT_TOKEN}
  polling:
    timeout: 30
    allowed_updates:
      - message
      - callback_query

# Claude Code 設定
claude:
  model: sonnet          # sonnet | opus | haiku
  max_turns: 10
  working_dir: "."
  allowed_tools:
    - read
    - write
    - edit
    - bash
    - search

# 安全設定
security:
  dm_policy: pairing     # pairing | allowlist | open
  group_policy: disabled # disabled | mention_only | always_on

  allowlist:
    - user_id: "123456789"
      permissions:
        - "*"

  tool_policy:
    profile: coding      # minimal | coding | messaging
    deny:
      - exec.dangerous

  audit:
    enabled: true
    retention: 30d
    redact_content: true

# 存儲設定
storage:
  base_dir: ".clawdbot"
```

### 4.2 環境變數

| 變數 | 必填 | 說明 |
|------|------|------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram Bot Token |
| `SESSION_SECRET` | ✅ | Session 加密金鑰 |
| `LOG_LEVEL` | ❌ | 日誌級別（預設: info） |
| `NODE_ENV` | ❌ | 環境（development/production） |

---

## 5. 開發計劃

### 5.1 里程碑

| 里程碑 | 週次 | 產出 | 驗收標準 |
|--------|------|------|---------|
| M1: Skeleton | W1 | 專案骨架 | CI 通過，配置載入成功 |
| M2: Security | W2 | 權限系統 | 權限測試 100% 通過 |
| M3: Core | W4 | Claude Code 整合 | 可透過 API 對話 |
| M4: Integration | W5 | Telegram Bot | Bot 可收發訊息 |
| M5: Feature Complete | W6 | 全功能 | 所有功能可用 |
| M6: Release | W7 | 生產就緒 | E2E 測試通過 |

### 5.2 任務分解

#### M1: Skeleton (Week 1)
- [ ] 初始化專案（tsconfig, package.json, eslint）
- [ ] 建立目錄結構
- [ ] 配置系統（schema, loader）
- [ ] CI/CD 設定

#### M2: Security (Week 2)
- [ ] Allowlist 管理
- [ ] DM Pairing 流程
- [ ] 集中化 PermissionChecker
- [ ] Audit Logger

#### M3: Core (Week 3-4)
- [ ] Claude Code Adapter 設計
- [ ] Task API 整合
- [ ] Tool API 端點
- [ ] Response 串流處理

#### M4: Integration (Week 5)
- [ ] Grammy Bot 設定
- [ ] 消息處理器
- [ ] 命令處理器
- [ ] Typing 控制

#### M5: Feature Complete (Week 6)
- [ ] Session 存儲
- [ ] Transcript 存儲
- [ ] CLI 工具
- [ ] 文檔

#### M6: Release (Week 7)
- [ ] E2E 測試
- [ ] 效能測試
- [ ] 安全測試
- [ ] 部署指南

---

## 6. 技術選型

### 6.1 依賴項

| 類別 | 套件 | 版本 | 用途 |
|------|------|------|------|
| Runtime | Node.js | ^20.0 | JavaScript 執行環境 |
| Telegram | grammy | ^1.21 | Telegram Bot API |
| Validation | zod | ^3.22 | Schema 驗證 |
| Config | yaml | ^2.3 | YAML 解析 |
| Logging | pino | ^8.17 | 結構化日誌 |
| CLI | commander | ^11.1 | CLI 框架 |
| Testing | vitest | ^1.2 | 測試框架 |
| Build | tsup | ^8.0 | 打包工具 |

### 6.2 開發工具

| 工具 | 版本 | 用途 |
|------|------|------|
| TypeScript | ^5.3 | 語言 |
| ESLint | ^8.56 | Linting |
| Prettier | ^3.2 | 格式化 |
| pnpm | ^8.0 | 套件管理 |

---

## 7. 風險與緩解

### 7.1 高優先級風險

| 風險 | 緩解措施 |
|------|---------|
| Claude Code API 變更 | Adapter 模式隔離，版本鎖定 |
| 權限繞過 | 集中化檢查，100% 測試覆蓋 |
| API 金鑰洩漏 | 環境變數，日誌 redact |

### 7.2 監控指標

| 指標 | 目標 |
|------|------|
| 權限檢查通過率 | 監控異常模式 |
| 回覆延遲 P95 | < 10 秒 |
| 錯誤率 | < 1% |

---

## 8. 成功指標

| 指標 | 目標 | 量測方式 |
|------|------|---------|
| 功能完整性 | 所有 MVP 功能可用 | 功能測試 |
| 安全性 | 無已知漏洞 | 安全測試 |
| 效能 | 回覆 < 10s (P95) | 效能測試 |
| 測試覆蓋 | > 80% | vitest coverage |

---

## 9. 未來規劃（v2.0）

以下功能明確排除在 MVP 範圍外，留待未來版本：

- [ ] 向量搜尋 / Memory Search
- [ ] 多 Channel 支援
- [ ] Block Streaming
- [ ] RBAC 權限系統
- [ ] 群組 AI 互動
- [ ] 監控儀表板

---

## 附錄

### A. 研究報告參考

- [輕量 MVP 研究](../research/clawdbot-lightweight-mvp/synthesis.md)
- [記憶系統研究](../research/clawdbot-memory-system/synthesis.md)
- [自動回報研究](../research/clawdbot-auto-reply-system/synthesis.md)
- [組件化策略研究](../research/clawdbot-componentization/synthesis.md)

### B. 視角報告

- [架構師報告](./perspectives/architect.md)
- [風險分析師報告](./perspectives/risk-analyst.md)
- [估算專家報告](./perspectives/estimator.md)
- [UX 倡導者報告](./perspectives/ux-advocate.md)

---

**規劃完成時間**: 2026-01-27
**下一步**: TASKS 階段 - 任務分解
**預計開發時間**: 7-9 週
