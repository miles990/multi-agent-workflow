# /plugin-dev status

> 查看快取和版本狀態

## 格式

```bash
/plugin-dev status [--json]
```

## 參數

| 參數 | 說明 |
|------|------|
| `--json` | JSON 格式輸出 |

## 實作路徑

```
Skill → Bash: python -m cli.plugin.dev status [options]
     → CacheManager.status()
     → VersionManager.get_current_version()
```

## 範例

### 基本狀態

```bash
/plugin-dev status
```

輸出：
```
📦 Plugin 狀態

  名稱: multi-agent-workflow
  版本: 2.4.0
  作者: user

快取狀態:
  路徑: ~/.claude/plugins/cache/multi-agent-workflow/2.4.0/
  狀態: ✓ 有效
  最後同步: 5 分鐘前
  檔案數: 156
  大小: 2.3 MB

Skills:
  ✓ orchestrate (v3.4.0)
  ✓ research (v3.2.0)
  ✓ plan (v3.2.0)
  ✓ tasks (v3.1.0)
  ✓ implement (v3.1.0)
  ✓ review (v3.1.0)
  ✓ verify (v3.1.0)
  ✓ status (v2.0.0)
  ✓ plugin-dev (v1.0.0)

監控狀態:
  狀態: ○ 未執行

最近發布:
  v2.4.0  2026-01-30  feat: 新增 plugin-dev Skill
  v2.3.2  2026-01-25  fix: git_lib 整合修復
  v2.3.1  2026-01-20  fix: 版本一致性檢查
```

### JSON 輸出

```bash
/plugin-dev status --json
```

輸出：
```json
{
  "plugin": {
    "name": "multi-agent-workflow",
    "version": "2.4.0",
    "author": "user"
  },
  "cache": {
    "path": "~/.claude/plugins/cache/multi-agent-workflow/2.4.0/",
    "valid": true,
    "last_sync": "2026-02-01T14:30:00",
    "file_count": 156,
    "size_bytes": 2411724
  },
  "skills": [
    {"name": "orchestrate", "version": "3.4.0"},
    {"name": "research", "version": "3.2.0"}
  ],
  "watch": {
    "running": false,
    "pid": null
  },
  "releases": [
    {"version": "2.4.0", "date": "2026-01-30", "message": "feat: 新增 plugin-dev Skill"}
  ]
}
```

## 狀態說明

### 快取狀態

| 狀態 | 說明 |
|------|------|
| ✓ 有效 | 快取存在且與源碼同步 |
| ⚠ 過期 | 快取存在但需要同步 |
| ✗ 無效 | 快取不存在或損壞 |

### 監控狀態

| 狀態 | 說明 |
|------|------|
| ● 執行中 | watch 正在執行 |
| ○ 未執行 | watch 未啟動 |

## 錯誤處理

### 快取不存在

```
📦 Plugin 狀態

  名稱: multi-agent-workflow
  版本: 2.4.0

快取狀態:
  狀態: ✗ 不存在

建議: 執行 /plugin-dev sync 建立快取
```

### 無法讀取 plugin.json

```
✗ 無法讀取狀態

錯誤: plugin.json 不存在或無法讀取

修復建議:
  1. 確認在正確的專案目錄
  2. 檢查 plugin.json 是否存在
```

## 相關命令

- `/plugin-dev sync` - 同步到快取
- `/plugin-dev validate` - 驗證結構
- `/plugin-dev version` - 版本管理
