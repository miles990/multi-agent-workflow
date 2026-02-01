# /plugin-dev sync

> 同步源碼到 Claude Code 快取

## 格式

```bash
/plugin-dev sync [--force] [--dry-run] [--verbose]
```

## 參數

| 參數 | 簡寫 | 說明 |
|------|------|------|
| `--force` | `-f` | 強制全量同步（忽略快取映射） |
| `--dry-run` | `-n` | 預覽變更，不實際同步 |
| `--verbose` | `-v` | 顯示詳細輸出 |

## 實作路徑

```
Skill → Bash: python -m cli.plugin.dev sync [options]
     → DevCommands.sync()
     → CacheManager
```

## 同步策略

### 增量同步（預設）

使用 hash-based 增量同步：

1. 讀取 `.plugin-dev/cache-map.json`
2. 計算源檔案 hash
3. 比對變更（新增/修改/刪除）
4. 只同步變更的檔案
5. 更新 cache-map

### 全量同步（--force）

忽略快取映射，重新同步所有檔案。

## 範例

### 基本同步

```bash
/plugin-dev sync
```

輸出：
```
✓ 同步完成
  新增: 3 個檔案
  修改: 2 個檔案
  刪除: 0 個檔案
  耗時: 120ms
```

### 預覽變更

```bash
/plugin-dev sync --dry-run
```

輸出：
```
預覽變更（不實際同步）:
  + skills/plugin-dev/SKILL.md
  + skills/plugin-dev/00-quickstart/_base/usage.md
  ~ shared/plugin/config.yaml
```

### 強制全量同步

```bash
/plugin-dev sync --force
```

## 錯誤處理

### 快取目錄不存在

```
✗ 同步失敗
  錯誤: 快取目錄不存在
  路徑: ~/.claude/plugins/cache/multi-agent-workflow/

修復建議:
  1. 確認 Claude Code 已正確安裝
  2. 檢查 PLUGIN_CACHE_BASE 環境變數
  3. 手動建立目錄後重試
```

### 權限問題

```
✗ 同步失敗
  錯誤: 快取目錄不可寫入

修復建議:
  1. 檢查目錄權限: ls -la ~/.claude/plugins/
  2. 修正權限: chmod 755 ~/.claude/plugins/cache/
```

## 相關命令

- `/plugin-dev status` - 查看同步狀態
- `/plugin-dev watch` - 自動同步模式
- `/plugin-dev validate` - 驗證結構
