# /plugin-dev watch

> 監控模式 - 檔案變更自動同步

## 格式

```bash
/plugin-dev watch [--debounce N] [--no-initial] [--background]
```

## 參數

| 參數 | 說明 |
|------|------|
| `--debounce N` | 防抖動時間（毫秒，預設 500） |
| `--no-initial` | 不執行初始同步 |
| `--background` | 背景執行 |

## 實作路徑

```
Skill → Bash: python -m cli.plugin.dev watch [options]
     → DevCommands.watch()
     → fswatch / inotifywait / polling
```

## 監控工具

按優先順序選擇：

1. **fswatch** (macOS) - 最佳效能
2. **inotifywait** (Linux) - 原生支援
3. **polling** (通用) - 備選方案

## 範例

### 前台監控

```bash
/plugin-dev watch
```

輸出：
```
┌─ Plugin Development Mode ─────────────────────┐
│                                               │
│  專案: multi-agent-workflow                   │
│  版本: 2.4.0                                  │
│                                               │
│  狀態: 監控中 (fswatch)                       │
│  防抖動: 500ms                                │
│                                               │
├───────────────────────────────────────────────┤
│  最近同步:                                    │
│  14:30:05  ✓ 2 個檔案已同步 (120ms)          │
│            • skills/plugin-dev/SKILL.md      │
│            • shared/plugin/config.yaml       │
│                                               │
├───────────────────────────────────────────────┤
│  按 Ctrl+C 停止監控                           │
└───────────────────────────────────────────────┘
```

### 背景監控

```bash
/plugin-dev watch --background
```

輸出：
```
✓ 監控已在背景啟動
  PID: 12345
  日誌: .plugin-dev/logs/watch.log

停止監控: kill 12345
```

### 自訂防抖動

```bash
/plugin-dev watch --debounce 1000
```

## 排除規則

預設排除：
- `__pycache__/`
- `*.pyc`
- `.git/`
- `.plugin-dev/`
- `node_modules/`

自訂排除：編輯 `.plugin-dev/watch.config.json`

## 錯誤處理

### 監控工具不可用

```
⚠ 未找到監控工具

建議安裝:
  macOS: brew install fswatch
  Linux: apt install inotify-tools

將使用 polling 模式（效能較低）
```

### 背景程序已存在

```
⚠ 監控程序已在執行
  PID: 12345

選項:
  1. 停止現有程序: kill 12345
  2. 查看日誌: tail -f .plugin-dev/logs/watch.log
```

## 相關命令

- `/plugin-dev sync` - 手動同步
- `/plugin-dev status` - 查看監控狀態
