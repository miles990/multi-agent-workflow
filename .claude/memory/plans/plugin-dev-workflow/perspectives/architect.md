# 系統架構師報告

> plugin-dev Skill 組件設計與技術架構

**視角**：系統架構師
**日期**：2026-02-01
**階段**：PLAN

## 核心設計

### 架構層次

```
┌─────────────────────────────────────────────────────┐
│                  Skill Layer                         │
│  /plugin-dev [command] [options]                    │
│  skills/plugin-dev/SKILL.md                         │
└────────────────────┬────────────────────────────────┘
                     │ 調用
                     ▼
┌─────────────────────────────────────────────────────┐
│               Python CLI Layer                       │
│  cli/plugin/                                        │
│  ├── cache.py      (CacheManager)                   │
│  ├── version.py    (VersionManager)                 │
│  ├── dev.py        (DevCommands)                    │
│  └── release.py    (ReleaseCommands)                │
└────────────────────┬────────────────────────────────┘
                     │ 使用
                     ▼
┌─────────────────────────────────────────────────────┐
│              Shared Modules Layer                    │
│  ├── scripts/git_lib/  (Git 操作統一)               │
│  └── shared/plugin/    (配置管理)                   │
└─────────────────────────────────────────────────────┘
```

### 工具型 Skill 定位

**不採用 MAP-REDUCE 框架**：
- Plugin 開發是單一領域操作
- 無需多視角並行分析
- 保持簡單性優先

**與工作流型 Skill 對比**：

| 特性 | 工作流型（research/plan） | 工具型（plugin-dev） |
|------|-------------------------|---------------------|
| 並行視角 | 4 個 | 無 |
| MAP-REDUCE | 是 | 否 |
| Context | fork | shared |
| 模型 | sonnet/haiku 混合 | haiku |
| 輸出 | 報告文檔 | 操作結果 |

## 目錄結構

### Skill 目錄

```
skills/plugin-dev/
├── SKILL.md                          # 主文檔 + Frontmatter
├── 00-quickstart/
│   └── _base/
│       └── usage.md                  # 快速開始指南
├── 01-commands/                      # 命令詳細說明（替代 perspectives）
│   └── _base/
│       ├── sync.md
│       ├── watch.md
│       ├── validate.md
│       ├── status.md
│       ├── version.md
│       └── release.md
├── config/
│   ├── commands.yaml                 # 命令配置
│   └── validation.yaml               # 驗證規則
└── templates/
    ├── release-notes.md.template     # 發布說明模板
    └── changelog-entry.md.template   # 變更日誌模板
```

### 狀態目錄

```
.plugin-dev/                          # 運行時狀態
├── cache-map.json                    # 增量同步映射
├── watch.config.json                 # 監控配置
├── release-progress.json             # 發布進度
└── logs/
    └── plugin-workflow.log           # 操作日誌
```

## SKILL.md Frontmatter

```yaml
---
name: plugin-dev
version: 1.0.0
description: Plugin 開發完整工作流 - 同步、監控、驗證、發布
triggers: [plugin-dev, plugin-workflow, plugin-sync, plugin-release]
context: shared                       # 不需要 fork，直接在主 Context
agent: general-purpose
allowed-tools: [Read, Write, Bash, Grep, Glob]
model: haiku                          # 輕量級工具，使用快速模型
hooks: false                          # 不使用自動 Hook，手動控制 commit
---
```

## 介面設計

### 命令結構

```
/plugin-dev <command> [subcommand] [options]

Commands:
  sync      同步到 Claude Code 快取
  watch     監控模式（熱載入）
  validate  驗證 Plugin 結構
  status    查看快取和版本狀態
  version   版本管理
  release   發布流程
```

### 命令詳細設計

#### `/plugin-dev sync`

```bash
/plugin-dev sync [options]

Options:
  --force       強制全量同步（忽略快取映射）
  --dry-run     預覽變更，不實際同步
  --verbose     顯示詳細輸出

Examples:
  /plugin-dev sync              # 增量同步
  /plugin-dev sync --force      # 全量同步
  /plugin-dev sync --dry-run    # 預覽變更
```

**實作路徑**：
```
Skill → Bash: python -m cli.plugin.dev sync [options]
     → DevCommands.sync()
     → CacheManager
```

#### `/plugin-dev watch`

```bash
/plugin-dev watch [options]

Options:
  --debounce N   防抖動時間（毫秒，預設 500）
  --no-initial   不執行初始同步
  --background   背景執行

Examples:
  /plugin-dev watch                    # 前台監控
  /plugin-dev watch --background       # 背景監控
  /plugin-dev watch --debounce 1000    # 1 秒防抖動
```

**實作路徑**：
```
Skill → Bash: python -m cli.plugin.dev watch [options]
     → DevCommands.watch()
     → fswatch / inotifywait / polling
```

#### `/plugin-dev validate`

```bash
/plugin-dev validate [options]

Options:
  --strict      嚴格模式（警告也視為錯誤）
  --fix         自動修復可修復的問題

Checks:
  - plugin.json 存在且有效
  - skills/ 目錄存在
  - 至少一個 SKILL.md
  - 版本一致性（plugin.json, marketplace.json）
```

**實作路徑**：
```
Skill → Bash: python -m cli.plugin.release validate [options]
     → ReleaseCommands.validate()
     → ValidationResult
```

#### `/plugin-dev status`

```bash
/plugin-dev status [options]

Options:
  --json        JSON 格式輸出

Output:
  Plugin: multi-agent-workflow
  Version: 2.4.0
  Cache: ~/.claude/plugins/cache/...
  Cache Status: Valid (synced 5 min ago)
  Skills: 8 loaded
  Last Release: v2.4.0 (2026-01-30)
```

**實作路徑**：
```
Skill → Bash: python -m cli.plugin.dev status [options]
     → CacheManager.status()
     → VersionManager.get_current_version()
```

#### `/plugin-dev version`

```bash
/plugin-dev version [command] [options]

Commands:
  (無)          顯示當前版本
  bump LEVEL    升級版本（patch/minor/major）
  check         檢查版本一致性

Options:
  --dry-run     預覽變更

Examples:
  /plugin-dev version             # 顯示 2.4.0
  /plugin-dev version bump patch  # 升級到 2.4.1
  /plugin-dev version check       # 檢查一致性
```

#### `/plugin-dev release`

```bash
/plugin-dev release [LEVEL] [options]

Arguments:
  LEVEL         版本級別：patch/minor/major（預設 patch）

Options:
  --dry-run     預覽完整發布流程
  --skip-tests  跳過測試步驟
  --resume      從中斷點恢復
  --yes         跳過確認提示

Examples:
  /plugin-dev release patch              # 發布 patch 版本
  /plugin-dev release minor --dry-run    # 預覽 minor 發布
  /plugin-dev release --resume           # 恢復中斷的發布
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

## 整合策略

### git_lib 整合

**改造 release.py**：

```python
# Before
def _git_commit(self, message: str):
    subprocess.run(["git", "add", "-A"], cwd=self.project_dir)
    subprocess.run(["git", "commit", "-m", message], cwd=self.project_dir)

# After
from scripts.git_lib import GitOps, WorkflowCommitFacade

def _git_commit(self, message: str):
    git = GitOps(self.project_dir)
    git.stage(["."])
    git.commit(message)
```

**優勢**：
- 統一 commit message 格式
- 自動處理 pathspec 排除
- 錯誤處理更完善

### 配置載入機制

```python
# cli/plugin/config.py
from pathlib import Path
import yaml

class PluginConfig:
    """Plugin 配置管理"""

    CONFIG_PATH = Path("shared/plugin/config.yaml")

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self._config = self._load()

    def _load(self) -> dict:
        config_file = self.project_dir / self.CONFIG_PATH
        if config_file.exists():
            return yaml.safe_load(config_file.read_text())
        return self._defaults()

    @property
    def cache_base(self) -> Path:
        """快取基礎路徑"""
        env_override = os.environ.get("PLUGIN_CACHE_BASE")
        if env_override:
            return Path(env_override)
        return Path(self._config["cache"]["base_path"]).expanduser()

    @property
    def watch_debounce(self) -> int:
        """監控防抖動時間"""
        return self._config.get("watch", {}).get("debounce_ms", 500)
```

### Skill 調用 Python CLI

**SKILL.md 執行流程**：

```markdown
## 執行流程

### /plugin-dev sync

1. **解析參數**：
   - `--force` → `force=True`
   - `--dry-run` → `dry_run=True`

2. **執行命令**：
   ```
   Bash: python -m cli.plugin.dev sync --force --dry-run
   ```

3. **處理輸出**：
   - 成功：顯示同步結果
   - 失敗：顯示錯誤訊息和修復建議
```

## 狀態管理設計

### ReleaseProgress 持久化

```python
# .plugin-dev/release-progress.json
{
    "workflow_id": "release_20260201_143000",
    "current_step": "CHANGELOG",
    "completed_steps": ["VALIDATE", "TEST", "CHECK_GIT", "BUMP"],
    "failed_step": null,
    "error": null,
    "new_version": "2.4.1",
    "started_at": "2026-02-01T14:30:00",
    "last_updated": "2026-02-01T14:35:00"
}
```

### 增量同步映射

```python
# .plugin-dev/cache-map.json
{
    "skills/plugin-dev/SKILL.md": {
        "hash": "sha256:a1b2c3...",
        "size": 12345,
        "mtime": 1706789012.34
    },
    "shared/plugin/config.yaml": {
        "hash": "sha256:d4e5f6...",
        "size": 2345,
        "mtime": 1706789010.00
    }
}
```

### Workflow ID 追蹤

```python
# 與 Claude Code Tasks 整合
WORKFLOW_ID = f"plugin-dev_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# 發布時建立任務
task_id = TaskCreate({
    "subject": f"Release v{new_version}",
    "description": "Plugin release workflow",
    "activeForm": "Releasing plugin",
})

# 更新進度
TaskUpdate({
    "taskId": task_id,
    "status": "in_progress",
    "metadata": {"step": current_step.value},
})
```

## 錯誤處理設計

### 錯誤類型

```python
# cli/plugin/exceptions.py
class PluginDevError(Exception):
    """Base exception"""
    pass

class CacheError(PluginDevError):
    """快取相關錯誤"""
    pass

class SyncError(PluginDevError):
    """同步相關錯誤"""
    pass

class ValidationError(PluginDevError):
    """驗證相關錯誤"""
    pass

class ReleaseError(PluginDevError):
    """發布相關錯誤"""
    pass
```

### 友善錯誤訊息

```python
def handle_error(error: PluginDevError):
    """處理錯誤並提供修復建議"""
    messages = {
        CacheError: {
            "message": "快取操作失敗",
            "suggestions": [
                "嘗試 /plugin-dev sync --force 強制同步",
                "檢查快取目錄權限",
                "使用 /plugin-dev status 查看詳情",
            ],
        },
        ValidationError: {
            "message": "Plugin 結構驗證失敗",
            "suggestions": [
                "檢查 plugin.json 格式",
                "確認 skills/ 目錄存在",
                "使用 /plugin-dev validate --fix 嘗試自動修復",
            ],
        },
    }
```

## 實作優先順序

### Phase 1: 基礎結構（Week 1-2）
1. 建立 skills/plugin-dev/ 目錄
2. 撰寫 SKILL.md
3. 實作 sync/validate/status 命令

### Phase 2: git_lib 整合（Week 2-3）
4. 修改 release.py 使用 git_lib
5. 統一 commit message 格式
6. 添加整合測試

### Phase 3: 發布功能（Week 3-4）
7. 實作 release 命令
8. 狀態持久化
9. Task API 整合

### Phase 4: 熱載入（Week 4-5）
10. 實作 watch 命令
11. 跨平台監控
12. 背景執行

### Phase 5: 完善（Week 5-6）
13. 文檔更新
14. Dogfooding 驗證
15. 效能優化

## 總結

**設計原則**：
1. **單一入口**：`/plugin-dev` 統一命令
2. **漸進複雜度**：簡單預設值 + 進階選項
3. **錯誤友善**：清晰訊息 + 修復建議
4. **狀態持久化**：支援中斷恢復
5. **模組化**：Skill 作介面，Python 作實作

**關鍵整合點**：
- git_lib 統一 Git 操作
- shared/plugin/config.yaml 配置管理
- Claude Code Tasks API 進度追蹤

---

*由系統架構師視角產出*
