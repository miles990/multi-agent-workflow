# Plugin 開發工作流 - 系統架構師視角

## 視角資訊

- 角色: 系統架構師
- 聚焦: 技術可行性、組件設計、系統擴展性
- 日期: 2026-02-01

## 架構分析

### 1. 系統分層設計

```
┌─────────────────────────────────────────┐
│         CLI Layer (cli/plugin/)         │  使用者介面層
│  - 命令解析、參數驗證、錯誤提示         │
├─────────────────────────────────────────┤
│      Business Logic Layer               │  業務邏輯層
│  - DevCommands, VersionManager          │
│  - CacheManager, ReleaseCommands        │
├─────────────────────────────────────────┤
│      Utility Layer (scripts/plugin/)    │  工具層
│  - Shell scripts, Git operations        │
├─────────────────────────────────────────┤
│      Configuration Layer                │  配置層
│  - .plugin-dev/, shared/plugin/         │
├─────────────────────────────────────────┤
│      Storage Layer                      │  儲存層
│  - ~/.claude/plugins/cache/             │
│  - Git repository                       │
└─────────────────────────────────────────┘
```

### 2. 核心組件設計

#### 2.1 CacheManager (快取管理器)

職責:
- 快取位置管理
- 快取狀態查詢
- 快取清理和驗證

介面:
```python
class CacheManager:
    def get_cache_dir(plugin_name: str) -> Path
    def clean(plugin_name: str = None) -> None
    def status() -> CacheStatus
    def validate() -> ValidationResult
```

依賴:
- pathlib.Path (標準庫)
- json (配置讀取)

#### 2.2 VersionManager (版本管理器)

職責:
- 版本號升級
- 相容性檢查
- 變更日誌生成

介面:
```python
class VersionManager:
    def bump(level: Literal["major", "minor", "patch"]) -> str
    def check_compatibility(target_version: str) -> CompatibilityReport
    def generate_changelog(since_tag: str = None) -> str
```

依賴:
- git_lib (已有統一模組)
- semver (語義化版本解析)
- json (plugin.json 讀寫)

#### 2.3 DevCommands (開發命令)

職責:
- 熱載入監控
- 檔案同步
- 符號連結管理

介面:
```python
class DevCommands:
    def watch(auto_sync: bool = True) -> None
    def sync(force: bool = False) -> SyncResult
    def link() -> None
```

依賴:
- CacheManager
- watchdog (檔案監控,可選依賴)
- subprocess (呼叫 rsync)

#### 2.4 ReleaseCommands (發布命令)

職責:
- 發布工作流編排
- 發布前驗證
- Marketplace 整合

介面:
```python
class ReleaseCommands:
    def release(dry_run: bool = False) -> ReleaseResult
    def validate() -> ValidationResult
```

依賴:
- VersionManager
- git_lib
- 測試執行器

### 3. 資料流設計

#### 3.1 開發模式資料流

```
源碼變更 -> 檔案監控(fswatch) -> 觸發同步 
  -> 計算檔案hash -> 比對快取映射 -> 僅同步變更檔案 
  -> 更新快取映射 -> 完成
```

#### 3.2 版本發布資料流

```
開始發布 -> 驗證結構 -> 執行測試 -> 檢查Git狀態
  -> 使用者選擇版本級別 -> 升級版本號(plugin.json等)
  -> 生成變更日誌 -> Git commit -> Git tag
  -> Git push -> 更新Marketplace -> 完成
```

### 4. 錯誤處理架構

#### 4.1 錯誤分類

| 類別 | 錯誤碼前綴 | 範例 |
|------|-----------|------|
| 配置錯誤 | E-CFG | 快取目錄不存在、配置檔案損壞 |
| Git 錯誤 | E-GIT | 未提交變更、推送失敗 |
| 驗證錯誤 | E-VAL | 測試失敗、Lint 錯誤 |
| 環境錯誤 | E-ENV | 缺少 rsync、fswatch 未安裝 |

#### 4.2 錯誤處理策略

```python
class PluginError(Exception):
    """基礎異常類別"""
    def __init__(self, code: str, message: str, suggestion: str):
        self.code = code
        self.message = message
        self.suggestion = suggestion

# 使用範例
raise PluginError(
    code="E-CFG-001",
    message="快取目錄不存在: ~/.claude/plugins/cache/",
    suggestion="請確認 Claude Code 已安裝並至少載入過一次 Plugin"
)
```

### 5. 擴展性設計

#### 5.1 Provider 模式 (未來擴展)

```python
class SyncProvider(ABC):
    @abstractmethod
    def sync(src: Path, dst: Path, exclude: List[str]) -> SyncResult:
        pass

class RsyncProvider(SyncProvider):
    def sync(...): ...

class NativeProvider(SyncProvider):
    """純 Python 實作,無外部依賴"""
    def sync(...): ...
```

#### 5.2 Hook 機制

```python
# 允許在關鍵點註冊自訂邏輯
class PluginCLI:
    def __init__(self):
        self.hooks = {
            "pre_sync": [],
            "post_sync": [],
            "pre_release": [],
            "post_release": []
        }
    
    def register_hook(self, event: str, callback: Callable):
        self.hooks[event].append(callback)
```

### 6. 效能考量

#### 6.1 快取同步優化

策略:
1. Hash-based 增量同步 (僅同步變更檔案)
2. 排除規則早期過濾 (減少檢查檔案數)
3. 並行計算 hash (多執行緒)

預期效果:
- 初次同步: ~2-3s (全部檔案)
- 增量同步: ~100-500ms (1-10 個檔案)

#### 6.2 檔案監控優化

策略:
1. Debounce 500ms (避免連續觸發)
2. 批次處理變更 (一次同步多個檔案)
3. 智能排除 (不監控 .git, __pycache__ 等)

預期效果:
- CPU 使用率: < 1%
- 記憶體佔用: < 50MB

### 7. 安全性設計

#### 7.1 路徑安全

```python
def safe_path(base: Path, relative: str) -> Path:
    """防止路徑遍歷攻擊"""
    resolved = (base / relative).resolve()
    if not resolved.is_relative_to(base):
        raise SecurityError("路徑遍歷嘗試")
    return resolved
```

#### 7.2 Git 操作安全

- 發布前強制檢查未提交變更
- 推送前確認遠端分支存在
- 使用 git_lib 統一模組,避免 shell injection

### 8. 技術債務管理

#### 8.1 已知限制

| 限制 | 影響 | 計劃改善時機 |
|------|------|------------|
| 依賴 watchdog 套件 | 增加依賴 | Phase 6+ (可選純Python實作) |
| 依賴 rsync 外部工具 | 需預先安裝 | Phase 6+ (可選純Python實作) |
| 僅支援 Git | 不支援其他VCS | 需求不明確,暫不處理 |

#### 8.2 重構機會

- DevCommands.watch() 可抽象為獨立的 FileWatcher 類別
- VersionManager.generate_changelog() 可支援自訂模板
- 配置載入邏輯可統一為 ConfigLoader

## 設計模式應用

### 1. Facade Pattern

PluginCLI 作為 Facade,簡化複雜子系統:

```python
class PluginCLI:
    def __init__(self):
        # 初始化所有子系統
        self.version_manager = VersionManager()
        self.cache_manager = CacheManager()
        self.dev = DevCommands(cache_manager)
        self.release = ReleaseCommands(version_manager)
    
    # 提供簡化的公開介面
```

### 2. Strategy Pattern

同步策略可抽換:

```python
class DevCommands:
    def __init__(self, sync_strategy: SyncProvider):
        self.sync_strategy = sync_strategy
    
    def sync(self):
        self.sync_strategy.sync(...)
```

### 3. Repository Pattern

Git 操作已封裝於 git_lib:

```python
from git_lib import GitOps

git = GitOps(project_dir)
git.commit("message")
git.tag("v1.0.0")
git.push()
```

## 整合點

### 1. 與現有 git_lib 整合

```python
from git_lib import WorkflowCommitFacade

facade = WorkflowCommitFacade(project_dir)

# 發布時使用
facade.auto_commit_after_task(
    "chore(release): bump version to 2.4.0",
    success=True
)
```

### 2. 與 validate-skills.sh 整合

```python
def validate_plugin():
    result = subprocess.run(
        ["./scripts/validate-skills.sh", "--ci"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise ValidationError("Skill 結構驗證失敗")
```

## 部署考量

### 1. 平台相容性

| 平台 | 檔案監控工具 | 同步工具 | 測試狀態 |
|------|------------|---------|---------|
| macOS | fswatch | rsync | 主要開發平台 |
| Linux | inotifywait | rsync | CI/CD 測試 |
| Windows | watchdog (Python) | robocopy | 待測試 |

### 2. 相依性管理

必要依賴:
- Python >= 3.10
- Git >= 2.30

可選依賴:
- fswatch (macOS) 或 inotifywait (Linux)
- rsync (跨平台)
- watchdog (Python,跨平台備選)

安裝指示將包含在文檔中。

## 架構決策記錄

### ADR-001: 選擇 rsync 而非純 Python 實作

決策: 使用 rsync 作為預設同步工具

理由:
- 成熟穩定,經過時間考驗
- 效能優異(增量同步、壓縮)
- 跨平台支援良好
- 減少自行維護的程式碼

代價:
- 增加外部依賴
- 需要預先安裝

替代方案:
- 純 Python 實作 (Phase 6+ 作為備選)

### ADR-002: 選擇 Python CLI 而非純 Bash

決策: 使用 Python 實作 CLI,Bash 作為輔助腳本

理由:
- 更好的錯誤處理
- 跨平台相容性佳
- 易於測試
- 與現有 cli/ 結構一致

代價:
- 啟動時間稍長 (可忽略)

### ADR-003: 語義化版本策略

決策: 強制使用語義化版本 (semver)

理由:
- 業界標準
- 相容性語義明確
- 工具生態豐富

約束:
- 版本號必須符合 X.Y.Z 格式
- Breaking changes 必須升級 major 版本

---

視角完成日期: 2026-02-01  
審核狀態: 待審核
