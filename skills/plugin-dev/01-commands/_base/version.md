# /plugin-dev version

> 版本管理

## 格式

```bash
/plugin-dev version [command] [--dry-run]

Commands:
  (無)          顯示當前版本
  bump LEVEL    升級版本（patch/minor/major）
  check         檢查版本一致性
```

## 參數

| 參數 | 說明 |
|------|------|
| `--dry-run` | 預覽變更，不實際修改 |

## 實作路徑

```
Skill → Bash: python -m cli.plugin.version [command] [options]
     → VersionManager
```

## 版本級別

| 級別 | 說明 | 範例 |
|------|------|------|
| `patch` | Bug 修復、小改進 | 2.4.0 → 2.4.1 |
| `minor` | 新功能、向後相容 | 2.4.0 → 2.5.0 |
| `major` | 破壞性變更 | 2.4.0 → 3.0.0 |

## 範例

### 顯示版本

```bash
/plugin-dev version
```

輸出：
```
multi-agent-workflow v2.4.0
```

### 升級版本

```bash
/plugin-dev version bump patch
```

輸出：
```
✓ 版本已升級

  舊版本: 2.4.0
  新版本: 2.4.1

已更新檔案:
  ✓ plugin.json
  ✓ marketplace.json
  ✓ CLAUDE.md

請執行 /plugin-dev release 完成發布
```

### 預覽升級

```bash
/plugin-dev version bump minor --dry-run
```

輸出：
```
預覽版本升級（不實際修改）:

  當前版本: 2.4.0
  新版本: 2.5.0

將更新:
  • plugin.json
  • marketplace.json
  • CLAUDE.md
```

### 檢查一致性

```bash
/plugin-dev version check
```

輸出（一致）：
```
✓ 版本一致

所有檔案版本: 2.4.0
  ✓ plugin.json
  ✓ marketplace.json
  ✓ CLAUDE.md
```

輸出（不一致）：
```
⚠ 版本不一致

  plugin.json:      2.4.0
  marketplace.json: 2.3.0  ← 不一致
  CLAUDE.md:        2.4.0

建議: 執行 /plugin-dev validate --fix 自動修復
```

## 版本檔案

版本資訊存儲在以下檔案：

| 檔案 | 位置 |
|------|------|
| plugin.json | `version` 欄位 |
| marketplace.json | `plugins[0].version` 欄位 |
| CLAUDE.md | 標題中的版本號 |

## 錯誤處理

### 無效的版本級別

```
✗ 無效的版本級別

錯誤: 'major2' 不是有效的版本級別

有效選項: patch, minor, major
```

### 版本格式錯誤

```
✗ 版本格式錯誤

錯誤: '2.4' 不是有效的語義化版本

正確格式: MAJOR.MINOR.PATCH (如 2.4.0)
```

## 相關命令

- `/plugin-dev validate` - 驗證結構
- `/plugin-dev release` - 完整發布流程
