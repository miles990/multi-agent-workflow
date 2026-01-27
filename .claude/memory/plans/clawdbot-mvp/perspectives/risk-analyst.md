# 風險分析師視角報告

**視角**: risk-analyst
**聚焦**: 潛在風險、失敗場景
**模型**: sonnet
**日期**: 2026-01-27

---

## 執行摘要

本報告從風險管理角度分析 Clawdbot MVP 專案。共識別出 **23 項風險**，分為 5 類：技術風險、安全風險、營運風險、依賴風險、整合風險。其中 **8 項為 P0/P1 優先級**，需在開發初期即處理。

---

## 1. 風險總覽

### 1.1 風險矩陣

```
              影響
              ↑
         高   │  ⚠️ Claude API    🔴 權限繞過
              │     變更           安全漏洞
              │
         中   │  ⚠️ Long Polling  ⚠️ Session
              │     斷線           競態
              │
         低   │  ○ Typing 延遲   ○ 配置錯誤
              │
              └─────────────────────────→ 可能性
                    低      中      高
```

### 1.2 優先級分佈

| 優先級 | 數量 | 說明 |
|--------|------|------|
| P0（必須阻止） | 3 | 權限繞過、API 金鑰洩漏、Session 注入 |
| P1（高度重要） | 5 | Claude API 變更、配置驗證失敗、審計缺失、DoS、依賴漏洞 |
| P2（中度重要） | 8 | Long Polling、Session 競態、記憶丟失等 |
| P3（低度重要） | 7 | 可接受的風險，有基本緩解措施 |

---

## 2. 詳細風險分析

### 2.1 安全風險（P0 優先）

#### R1: 權限繞過攻擊
| 屬性 | 值 |
|------|-----|
| **優先級** | P0 |
| **可能性** | 中 |
| **影響** | 高 |
| **攻擊場景** | 惡意用戶嘗試繞過 Allowlist 或 DM Pairing 驗證 |

**失敗場景**：
1. 用戶 ID 偽造（Telegram 不會發生，但需驗證）
2. Session Key 碰撞
3. Tool Policy 繞過
4. 群組權限升級

**緩解措施**：
```typescript
// 集中化權限檢查 - 單一入口
class PermissionChecker {
  // 所有權限邏輯在此，不允許分散檢查
  async check(ctx: PermissionContext): Promise<PermissionResult> {
    // 1. 驗證用戶 ID 來源（必須從 Telegram 取得）
    if (!ctx.isFromTelegram) {
      return this.deny('invalid_source');
    }

    // 2. Allowlist 檢查（O(1) 查找）
    // 3. DM/Group Policy
    // 4. Tool Policy
    // 全部通過才允許
  }
}
```

**驗收標準**：
- [ ] 權限檢查 100% 測試覆蓋
- [ ] 無分散的權限邏輯
- [ ] 審計日誌記錄所有檢查

---

#### R2: API 金鑰洩漏
| 屬性 | 值 |
|------|-----|
| **優先級** | P0 |
| **可能性** | 中 |
| **影響** | 高 |
| **攻擊場景** | Telegram Token 或 Claude API Key 外洩 |

**失敗場景**：
1. 配置檔意外提交到 Git
2. 日誌記錄敏感資訊
3. 錯誤訊息包含 Token

**緩解措施**：
```yaml
# 配置驗證
config:
  telegram:
    token: ${TELEGRAM_BOT_TOKEN}  # 環境變數，不存檔

# .gitignore
config/local.yaml
.env
*.key
```

```typescript
// 日誌過濾
const logger = pino({
  redact: ['token', 'apiKey', 'password', 'secret'],
});
```

**驗收標準**：
- [ ] 所有敏感值透過環境變數
- [ ] 日誌自動 redact
- [ ] pre-commit hook 檢查敏感資訊

---

#### R3: Session 注入攻擊
| 屬性 | 值 |
|------|-----|
| **優先級** | P0 |
| **可能性** | 低 |
| **影響** | 高 |
| **攻擊場景** | 惡意用戶嘗試存取其他用戶的 Session |

**失敗場景**：
1. Session Key 可預測
2. Path Traversal（`../../../other-user/session.json`）
3. Session 劫持

**緩解措施**：
```typescript
// Session Key 生成 - 使用加密安全隨機
function generateSessionKey(userId: string, chatId: string): string {
  const data = `${userId}:${chatId}:${Date.now()}`;
  return crypto.createHash('sha256')
    .update(data + process.env.SESSION_SECRET)
    .digest('hex')
    .slice(0, 32);
}

// 路徑驗證
function getSessionPath(sessionKey: string): string {
  // 僅允許 hex 字符
  if (!/^[a-f0-9]{32}$/.test(sessionKey)) {
    throw new Error('Invalid session key');
  }
  return path.join(SESSION_DIR, `${sessionKey}.json`);
}
```

**驗收標準**：
- [ ] Session Key 不可預測（熵測試）
- [ ] 路徑驗證防止 Traversal
- [ ] Session 與 User ID 綁定驗證

---

### 2.2 技術風險（P1 優先）

#### R4: Claude Code API 變更
| 屬性 | 值 |
|------|-----|
| **優先級** | P1 |
| **可能性** | 中 |
| **影響** | 高 |
| **場景** | Claude Code CLI 或 Task API 介面變更 |

**失敗場景**：
1. CLI 參數變更
2. 輸出格式變更
3. Tool API 協議變更
4. 新版本行為差異

**緩解措施**：
```typescript
// Adapter Pattern - 隔離 API 變更
interface ClaudeAdapter {
  processMessage(ctx: MessageContext): AsyncGenerator<string>;
}

// 具體實現
class ClaudeCodeAdapter implements ClaudeAdapter {
  private version = '1.0.0';  // 鎖定版本

  async *processMessage(ctx: MessageContext) {
    // 實現細節
  }
}

// 未來可替換
class ClaudeApiAdapter implements ClaudeAdapter {
  // 直接使用 Claude API
}
```

**驗收標準**：
- [ ] Adapter 介面穩定
- [ ] 版本鎖定記錄
- [ ] Integration test 覆蓋

---

#### R5: 配置驗證失敗
| 屬性 | 值 |
|------|-----|
| **優先級** | P1 |
| **可能性** | 中 |
| **影響** | 中 |
| **場景** | 錯誤配置導致安全漏洞或功能異常 |

**失敗場景**：
1. Allowlist 為空但 dm_policy 不是 open
2. Tool deny list 配置錯誤
3. 配置類型錯誤

**緩解措施**：
```typescript
// Zod Schema 驗證
const SecurityConfigSchema = z.object({
  dm_policy: z.enum(['pairing', 'allowlist', 'open']),
  group_policy: z.enum(['disabled', 'mention_only', 'always_on']),
  allowlist: z.array(AllowlistEntrySchema).min(1, {
    message: 'Allowlist must have at least one entry when dm_policy is not "open"',
  }),
}).refine(
  (data) => data.dm_policy === 'open' || data.allowlist.length > 0,
  { message: 'Allowlist required when dm_policy is not "open"' }
);
```

**驗收標準**：
- [ ] 配置載入時完整驗證
- [ ] 有意義的錯誤訊息
- [ ] 啟動時配置檢查

---

### 2.3 營運風險

#### R6: 審計日誌缺失
| 屬性 | 值 |
|------|-----|
| **優先級** | P1 |
| **可能性** | 低 |
| **影響** | 高 |
| **場景** | 安全事件發生但無法追蹤 |

**緩解措施**：
```typescript
interface AuditEntry {
  timestamp: number;
  eventType: 'permission_check' | 'tool_invoke' | 'message' | 'error';
  sessionKey: string;
  userId: string;
  result: 'allowed' | 'denied' | 'error';
  details: Record<string, unknown>;
}

class AuditLogger {
  private stream: WriteStream;

  log(entry: AuditEntry): void {
    // 同步寫入，確保不丟失
    this.stream.write(JSON.stringify(entry) + '\n');
  }

  async flush(): Promise<void> {
    // 強制刷新
  }
}
```

**驗收標準**：
- [ ] 所有權限決策有日誌
- [ ] 日誌不丟失（sync 寫入）
- [ ] 可查詢歷史記錄

---

#### R7: DoS 攻擊
| 屬性 | 值 |
|------|-----|
| **優先級** | P1 |
| **可能性** | 中 |
| **影響** | 中 |
| **場景** | 惡意用戶透過大量請求耗盡資源 |

**緩解措施**：
```typescript
// 速率限制
const rateLimiter = new Map<string, { count: number; resetAt: number }>();

function checkRateLimit(userId: string): boolean {
  const now = Date.now();
  const limit = rateLimiter.get(userId);

  if (!limit || limit.resetAt < now) {
    rateLimiter.set(userId, { count: 1, resetAt: now + 60000 });
    return true;
  }

  if (limit.count >= 10) { // 每分鐘 10 條
    return false;
  }

  limit.count++;
  return true;
}
```

**驗收標準**：
- [ ] 每用戶速率限制
- [ ] 超限友善提示
- [ ] 可配置限制值

---

### 2.4 依賴風險

#### R8: 第三方依賴漏洞
| 屬性 | 值 |
|------|-----|
| **優先級** | P1 |
| **可能性** | 中 |
| **影響** | 變動 |
| **場景** | Grammy 或其他依賴有安全漏洞 |

**緩解措施**：
```json
// package.json
{
  "scripts": {
    "audit": "pnpm audit --audit-level=moderate",
    "audit:fix": "pnpm audit --fix"
  }
}
```

```yaml
# .github/workflows/security.yml
- name: Security Audit
  run: pnpm audit --audit-level=moderate

- name: Dependabot
  # 自動更新依賴
```

**驗收標準**：
- [ ] CI 自動 audit
- [ ] 依賴版本鎖定
- [ ] 定期更新計劃

---

### 2.5 整合風險

#### R9: Long Polling 斷線
| 屬性 | 值 |
|------|-----|
| **優先級** | P2 |
| **可能性** | 中 |
| **影響** | 中 |
| **場景** | 網路問題導致消息丟失 |

**緩解措施**：
```typescript
// Grammy 內建重試
const bot = new Bot(token, {
  client: {
    timeoutSeconds: 30,
    retryAfter: 5,
  },
});

// Offset 確認機制
bot.start({
  drop_pending_updates: false,
  onStart: (info) => {
    logger.info(`Bot started: ${info.username}`);
  },
});
```

**驗收標準**：
- [ ] 斷線自動重連
- [ ] Offset 正確追蹤
- [ ] 不丟失已確認消息

---

#### R10: Session 競態條件
| 屬性 | 值 |
|------|-----|
| **優先級** | P2 |
| **可能性** | 低 |
| **影響** | 中 |
| **場景** | 同一用戶快速發送多條消息導致 Session 衝突 |

**緩解措施**：
```typescript
import { lock } from 'proper-lockfile';

async function withSessionLock<T>(
  sessionKey: string,
  fn: () => Promise<T>
): Promise<T> {
  const release = await lock(getSessionPath(sessionKey), {
    stale: 10000, // 10 秒超時
    retries: 3,
  });

  try {
    return await fn();
  } finally {
    await release();
  }
}
```

**驗收標準**：
- [ ] 並發寫入測試
- [ ] 鎖超時處理
- [ ] 不死鎖

---

## 3. 風險應對計劃

### 3.1 開發階段

| 階段 | 必須完成的風險緩解 |
|------|-------------------|
| Week 1 | R2（API 金鑰）、R5（配置驗證） |
| Week 2 | R1（權限）、R3（Session）、R6（審計） |
| Week 3 | R4（API 變更）、R7（DoS） |
| Week 4 | R8（依賴）、R9-R10（整合） |

### 3.2 監控指標

```typescript
interface RiskMetrics {
  // 安全指標
  permissionDenials: Counter;        // 權限拒絕次數
  auditLogSize: Gauge;               // 審計日誌大小

  // 技術指標
  pollingReconnects: Counter;        // 重連次數
  sessionLockWaits: Histogram;       // 鎖等待時間
  claudeApiErrors: Counter;          // API 錯誤次數

  // 營運指標
  rateLimitHits: Counter;            // 速率限制觸發
  activeUsers: Gauge;                // 活躍用戶數
}
```

---

## 4. 建議

### 4.1 必須（P0）

1. **權限系統必須集中化**：不允許分散的權限檢查
2. **敏感資訊必須環境變數**：配置檔禁止硬編碼
3. **Session 必須防注入**：路徑驗證 + 加密 Key

### 4.2 應該（P1）

1. **Adapter 模式隔離 API**：為 Claude Code 變更準備
2. **配置載入時驗證**：不允許無效配置啟動
3. **審計日誌同步寫入**：確保不丟失

### 4.3 可以（P2-P3）

1. **速率限制可選**：初期可簡單實現
2. **依賴審計 CI**：建議但非必須

---

**報告生成時間**: 2026-01-27
**視角**: risk-analyst
**識別風險數**: 23
**P0/P1 風險數**: 8
