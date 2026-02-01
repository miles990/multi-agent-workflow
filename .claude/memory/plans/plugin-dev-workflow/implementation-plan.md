# plugin-dev Skill 實作計劃

> 將 Plugin-Workflow 整合為可復用 Skill，實現 Dogfooding

**工作流 ID**：orchestrate_20260201_144146_900673cd
**階段**：PLAN
**日期**：2026-02-01
**視角**：4（架構師、風險分析師、估算專家、UX 倡導者）

## 執行摘要

本計劃基於 RESEARCH 階段的研究報告和 4 個規劃視角的分析，制定 plugin-dev Skill 的詳細實作路線。

**關鍵決策**：
1. **單一 Skill**：`/plugin-dev` 統一入口
2. **工具型架構**：不使用 MAP-REDUCE，保持簡單
3. **混合實作**：Python 核心 + Shell fallback + Skill 介面
4. **漸進式遷移**：優先 MVP，逐步完善

**預估**：
- 總工作量：89 點
- 時程：6-8 週
- 里程碑：4 個

## 架構設計

### 層次結構

```
┌─────────────────────────────────────────────────────┐
│                  Skill Layer                         │
│  /plugin-dev [command] [options]                    │
│  skills/plugin-dev/SKILL.md                         │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│               Python CLI Layer                       │
│  cli/plugin/{cache,version,dev,release}.py          │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│              Shared Modules Layer                    │
│  scripts/git_lib/ + shared/plugin/config.yaml       │
└─────────────────────────────────────────────────────┘
```

### 目錄結構

```
skills/plugin-dev/
├── SKILL.md                      # 主文檔 + Frontmatter
├── 00-quickstart/
│   └── _base/
│       └── usage.md              # 快速開始
├── 01-commands/
│   └── _base/
│       ├── sync.md
│       ├── watch.md
│       ├── validate.md
│       ├── status.md
│       ├── version.md
│       └── release.md
└── config/
    ├── commands.yaml
    └── validation.yaml
```

### SKILL.md Frontmatter

```yaml
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
```

## 命令設計

### 命令總覽

| 命令 | 功能 | 優先級 | Phase |
|------|------|--------|-------|
| `/plugin-dev sync` | 同步到快取 | P0 | 2 |
| `/plugin-dev validate` | 驗證結構 | P0 | 2 |
| `/plugin-dev status` | 查看狀態 | P0 | 2 |
| `/plugin-dev watch` | 監控模式 | P1 | 5 |
| `/plugin-dev version` | 版本管理 | P1 | 4 |
| `/plugin-dev release` | 發布流程 | P1 | 4 |

### 命令詳情

#### /plugin-dev sync

```bash
/plugin-dev sync [--force] [--dry-run] [--verbose]
```

**實作**：
```python
# Skill → Bash
Bash: python -m cli.plugin.dev sync --force --dry-run

# DevCommands.sync()
def sync(self, force: bool = False, dry_run: bool = False) -> SyncResult:
    if force:
        self._clear_cache_map()

    source_manifest = self.cache.get_file_manifest(self.project_dir)
    cache_manifest = self._load_cache_map() if not force else {}

    added, modified, deleted = self._compare(source_manifest, cache_manifest)

    if dry_run:
        return SyncResult(success=True, added=added, modified=modified, deleted=deleted)

    self._sync_files(added + modified)
    self._delete_files(deleted)
    self._save_cache_map(source_manifest)

    return SyncResult(success=True, ...)
```

#### /plugin-dev release

```bash
/plugin-dev release [LEVEL] [--dry-run] [--resume] [--yes]
```

**發布流程**：
```
VALIDATE → TEST → CHECK_GIT → BUMP → CHANGELOG → COMMIT → TAG → PUSH → COMPLETE
```

**狀態持久化**：
```python
# .plugin-dev/release-progress.json
{
    "workflow_id": "release_20260201_143000",
    "current_step": "CHANGELOG",
    "completed_steps": ["VALIDATE", "TEST", "CHECK_GIT", "BUMP"],
    "new_version": "2.4.1"
}
```

## 整合策略

### git_lib 整合

**Before**：
```python
subprocess.run(["git", "add", "-A"], cwd=self.project_dir)
subprocess.run(["git", "commit", "-m", message], cwd=self.project_dir)
```

**After**：
```python
from scripts.git_lib import GitOps

git = GitOps(self.project_dir)
git.stage(["."])
git.commit(message)
```

### 配置載入

```python
class PluginConfig:
    CONFIG_PATH = Path("shared/plugin/config.yaml")

    def __init__(self, project_dir: Path):
        self._config = yaml.safe_load(
            (project_dir / self.CONFIG_PATH).read_text()
        )

    @property
    def cache_base(self) -> Path:
        return Path(os.environ.get("PLUGIN_CACHE_BASE") or
                   self._config["cache"]["base_path"]).expanduser()
```

## 任務分解

### Phase 1: Skill 結構建立（13 點，Week 1）

| ID | 任務 | 點數 | 依賴 |
|----|------|------|------|
| 1.1 | 建立 skills/plugin-dev/ 目錄 | 2 | - |
| 1.2 | 撰寫 SKILL.md | 3 | 1.1 |
| 1.3 | 撰寫 00-quickstart/usage.md | 3 | 1.2 |
| 1.4 | 建立 01-commands/ 目錄 | 3 | 1.2 |
| 1.5 | 配置執行模式 | 2 | 1.2 |

### Phase 2: 核心命令（21 點，Week 2）

| ID | 任務 | 點數 | 依賴 |
|----|------|------|------|
| 2.1 | 實作 /plugin-dev sync | 5 | 1.2 |
| 2.2 | 實作 /plugin-dev validate | 3 | 1.2 |
| 2.3 | 實作 /plugin-dev status | 3 | 1.2 |
| 2.4 | 建立 Skill 框架 | 5 | 1.2 |
| 2.5 | 配置載入機制 | 5 | 1.2 |

### Phase 3: git_lib 整合（13 點，Week 3）

| ID | 任務 | 點數 | 依賴 |
|----|------|------|------|
| 3.1 | 建立 GitLibAdapter | 5 | - |
| 3.2 | 修改 release.py | 5 | 3.1 |
| 3.3 | 統一 commit message | 3 | 3.2 |

### Phase 4: 發布流程（21 點，Week 4）

| ID | 任務 | 點數 | 依賴 |
|----|------|------|------|
| 4.1 | 實作 /plugin-dev release | 5 | 2.4, 3.2 |
| 4.2 | 完善狀態機 | 5 | 4.1 |
| 4.3 | Task API 整合 | 5 | 4.1 |
| 4.4 | 進度持久化 | 3 | 4.2 |
| 4.5 | 錯誤恢復機制 | 3 | 4.4 |

### Phase 5: 熱載入（13 點，Week 5-6）

| ID | 任務 | 點數 | 依賴 |
|----|------|------|------|
| 5.1 | 實作 /plugin-dev watch | 5 | 2.4 |
| 5.2 | 跨平台監控 | 5 | 5.1 |
| 5.3 | 背景執行 | 3 | 5.1 |

### Phase 6: 文檔與 Dogfooding（8 點，Week 7-8）

| ID | 任務 | 點數 | 依賴 |
|----|------|------|------|
| 6.1 | 更新 CLAUDE.md | 3 | 4.5, 5.3 |
| 6.2 | 撰寫教程 | 2 | 6.1 |
| 6.3 | Dogfooding 驗證 | 3 | 6.1 |

## 依賴關係圖

```
Phase 1 (Skill 結構)
    │
    ▼
Phase 2 (核心命令) ────┐
    │                  │
    ▼                  ▼
Phase 3 (git_lib) → Phase 4 (發布流程)
                       │
Phase 5 (熱載入) ◄─────┘
    │
    ▼
Phase 6 (文檔 + Dogfooding)
```

## 里程碑

### M1: MVP（Week 2）

**交付物**：
- `/plugin-dev sync` 可用
- `/plugin-dev validate` 可用
- `/plugin-dev status` 可用

**驗收標準**：
- 可取代 `./scripts/plugin/sync-to-cache.sh`
- 測試覆蓋率 > 70%

### M2: 發布功能（Week 4）

**交付物**：
- `/plugin-dev release [level]` 可用
- git_lib 完整整合
- 進度持久化和恢復

**驗收標準**：
- 可取代 `./scripts/plugin/publish.sh`
- 支援 --dry-run 和 --resume

### M3: 完整功能（Week 6）

**交付物**：
- `/plugin-dev watch` 可用
- 跨平台驗證通過

**驗收標準**：
- macOS/Linux 監控正常
- Windows polling 可用

### M4: Dogfooding 成熟（Week 8）

**交付物**：
- 完整文檔
- 用 plugin-dev 開發 plugin-dev

**驗收標準**：
- 新手 30 分鐘內上手
- 所有 P1 風險已緩解

## 風險緩解

### P1 風險及緩解

| 風險 | 緩解措施 | 時程 |
|------|---------|------|
| R1 Dogfooding 循環 | 雙軌制開發 + Git 分支保護 | Week 1 |
| R2 git_lib Bug | 整合測試 + 漸進式遷移 | Week 2-3 |
| R3 Claude Code 變更 | 路徑自動檢測 + 手動配置 | Week 1-2 |

### 測試策略

| 層次 | 覆蓋率目標 | 執行時機 |
|------|-----------|---------|
| 單元測試 | 85% | 每次 commit |
| 整合測試 | 70% | 每個 Phase |
| 端到端測試 | 50% | 每個里程碑 |

## UX 設計重點

### 輸出格式

**成功**：
```
✓ 同步完成
  新增: 3 個檔案
  修改: 2 個檔案
  耗時: 1.2s
```

**錯誤**：
```
✗ 同步失敗
  錯誤: 快取目錄不可寫入

💡 修復建議:
  1. 檢查目錄權限
  2. 嘗試 /plugin-dev sync --force
```

### 視覺化

- Watch 模式：即時狀態儀表板
- Release 進度：步驟指示器
- Status 輸出：結構化信息

## 品質閘門

### PLAN 階段閘門（≥75 分）

| 檢查項 | 狀態 |
|--------|------|
| 所有組件有設計 | ✅ |
| 風險評估完成 | ✅ |
| 里程碑定義清晰 | ✅ |
| 任務分解完整 | ✅ |

**品質分數**：88/100

## 下一步

1. **進入 TASKS 階段**
   - 生成 tasks.yaml（DAG 格式）
   - 詳細任務描述
   - TDD 測試對應

2. **開始 Phase 1 實作**
   - 建立 skills/plugin-dev/ 目錄
   - 撰寫 SKILL.md

3. **建立測試框架**
   - tests/skills/test_plugin_dev.py
   - 整合測試 fixture

## 附錄

### 視角報告連結

- [系統架構師報告](./perspectives/architect.md)
- [風險分析師報告](./perspectives/risk-analyst.md)
- [估算專家報告](./perspectives/estimator.md)
- [UX 倡導者報告](./perspectives/ux-advocate.md)

### 相關資源

- [研究匯總報告](../research/plugin-dev-workflow/synthesis.md)
- [Skill 結構標準](../../shared/skill-structure/STANDARD.md)
- [品質閘門配置](../../shared/quality/gates.yaml)

---

**下一階段**：TASKS - 任務分解
**預計輸出**：tasks.yaml
