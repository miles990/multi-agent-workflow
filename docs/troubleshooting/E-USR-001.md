# E-USR-001: 參數錯誤

## 錯誤資訊

| 欄位 | 值 |
|------|-----|
| 錯誤碼 | E-USR-001 |
| 名稱 | 參數錯誤 |
| 嚴重度 | LOW |
| 類別 | User 輸入 |

## 說明

當命令參數格式不正確或值無效時，會觸發此錯誤。這通常是由於輸入錯誤或對命令用法的誤解造成的。

## 常見場景

### 場景 1：Flag 格式錯誤

**狀況**：使用了錯誤的 flag 格式。

**範例**：
```bash
# 錯誤
/multi-orchestrate -perspectives 4 "任務"

# 正確
/multi-orchestrate --perspectives 4 "任務"
```

**解決方案**：使用正確的 `--` 前綴。

### 場景 2：值類型錯誤

**狀況**：參數值的類型不正確。

**範例**：
```bash
# 錯誤
/multi-orchestrate --perspectives abc "任務"

# 正確
/multi-orchestrate --perspectives 4 "任務"
```

**解決方案**：提供正確類型的值。

### 場景 3：缺少引號

**狀況**：包含空格的參數未加引號。

**範例**：
```bash
# 錯誤
/multi-orchestrate 新增用戶認證功能

# 正確
/multi-orchestrate "新增用戶認證功能"
```

**解決方案**：用引號包圍含空格的參數。

## 快速修復

### 方法 1：查看幫助

```bash
/multi-orchestrate --help
```

### 方法 2：使用預設值

省略可選參數，使用預設值：

```bash
# 使用所有預設值
/multi-orchestrate "任務描述"
```

### 方法 3：參考範例

參考文檔中的使用範例：

```bash
# 基本用法
/multi-orchestrate "新增用戶認證功能"

# 指定起點
/multi-orchestrate --from-plan user-auth

# 部分執行
/multi-orchestrate --stop-at implement "任務"
```

## 參數參考

### orchestrate 命令

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `--perspectives` | 數字 | 4 | 視角數量 |
| `--from-research` | 字串 | - | 從研究 ID 開始 |
| `--from-plan` | 字串 | - | 從計劃 ID 開始 |
| `--start-at` | 字串 | auto | 起始階段 |
| `--stop-at` | 字串 | - | 停止階段 |
| `--skip` | 字串 | - | 跳過階段 |
| `--worktree` | 布林 | auto | 使用 worktree |
| `--no-worktree` | 布林 | false | 禁用 worktree |
| `--no-memory` | 布林 | false | 不使用 Memory |
| `--resume` | 字串 | - | 恢復工作流 ID |
| `--dry-run` | 布林 | false | 演練模式 |

### 階段名稱

有效的階段名稱：
- `research`
- `plan`
- `implement`
- `review`
- `verify`

### 常見錯誤

| 錯誤輸入 | 正確輸入 | 說明 |
|----------|----------|------|
| `--perspective` | `--perspectives` | 複數形式 |
| `--start` | `--start-at` | 完整名稱 |
| `--from plan` | `--from-plan` | 使用連字號 |
| `IMPLEMENT` | `implement` | 小寫 |

## 深入分析

### 參數解析邏輯

1. 解析 flags（`--xxx`）
2. 解析位置參數（任務描述）
3. 驗證值類型和範圍
4. 應用預設值

### 常見錯誤訊息

```
E-USR-001: 參數錯誤
詳情: 無效的視角數量 'abc'，需要正整數

E-USR-001: 參數錯誤
詳情: 未知的階段名稱 'imple'，有效值: research, plan, implement, review, verify

E-USR-001: 參數錯誤
詳情: 缺少任務描述，請提供要執行的任務
```

## 預防措施

### 1. 使用 Tab 補全

如果環境支援，使用 Tab 補全避免輸入錯誤。

### 2. 複製貼上

從文檔複製正確的命令格式。

### 3. 使用演練模式

先用演練模式確認命令正確：

```bash
/multi-orchestrate --dry-run "任務描述"
```

### 4. 查看最近使用

參考最近成功的命令。

## 相關錯誤

- [E-USR-002](./E-USR-002.md) - 缺少輸入
- [E-USR-003](./E-USR-003.md) - 無效選項

## 參考資料

- [錯誤碼定義](../../shared/errors/error-codes.md)
- [orchestrate SKILL](../../skills/orchestrate/SKILL.md)
- [快速開始](../../skills/orchestrate/00-quickstart/)
