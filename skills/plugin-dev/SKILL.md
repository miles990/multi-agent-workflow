---
name: plugin-dev
version: 1.0.0
description: Plugin 開發完整工作流 - 同步、監控、驗證、發布
triggers: [plugin-dev, plugin-workflow, plugin-sync, plugin-release]
context: shared
agent: general-purpose
allowed-tools: [Read, Write, Bash, Grep, Glob]
model: haiku
---

# plugin-dev Skill

> Plugin 開發完整工作流 - 同步、監控、驗證、發布

## 命令總覽

| 命令 | 功能 | 用途 |
|------|------|------|
| `/plugin-dev sync` | 同步到快取 | 將源碼同步到 Claude Code 快取 |
| `/plugin-dev watch` | 監控模式 | 熱載入，檔案變更自動同步 |
| `/plugin-dev validate` | 驗證結構 | 檢查 Plugin 結構和版本一致性 |
| `/plugin-dev status` | 查看狀態 | 顯示快取和版本資訊 |
| `/plugin-dev version` | 版本管理 | 查看或升級版本 |
| `/plugin-dev release` | 發布流程 | 完整的發布自動化 |

## 快速開始

```bash
# 1. 同步到快取
/plugin-dev sync

# 2. 驗證結構
/plugin-dev validate

# 3. 查看狀態
/plugin-dev status

# 4. 啟動開發模式（熱載入）
/plugin-dev watch

# 5. 發布新版本
/plugin-dev release patch
```

## 命令詳情

### /plugin-dev sync

同步源碼到 Claude Code 快取。

```bash
/plugin-dev sync [--force] [--dry-run] [--verbose]
```

**參數**：
- `--force`：強制全量同步（忽略快取映射）
- `--dry-run`：預覽變更，不實際同步
- `--verbose`：顯示詳細輸出

**執行**：
```
Bash: python -m cli.plugin.dev sync [options]
```

**範例**：
```bash
/plugin-dev sync              # 增量同步
/plugin-dev sync --force      # 全量同步
/plugin-dev sync --dry-run    # 預覽變更
```

### /plugin-dev watch

監控模式，檔案變更自動同步。

```bash
/plugin-dev watch [--debounce N] [--no-initial] [--background]
```

**參數**：
- `--debounce N`：防抖動時間（毫秒，預設 500）
- `--no-initial`：不執行初始同步
- `--background`：背景執行

**執行**：
```
Bash: python -m cli.plugin.dev watch [options]
```

**範例**：
```bash
/plugin-dev watch                    # 前台監控
/plugin-dev watch --background       # 背景監控
/plugin-dev watch --debounce 1000    # 1 秒防抖動
```

### /plugin-dev validate

驗證 Plugin 結構和版本一致性。

```bash
/plugin-dev validate [--strict] [--fix]
```

**參數**：
- `--strict`：嚴格模式（警告也視為錯誤）
- `--fix`：自動修復可修復的問題

**執行**：
```
Bash: python -m cli.plugin.release validate [options]
```

**檢查項目**：
- plugin.json 存在且有效
- skills/ 目錄存在
- 至少一個 SKILL.md
- 版本一致性（plugin.json, marketplace.json）

### /plugin-dev status

查看快取和版本狀態。

```bash
/plugin-dev status [--json]
```

**參數**：
- `--json`：JSON 格式輸出

**執行**：
```
Bash: python -m cli.plugin.dev status [options]
```

**輸出範例**：
```
Plugin: multi-agent-workflow
Version: 2.4.0
Cache: ~/.claude/plugins/cache/...
Cache Status: Valid (synced 5 min ago)
Skills: 8 loaded
Last Release: v2.4.0 (2026-01-30)
```

### /plugin-dev version

版本管理。

```bash
/plugin-dev version [command] [--dry-run]

Commands:
  (無)          顯示當前版本
  bump LEVEL    升級版本（patch/minor/major）
  check         檢查版本一致性
```

**執行**：
```
Bash: python -m cli.plugin.version [command] [options]
```

**範例**：
```bash
/plugin-dev version             # 顯示 2.4.0
/plugin-dev version bump patch  # 升級到 2.4.1
/plugin-dev version check       # 檢查一致性
```

### /plugin-dev release

完整的發布自動化。

```bash
/plugin-dev release [LEVEL] [--dry-run] [--resume] [--yes]
```

**參數**：
- `LEVEL`：版本級別 patch/minor/major（預設 patch）
- `--dry-run`：預覽完整發布流程
- `--resume`：從中斷點恢復
- `--yes`：跳過確認提示

**執行**：
```
Bash: python -m cli.plugin.release release [LEVEL] [options]
```

**發布流程**：
```
1. VALIDATE    驗證 Plugin 結構
2. TEST        執行測試套件
3. CHECK_GIT   檢查 Git 狀態
4. BUMP        升級版本號
5. CHANGELOG   生成變更日誌
6. COMMIT      Git commit
7. TAG         建立 Git tag
8. PUSH        推送到遠端
9. COMPLETE    完成
```

**範例**：
```bash
/plugin-dev release patch              # 發布 patch 版本
/plugin-dev release minor --dry-run    # 預覽 minor 發布
/plugin-dev release --resume           # 恢復中斷的發布
```

## 執行流程

### 命令路由

當用戶輸入 `/plugin-dev <command>` 時：

1. **解析命令**：識別 command（sync/watch/validate/status/version/release）
2. **解析參數**：識別選項（--force/--dry-run/--verbose 等）
3. **執行 Python CLI**：調用對應的 Python 模組
4. **格式化輸出**：將結果以友善格式顯示

### 錯誤處理

**成功輸出**：
```
✓ 同步完成
  新增: 3 個檔案
  修改: 2 個檔案
  耗時: 1.2s
```

**警告輸出**：
```
⚠ 發現潛在問題
  - plugin.json 缺少 author 欄位
  - marketplace.json 版本與 plugin.json 不一致

建議: 執行 /plugin-dev validate --fix 自動修復
```

**錯誤輸出**：
```
✗ 同步失敗
  錯誤: 快取目錄不可寫入
  路徑: ~/.claude/plugins/cache/...

修復建議:
  1. 檢查目錄權限: ls -la ~/.claude/plugins/
  2. 嘗試強制同步: /plugin-dev sync --force
  3. 查看詳細日誌: /plugin-dev status --verbose
```

## 配置

### 快取路徑

環境變數覆寫：
```bash
export PLUGIN_CACHE_BASE=~/.claude/plugins/cache
```

配置檔案：`shared/plugin/config.yaml`

### Watch 模式

```yaml
# .plugin-dev/watch.config.json
{
  "debounce_ms": 500,
  "exclude_patterns": [
    "__pycache__/",
    "*.pyc",
    ".git/",
    ".plugin-dev/"
  ]
}
```

## Fallback 腳本

當 Python CLI 不可用時，可使用 Shell 腳本：

```bash
# 同步
./scripts/plugin/sync-to-cache.sh

# 監控
./scripts/plugin/dev-watch.sh

# 驗證
./scripts/plugin/validate-plugin.sh

# 發布
./scripts/plugin/publish.sh patch
```

## 相關資源

- [Python CLI 模組](../../cli/plugin/)
- [Shell 腳本](../../scripts/plugin/)
- [配置檔案](../../shared/plugin/)
- [開發經驗](../../CLAUDE.md#plugin-開發工作流)
