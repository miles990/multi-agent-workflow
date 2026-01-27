# Clawdbot MVP 風險緩解計劃

**版本**: 1.0
**日期**: 2026-01-27

---

## 1. 風險總覽

### 1.1 風險分類

| 類別 | P0 | P1 | P2 | P3 | 總計 |
|------|-----|-----|-----|-----|------|
| 安全風險 | 3 | 1 | 1 | 0 | 5 |
| 技術風險 | 0 | 2 | 3 | 2 | 7 |
| 營運風險 | 0 | 2 | 1 | 1 | 4 |
| 依賴風險 | 0 | 1 | 1 | 1 | 3 |
| 整合風險 | 0 | 0 | 2 | 2 | 4 |
| **總計** | **3** | **6** | **8** | **6** | **23** |

### 1.2 風險矩陣

```
影響
 高 │ R1,R2,R3    R4
    │ (P0)        (P1)
 中 │ R5,R6       R9,R10       R11-R15
    │ (P1)        (P2)         (P3)
 低 │             R7,R8        R16-R23
    │             (P2)         (P3)
    └────────────────────────────────
      低          中           高    可能性
```

---

## 2. P0 風險（必須阻止）

### R1: 權限繞過攻擊

| 屬性 | 值 |
|------|-----|
| 影響 | 高 |
| 可能性 | 中 |
| 優先級 | P0 |

**風險描述**:
惡意用戶嘗試繞過 Allowlist 或 DM Pairing 驗證，獲得未授權存取。

**攻擊向量**:
1. Session Key 預測/碰撞
2. 用戶 ID 偽造
3. Tool Policy 繞過
4. 群組權限升級

**緩解措施**:

| 措施 | 實施週次 | 負責人 |
|------|---------|--------|
| 集中化權限檢查 | W2 | 開發者 |
| Session Key 使用加密隨機 | W2 | 開發者 |
| 100% 權限測試覆蓋 | W2 | 開發者 |
| 審計日誌記錄所有決策 | W2 | 開發者 |

**驗證方法**:
```bash
# 滲透測試腳本
pnpm test:security
# 應包含:
# - 非 allowlist 用戶測試
# - Session Key 碰撞測試
# - Tool Policy 繞過測試
```

**殘餘風險**: 低（實施後）

---

### R2: API 金鑰洩漏

| 屬性 | 值 |
|------|-----|
| 影響 | 高 |
| 可能性 | 中 |
| 優先級 | P0 |

**風險描述**:
Telegram Token 或 Claude API Key 外洩導致帳號被濫用。

**攻擊向量**:
1. 配置檔提交到 Git
2. 日誌記錄敏感資訊
3. 錯誤訊息包含 Token
4. 環境變數洩漏

**緩解措施**:

| 措施 | 實施週次 | 負責人 |
|------|---------|--------|
| 環境變數存儲敏感值 | W1 | 開發者 |
| pino redact 配置 | W1 | 開發者 |
| .gitignore 完整配置 | W1 | 開發者 |
| pre-commit hook 檢查 | W1 | 開發者 |
| 錯誤訊息過濾 | W2 | 開發者 |

**驗證方法**:
```bash
# 敏感資訊檢查
git secrets --scan
grep -r "token" . --include="*.ts" | grep -v "process.env"
```

**殘餘風險**: 低（實施後）

---

### R3: Session 注入攻擊

| 屬性 | 值 |
|------|-----|
| 影響 | 高 |
| 可能性 | 低 |
| 優先級 | P0 |

**風險描述**:
惡意用戶嘗試存取其他用戶的 Session 資料。

**攻擊向量**:
1. Session Key 可預測
2. Path Traversal
3. Session 劫持
4. 檔案系統注入

**緩解措施**:

| 措施 | 實施週次 | 負責人 |
|------|---------|--------|
| 加密隨機 Session Key | W2 | 開發者 |
| 路徑驗證（白名單字符） | W2 | 開發者 |
| Session-User 綁定驗證 | W2 | 開發者 |
| 檔案權限限制 (600) | W6 | 開發者 |

**驗證方法**:
```typescript
// Session Key 熵測試
const keys = Array(1000).fill(0).map(() => generateSessionKey('test', 'test'));
const uniqueKeys = new Set(keys);
expect(uniqueKeys.size).toBe(1000);

// Path Traversal 測試
expect(() => getSessionPath('../../../etc/passwd')).toThrow();
```

**殘餘風險**: 低（實施後）

---

## 3. P1 風險（高度重要）

### R4: Claude Code API 變更

| 屬性 | 值 |
|------|-----|
| 影響 | 高 |
| 可能性 | 中 |
| 優先級 | P1 |

**緩解措施**:

| 措施 | 說明 |
|------|------|
| Adapter Pattern | 隔離 API 變更影響 |
| 版本鎖定 | 鎖定 Claude Code CLI 版本 |
| 整合測試 | 每次 CI 測試 Claude 整合 |
| 回退策略 | 準備直接 API 呼叫作為備用 |

---

### R5: 配置驗證失敗

| 屬性 | 值 |
|------|-----|
| 影響 | 中 |
| 可能性 | 中 |
| 優先級 | P1 |

**緩解措施**:

```typescript
// Zod 跨欄位驗證
const ConfigSchema = z.object({
  security: z.object({
    dm_policy: z.enum(['pairing', 'allowlist', 'open']),
    allowlist: z.array(AllowlistEntry),
  }).refine(
    (data) => data.dm_policy === 'open' || data.allowlist.length > 0,
    { message: 'Allowlist required when dm_policy is not "open"' }
  ),
});

// CLI 驗證命令
clawdbot config check
```

---

### R6: 審計日誌缺失

| 屬性 | 值 |
|------|-----|
| 影響 | 高 |
| 可能性 | 低 |
| 優先級 | P1 |

**緩解措施**:

| 措施 | 說明 |
|------|------|
| 同步寫入 | 確保日誌不丟失 |
| 權限決策必記錄 | 所有 allow/deny 有日誌 |
| 日誌備份 | 定期備份到外部存儲 |
| 監控告警 | 日誌寫入失敗告警 |

---

### R7: DoS 攻擊

| 屬性 | 值 |
|------|-----|
| 影響 | 中 |
| 可能性 | 中 |
| 優先級 | P1 |

**緩解措施**:

```typescript
// 速率限制
const RATE_LIMIT = 10; // 每分鐘
const rateLimiter = new Map<string, { count: number; resetAt: number }>();

function checkRateLimit(userId: string): boolean {
  const now = Date.now();
  const limit = rateLimiter.get(userId);

  if (!limit || limit.resetAt < now) {
    rateLimiter.set(userId, { count: 1, resetAt: now + 60000 });
    return true;
  }

  if (limit.count >= RATE_LIMIT) {
    return false;
  }

  limit.count++;
  return true;
}
```

---

### R8: 第三方依賴漏洞

| 屬性 | 值 |
|------|-----|
| 影響 | 變動 |
| 可能性 | 中 |
| 優先級 | P1 |

**緩解措施**:

| 措施 | 說明 |
|------|------|
| pnpm audit | CI 自動審計 |
| Dependabot | 自動更新建議 |
| 版本鎖定 | pnpm-lock.yaml |
| 定期更新 | 每月依賴更新 |

---

## 4. P2 風險（中度重要）

### R9-R15 摘要

| ID | 風險 | 緩解 |
|-----|------|------|
| R9 | Long Polling 斷線 | Grammy 內建重試 + offset 確認 |
| R10 | Session 競態 | 檔案鎖定 (proper-lockfile) |
| R11 | 記憶體洩漏 | 定期清理 + 監控 |
| R12 | 回覆延遲 | 超時處理 + 用戶提示 |
| R13 | 配置熱載入 | 不支援，需重啟 |
| R14 | 日誌膨脹 | Retention + 輪轉 |
| R15 | 測試覆蓋不足 | CI 覆蓋率門檻 |

---

## 5. 監控與告警

### 5.1 監控指標

```typescript
interface RiskMetrics {
  // 安全指標
  permission_denied_count: Counter;
  permission_denied_by_reason: Counter;
  session_key_collisions: Counter;

  // 營運指標
  rate_limit_hits: Counter;
  audit_log_errors: Counter;

  // 技術指標
  claude_api_errors: Counter;
  response_latency_p95: Histogram;
  session_lock_waits: Histogram;
}
```

### 5.2 告警規則

| 指標 | 閾值 | 告警級別 |
|------|------|---------|
| permission_denied_count | > 100/min | WARNING |
| session_key_collisions | > 0 | CRITICAL |
| claude_api_errors | > 10/min | WARNING |
| audit_log_errors | > 0 | CRITICAL |

---

## 6. 應急計劃

### 6.1 安全事件應急

```
發現安全事件
     ↓
1. 立即停止 Bot (clawdbot stop)
     ↓
2. 保留審計日誌
     ↓
3. 分析攻擊向量
     ↓
4. 修復漏洞
     ↓
5. 重新部署
     ↓
6. 通知受影響用戶
```

### 6.2 服務中斷應急

```
發現服務中斷
     ↓
1. 檢查 Long Polling 狀態
     ↓
2. 檢查 Claude Code 可用性
     ↓
3. 查看錯誤日誌
     ↓
4. 重啟服務
     ↓
5. 如持續中斷，啟用備用模式
```

### 6.3 備用模式

| 場景 | 備用方案 |
|------|---------|
| Claude Code 不可用 | 返回友善錯誤訊息 |
| Telegram API 限流 | 降低輪詢頻率 |
| 存儲失敗 | 記憶體暫存，稍後重試 |

---

## 7. 風險審查週期

| 審查類型 | 頻率 | 內容 |
|---------|------|------|
| 日常監控 | 每日 | 檢查監控指標 |
| 週報 | 每週 | 風險狀態更新 |
| 月度審查 | 每月 | 完整風險重評估 |
| 依賴審計 | 每月 | pnpm audit |

---

## 8. 緩解進度追蹤

### 8.1 P0 緩解狀態

| 風險 | 措施 | 狀態 | 預計完成 |
|------|------|------|---------|
| R1 權限繞過 | 集中化檢查 | 待開始 | W2 |
| R1 權限繞過 | 100% 測試 | 待開始 | W2 |
| R2 金鑰洩漏 | 環境變數 | 待開始 | W1 |
| R2 金鑰洩漏 | 日誌 redact | 待開始 | W1 |
| R3 Session 注入 | 加密隨機 Key | 待開始 | W2 |
| R3 Session 注入 | 路徑驗證 | 待開始 | W2 |

### 8.2 P1 緩解狀態

| 風險 | 措施 | 狀態 | 預計完成 |
|------|------|------|---------|
| R4 API 變更 | Adapter Pattern | 待開始 | W3 |
| R5 配置驗證 | Zod 驗證 | 待開始 | W1 |
| R6 審計缺失 | 同步寫入 | 待開始 | W2 |
| R7 DoS | 速率限制 | 待開始 | W2 |
| R8 依賴漏洞 | CI audit | 待開始 | W1 |

---

**風險緩解計劃完成時間**: 2026-01-27
**下次審查日期**: 開發啟動後每週
