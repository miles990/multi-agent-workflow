# UX 倡導者視角報告

**視角**: ux-advocate
**聚焦**: 使用者體驗、API 設計
**模型**: haiku
**日期**: 2026-01-27

---

## 執行摘要

本報告從使用者體驗角度分析 Clawdbot MVP。主要關注兩類使用者：**終端用戶**（Telegram 使用者）和**開發者**（配置和擴展系統的人）。核心建議是保持**認知簡單**、**回饋即時**、**錯誤友善**。

---

## 1. 使用者旅程

### 1.1 終端用戶旅程

```
┌─────────────────────────────────────────────────────────────────┐
│                    TELEGRAM 用戶旅程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. 發現         2. 配對          3. 首次對話      4. 日常使用    │
│  ┌────────┐     ┌────────┐      ┌────────┐      ┌────────┐     │
│  │ 搜尋 Bot│────▶│ /start │────▶│ 發送訊息│────▶│ 持續互動│     │
│  │        │     │ /pair  │      │ 等待回覆│      │        │     │
│  └────────┘     └────────┘      └────────┘      └────────┘     │
│       ↓              ↓               ↓               ↓          │
│   [期待]         [期待]          [期待]          [期待]         │
│   簡單找到       快速完成        <10s 回覆       穩定可靠        │
│                                                                  │
│   [痛點]         [痛點]          [痛點]          [痛點]         │
│   找不到入口     驗證繁瑣        無回應焦慮      功能不明確      │
│                  不知下一步      不知進度        忘記命令        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 開發者旅程

```
┌─────────────────────────────────────────────────────────────────┐
│                    開發者配置旅程                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. 安裝         2. 配置          3. 啟動         4. 除錯        │
│  ┌────────┐     ┌────────┐      ┌────────┐      ┌────────┐     │
│  │ npm i  │────▶│ 編輯    │────▶│ start  │────▶│ 查日誌  │     │
│  │        │     │ config │      │        │      │        │     │
│  └────────┘     └────────┘      └────────┘      └────────┘     │
│       ↓              ↓               ↓               ↓          │
│   [期待]         [期待]          [期待]          [期待]         │
│   一行搞定       有範例          即時回饋        錯誤可查        │
│                  有驗證          成功提示        有上下文        │
│                                                                  │
│   [痛點]         [痛點]          [痛點]          [痛點]         │
│   依賴問題       配置不清楚      靜默失敗        日誌難讀        │
│   版本衝突       缺少範例        不知是否成功    找不到原因      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 終端用戶 UX 設計

### 2.1 首次互動（Onboarding）

#### 問題：配對流程可能混淆

**建議設計**：

```
用戶: /start

Bot: 👋 歡迎使用 Clawdbot！

我是一個 AI 助手，可以幫你完成各種任務。

📋 開始前，請完成驗證：
1. 發送 /pair 開始配對
2. 輸入你的配對碼

需要幫助？發送 /help
```

```
用戶: /pair

Bot: 🔐 配對驗證

請輸入管理員提供的配對碼：
（格式：XXXX-XXXX）

❓ 沒有配對碼？請聯繫管理員。
發送 /cancel 取消配對。
```

**關鍵原則**：
- 明確的下一步指引
- 簡潔但足夠的資訊
- 提供求助出口

### 2.2 對話中體驗

#### 問題：長時間等待產生焦慮

**建議設計**：

```
用戶: 幫我寫一個 Python 函數

Bot: [typing indicator 開始]
     💭 正在思考...

     [5秒後如果還沒完成]
     ⏳ 處理中，這可能需要一點時間...

     [完成]
     好的，這是你需要的函數：
     ```python
     def example():
         ...
     ```
```

**實作建議**：
```typescript
// src/telegram/typing.ts

export class TypingController {
  private intervalId: NodeJS.Timer | null = null;
  private messageId: number | null = null;

  async start(ctx: Context): Promise<void> {
    // 1. 立即開始 typing indicator
    await ctx.sendChatAction('typing');

    // 2. 每 4 秒刷新（Telegram typing 5秒過期）
    this.intervalId = setInterval(async () => {
      await ctx.sendChatAction('typing');
    }, 4000);

    // 3. 5秒後發送「處理中」提示
    setTimeout(async () => {
      if (this.intervalId) {
        const msg = await ctx.reply('⏳ 處理中...');
        this.messageId = msg.message_id;
      }
    }, 5000);
  }

  async stop(ctx: Context): Promise<void> {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }

    // 刪除「處理中」訊息
    if (this.messageId) {
      try {
        await ctx.api.deleteMessage(ctx.chat!.id, this.messageId);
      } catch { /* 忽略 */ }
    }
  }
}
```

### 2.3 錯誤處理

#### 問題：錯誤訊息不友善

**建議設計**：

| 錯誤類型 | 不好的訊息 | 好的訊息 |
|---------|-----------|---------|
| 權限不足 | `Error: Permission denied` | `抱歉，你還沒有權限使用這個功能。請先完成 /pair 配對。` |
| 服務錯誤 | `Internal server error` | `處理時遇到問題，請稍後再試。如果持續發生，請聯繫管理員。` |
| 速率限制 | `429 Too Many Requests` | `你發送太快了！請稍等一下再試。` |

**實作建議**：
```typescript
// src/utils/errors.ts

export const USER_FRIENDLY_ERRORS = {
  NOT_PAIRED: '🔒 請先完成配對驗證。發送 /pair 開始。',
  NOT_ALLOWED: '⛔ 抱歉，你沒有權限使用這個功能。',
  RATE_LIMITED: '⏰ 請稍等一下再發送訊息。',
  SERVICE_ERROR: '😕 處理時遇到問題，請稍後再試。',
  TIMEOUT: '⌛ 回覆時間過長，請稍後再試。',
} as const;

export function toUserFriendly(error: Error): string {
  // 映射內部錯誤到用戶友善訊息
  if (error.message.includes('not_paired')) {
    return USER_FRIENDLY_ERRORS.NOT_PAIRED;
  }
  // ... 其他映射
  return USER_FRIENDLY_ERRORS.SERVICE_ERROR;
}
```

### 2.4 命令設計

#### 問題：命令太多難記

**建議設計**：MVP 只需 5 個命令

| 命令 | 功能 | 別名 |
|------|------|------|
| `/start` | 開始使用 | - |
| `/pair` | 配對驗證 | - |
| `/help` | 查看幫助 | `/h` |
| `/status` | 查看狀態 | `/s` |
| `/reset` | 重置對話 | `/r` |

**命令選單設計**：
```typescript
// src/telegram/bot.ts

await bot.api.setMyCommands([
  { command: 'start', description: '開始使用' },
  { command: 'pair', description: '配對驗證' },
  { command: 'help', description: '查看幫助' },
  { command: 'status', description: '查看狀態' },
  { command: 'reset', description: '重置對話' },
]);
```

---

## 3. 開發者 UX 設計

### 3.1 快速開始

**README 範例**：
```markdown
## 快速開始

1. 安裝
\`\`\`bash
npm install -g clawdbot-mvp
\`\`\`

2. 配置
\`\`\`bash
clawdbot init  # 互動式建立配置
\`\`\`

3. 啟動
\`\`\`bash
TELEGRAM_BOT_TOKEN=your-token clawdbot start
\`\`\`

就這樣！你的 Bot 現在已經在線了 🎉
```

### 3.2 配置驗證

**問題**：配置錯誤難以發現

**建議設計**：
```bash
$ clawdbot config check

✅ 配置檔案有效

📋 配置摘要:
  - Telegram Bot: @your_bot
  - DM Policy: pairing
  - Allowlist: 2 users
  - Tool Profile: coding

⚠️  警告:
  - group_policy 設為 disabled，群組功能將不可用

🔧 建議:
  - 建議設定 AUDIT_RETENTION 環境變數
```

**實作建議**：
```typescript
// src/cli/config-check.ts

export async function checkConfig(configPath: string): Promise<void> {
  const spinner = ora('檢查配置...').start();

  try {
    const config = await loadConfig(configPath);
    spinner.succeed('配置檔案有效');

    // 顯示摘要
    console.log('\n📋 配置摘要:');
    console.log(`  - DM Policy: ${config.security.dm_policy}`);
    console.log(`  - Allowlist: ${config.security.allowlist.length} users`);

    // 警告
    const warnings = validateWarnings(config);
    if (warnings.length > 0) {
      console.log('\n⚠️  警告:');
      warnings.forEach(w => console.log(`  - ${w}`));
    }

  } catch (error) {
    spinner.fail('配置無效');
    console.error(formatConfigError(error));
    process.exit(1);
  }
}

function formatConfigError(error: ZodError): string {
  // 將 Zod 錯誤轉換為可讀格式
  return error.issues.map(issue => {
    const path = issue.path.join('.');
    return `❌ ${path}: ${issue.message}`;
  }).join('\n');
}
```

### 3.3 日誌設計

**問題**：日誌難以閱讀和過濾

**建議設計**：
```typescript
// 結構化日誌
{
  "level": "info",
  "time": "2026-01-27T12:00:00.000Z",
  "msg": "Message processed",
  "sessionKey": "abc123",
  "userId": "12345",
  "duration": 1234,
  "success": true
}

// 開發模式：可讀格式
[12:00:00] INFO  Message processed
           ├─ session: abc123
           ├─ user: 12345
           └─ duration: 1.2s ✓
```

**實作建議**：
```typescript
// src/utils/logger.ts

import pino from 'pino';

const isDev = process.env.NODE_ENV !== 'production';

export const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  transport: isDev ? {
    target: 'pino-pretty',
    options: {
      colorize: true,
      translateTime: 'HH:MM:ss',
      ignore: 'pid,hostname',
    }
  } : undefined,
  redact: ['token', 'apiKey', '*.password'],
});
```

---

## 4. API 設計原則

### 4.1 配置 API

**原則**：合理預設、最小配置

```yaml
# 最小配置（僅必填項）
telegram:
  token: ${TELEGRAM_BOT_TOKEN}

security:
  allowlist:
    - user_id: "123456789"
```

```yaml
# 完整配置（顯示所有選項）
telegram:
  token: ${TELEGRAM_BOT_TOKEN}
  polling:
    timeout: 30                    # 預設: 30
    allowed_updates: ["message"]   # 預設: ["message", "callback_query"]

claude:
  model: sonnet                    # 預設: sonnet
  max_turns: 10                    # 預設: 10

security:
  dm_policy: pairing               # 預設: pairing
  group_policy: disabled           # 預設: disabled
  allowlist:
    - user_id: "123456789"
      permissions: ["*"]           # 預設: ["*"]
```

### 4.2 錯誤訊息 API

**原則**：結構化、可操作

```typescript
interface UserError {
  code: string;           // 機器可讀：'NOT_PAIRED'
  message: string;        // 用戶可讀：'請先完成配對'
  action?: string;        // 建議動作：'發送 /pair'
  details?: string;       // 技術細節（開發模式）
}
```

### 4.3 事件 API（未來擴展）

**原則**：預留 Hook 點

```typescript
interface ClawdbotEvents {
  'message:received': (ctx: MessageContext) => void;
  'message:processed': (ctx: MessageContext, response: string) => void;
  'permission:denied': (ctx: PermissionContext, reason: string) => void;
  'error': (error: Error, ctx?: MessageContext) => void;
}
```

---

## 5. 建議總結

### 5.1 終端用戶（優先）

| 優先級 | 建議 | 影響 |
|--------|------|------|
| P0 | Typing indicator + 進度提示 | 減少等待焦慮 |
| P0 | 友善錯誤訊息 | 用戶知道如何修復 |
| P1 | 簡化命令（5 個） | 降低認知負擔 |
| P1 | 清晰的配對流程 | 順利上手 |
| P2 | 命令選單 | 探索功能 |

### 5.2 開發者

| 優先級 | 建議 | 影響 |
|--------|------|------|
| P0 | 配置驗證 + 錯誤訊息 | 快速發現問題 |
| P1 | 互動式 init | 快速上手 |
| P1 | 結構化日誌 | 易於除錯 |
| P2 | 開發模式友好輸出 | 開發體驗 |

### 5.3 不做的事

- 複雜的多語言支援（MVP 只用繁中）
- 自訂 UI 主題
- 複雜的對話管理 UI

---

**報告生成時間**: 2026-01-27
**視角**: ux-advocate
**信心度**: 高
