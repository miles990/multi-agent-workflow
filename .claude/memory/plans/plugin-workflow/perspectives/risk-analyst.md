# Plugin 開發工作流 - 風險分析師視角

## 視角資訊

- 角色: 風險分析師
- 聚焦: 潛在風險、失敗場景、緩解策略
- 日期: 2026-02-01

## 風險矩陣

| 風險 | 機率 | 影響 | 嚴重度 | 優先級 |
|------|------|------|--------|--------|
| Claude Code 快取路徑變更 | Medium | High | High | P1 |
| 跨平台相容性問題 | Medium | Medium | Medium | P2 |
| 檔案監控效能問題 | Low | Medium | Low | P3 |
| 版本相容性誤判 | Medium | Low | Low | P4 |
| Git 操作失敗 | Low | High | Medium | P2 |
| 快取損壞 | Low | Medium | Low | P3 |
| 同步中斷導致不一致 | Medium | Medium | Medium | P2 |
| 發布流程中斷 | Low | High | Medium | P2 |

## 詳細風險分析

### 風險 1: Claude Code 快取路徑變更 (P1)

描述:
Claude Code 未來版本可能變更快取目錄位置或結構,導致同步功能失效。

發生場景:
- Claude Code 更新後快取位置從 ~/.claude/plugins/cache/ 變更
- 快取目錄結構改變(例如增加版本子目錄)
- Plugin 載入機制改變(例如不再從快取載入)

影響:
- 開發模式完全失效
- 使用者無法使用熱載入功能
- 需要緊急修復

機率: Medium (30%)

緩解策略:
1. 抽象化快取路徑為可配置項
2. 提供自動檢測腳本
3. 文檔說明手動配置方法
4. 監控 Claude Code 版本更新,提前測試

實作:
```python
# shared/plugin/config.yaml
cache:
  auto_detect: true
  manual_path: null  # 手動覆寫
  
  fallback_locations:
    - "~/.claude/plugins/cache/"
    - "~/.config/claude/plugins/"
    - "~/Library/Application Support/Claude/plugins/"  # macOS
```

驗證方式:
- 單元測試覆蓋路徑檢測邏輯
- 手動測試在不同 Claude Code 版本

---

### 風險 2: 跨平台相容性問題 (P2)

描述:
不同作業系統的檔案系統、路徑格式、工具可用性差異導致功能異常。

發生場景:
- Windows 路徑分隔符 \ vs /
- Windows 符號連結需要管理員權限
- Linux/macOS 檔案權限差異
- rsync 在 Windows 不可用或表現不同
- fswatch vs inotifywait vs watchdog

影響:
- 部分平台功能受限
- 使用者體驗不一致
- 增加支援成本

機率: Medium (40%)

緩解策略:
1. 使用跨平台工具和標準庫
2. 平台檢測和自動選擇工具
3. 提供純 Python 備選方案
4. CI/CD 在多平台測試

實作:
```python
import platform
import shutil

def get_sync_command():
    system = platform.system()
    
    if system in ["Darwin", "Linux"]:
        if shutil.which("rsync"):
            return "rsync"
        else:
            return "python_sync"  # 備選
    
    elif system == "Windows":
        if shutil.which("robocopy"):
            return "robocopy"
        else:
            return "python_sync"
    
    else:
        return "python_sync"
```

測試矩陣:
| 平台 | 檔案監控 | 同步工具 | 測試狀態 |
|------|---------|---------|---------|
| macOS 14+ | fswatch | rsync | 通過 |
| Ubuntu 22.04 | inotifywait | rsync | 通過 |
| Windows 11 | watchdog | python_sync | 待測試 |

---

### 風險 3: 檔案監控效能問題 (P3)

描述:
監控大量檔案或頻繁變更導致 CPU/記憶體佔用過高,影響系統效能。

發生場景:
- 專案包含大量檔案 (>10000)
- 頻繁儲存觸發大量同步 (每秒多次)
- 監控目錄包含 node_modules, .git 等大目錄
- 記憶體洩漏 (長時間運行)

影響:
- 使用者電腦變慢
- 電池快速消耗
- 負面使用者體驗

機率: Low (20%)

緩解策略:
1. 防抖動邏輯 (debounce 500ms)
2. 智能排除規則
3. 批次處理變更
4. 資源使用監控和限制

實作:
```python
import time
from collections import deque

class DebouncedSync:
    def __init__(self, delay=0.5):
        self.delay = delay
        self.last_sync = 0
        self.pending = deque()
    
    def trigger(self, files):
        self.pending.extend(files)
        
        now = time.time()
        if now - self.last_sync >= self.delay:
            self._do_sync()
    
    def _do_sync(self):
        if not self.pending:
            return
        
        files = set(self.pending)
        self.pending.clear()
        
        # 執行同步
        sync(files)
        self.last_sync = time.time()
```

監控指標:
- CPU 使用率 < 5%
- 記憶體佔用 < 100MB
- 同步延遲 < 1s (95th percentile)

---

### 風險 4: 版本相容性誤判 (P4)

描述:
自動檢測破壞性變更時誤判或漏判,導致版本號不正確或使用者升級後出問題。

發生場景:
- 靜態分析無法檢測行為變更
- 重構程式碼但保持 API 不變
- 依賴版本變更影響行為
- 配置預設值變更

影響:
- 使用者升級後功能異常
- 版本號語義不正確
- 信任度下降

機率: Medium (30%)

緩解策略:
1. 多層檢測機制 (靜態+語義+人工)
2. 提供人工審核流程
3. CHANGELOG.md 手動確認
4. 提供 override 選項
5. 詳細文檔說明破壞性變更定義

實作:
```python
def check_compatibility(old_ver, new_ver):
    results = []
    
    # 1. 靜態分析
    static_result = static_analysis(old_ver, new_ver)
    results.append(static_result)
    
    # 2. Git commit 分析
    git_result = analyze_commits(old_ver, new_ver)
    results.append(git_result)
    
    # 3. 人工標記檢查
    manual_result = check_manual_markers()
    results.append(manual_result)
    
    # 4. 綜合評估
    report = CompatibilityReport(results)
    
    # 5. 人工確認
    if report.has_warnings():
        confirmed = input(f"偵測到可能的破壞性變更:\n{report}\n繼續? (y/n): ")
        if confirmed != 'y':
            raise Aborted("使用者取消")
    
    return report
```

人工檢查清單:
- [ ] API 方法簽名是否變更?
- [ ] 必要參數是否新增?
- [ ] 配置檔案 schema 是否變更?
- [ ] 預設行為是否變更?
- [ ] 相依性版本是否有破壞性更新?

---

### 風險 5: Git 操作失敗 (P2)

描述:
發布過程中 Git 操作失敗,導致版本狀態不一致或發布中斷。

發生場景:
- 網路斷線導致 push 失敗
- 遠端分支保護規則阻擋 push
- 本地有未提交變更
- Tag 已存在
- 權限不足

影響:
- 發布流程中斷
- 版本狀態不一致 (本地已 tag 但遠端沒有)
- 需要手動修復

機率: Low (15%)

緩解策略:
1. 發布前強制檢查狀態
2. 提供 --dry-run 模擬執行
3. 詳細的錯誤訊息和建議
4. 支援從中斷點恢復
5. 使用已驗證的 git_lib 模組

實作:
```python
def pre_release_checks():
    """發布前檢查清單"""
    checks = [
        check_no_uncommitted_changes(),
        check_remote_exists(),
        check_remote_reachable(),
        check_tag_not_exists(),
        check_push_permission(),
    ]
    
    failed = [c for c in checks if not c.passed]
    
    if failed:
        raise PreReleaseCheckFailed(failed)

def release_with_recovery(dry_run=False):
    """支援中斷恢復的發布流程"""
    state = load_release_state()  # 從 .plugin-dev/release-state.json
    
    try:
        if not state.version_bumped:
            bump_version()
            state.version_bumped = True
            save_release_state(state)
        
        if not state.changelog_generated:
            generate_changelog()
            state.changelog_generated = True
            save_release_state(state)
        
        if not state.committed:
            git_commit()
            state.committed = True
            save_release_state(state)
        
        # ... 其他步驟
        
    except Exception as e:
        print(f"發布中斷: {e}")
        print("可使用 'plugin release --resume' 從中斷點繼續")
        raise
    
    finally:
        if dry_run:
            cleanup_dry_run()
```

錯誤訊息範例:
```
E-GIT-001: Git push 失敗

原因: 遠端分支有保護規則

建議步驟:
1. 檢查 GitHub/GitLab 分支保護設定
2. 確認你有 push 權限
3. 如需強制推送,使用 --force (謹慎使用)

技術細節:
  remote: error: GH006: Protected branch update failed
  To github.com:miles990/multi-agent-workflow.git
   ! [remote rejected] main -> main (protected branch hook declined)
```

---

### 風險 6: 快取損壞 (P3)

描述:
快取目錄損壞、不完整或與源碼不一致,導致 Claude Code 載入錯誤版本。

發生場景:
- 同步過程中系統崩潰
- 磁碟空間不足導致複製失敗
- 手動修改快取導致不一致
- 快取映射檔案損壞

影響:
- Claude Code 載入失敗或行為異常
- 難以診斷問題來源
- 需要手動修復

機率: Low (10%)

緩解策略:
1. 快取完整性驗證
2. 提供修復工具
3. 同步前檢查磁碟空間
4. 原子性操作 (寫入臨時目錄再 rename)
5. 詳細日誌記錄

實作:
```python
def validate_cache():
    """驗證快取完整性"""
    issues = []
    
    # 1. 檢查必要檔案
    required = ["plugin.json", ".claude-plugin/marketplace.json"]
    for file in required:
        if not (cache_dir / file).exists():
            issues.append(f"缺少必要檔案: {file}")
    
    # 2. 驗證 plugin.json 格式
    try:
        with open(cache_dir / "plugin.json") as f:
            data = json.load(f)
            if "name" not in data or "version" not in data:
                issues.append("plugin.json 格式不正確")
    except Exception as e:
        issues.append(f"plugin.json 無法解析: {e}")
    
    # 3. 檢查快取映射一致性
    cache_map = load_cache_map()
    for file, info in cache_map["files"].items():
        actual_hash = file_hash(cache_dir / file)
        if actual_hash != info["hash"]:
            issues.append(f"檔案 hash 不一致: {file}")
    
    return ValidationResult(issues)

def repair_cache():
    """修復快取"""
    print("檢測快取損壞,開始修復...")
    
    # 清空快取
    clean_cache()
    
    # 重新全量同步
    sync(force=True)
    
    print("快取修復完成")
```

自動修復觸發:
- 每次 `plugin dev watch` 啟動時自動驗證
- 發現問題時詢問是否自動修復
- 提供 `plugin cache repair` 手動修復命令

---

### 風險 7: 同步中斷導致不一致 (P2)

描述:
同步過程中被中斷 (Ctrl+C, 系統關機等),導致快取處於不一致狀態。

發生場景:
- 使用者按 Ctrl+C 中斷同步
- 系統休眠/關機
- rsync 被 kill
- 網路斷線 (如果使用網路檔案系統)

影響:
- 快取不完整
- 下次同步可能出錯
- Claude Code 載入異常

機率: Medium (25%)

緩解策略:
1. 使用原子性操作
2. 同步到臨時目錄再 rename
3. 訊號處理 (捕捉 SIGINT/SIGTERM)
4. 同步前備份
5. 自動恢復機制

實作:
```python
import signal
import shutil
from pathlib import Path

class AtomicSync:
    def __init__(self):
        self.temp_dir = None
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
    
    def sync(self, src, dst):
        # 1. 建立臨時目錄
        self.temp_dir = dst.parent / f".{dst.name}.tmp"
        self.temp_dir.mkdir(exist_ok=True)
        
        try:
            # 2. 同步到臨時目錄
            rsync(src, self.temp_dir)
            
            # 3. 驗證完整性
            if not self.validate(self.temp_dir):
                raise SyncError("同步驗證失敗")
            
            # 4. 原子性替換 (rename 是原子操作)
            backup = dst.parent / f".{dst.name}.backup"
            if dst.exists():
                dst.rename(backup)
            
            self.temp_dir.rename(dst)
            
            # 5. 清理備份
            if backup.exists():
                shutil.rmtree(backup)
            
        except Exception as e:
            self.cleanup()
            raise SyncError(f"同步失敗: {e}") from e
    
    def cleanup(self, *args):
        """訊號處理器"""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        print("\n同步已中斷,臨時檔案已清理")
        exit(1)
```

恢復策略:
- 下次同步時自動偵測並清理臨時目錄
- 如有備份,詢問是否恢復

---

### 風險 8: 發布流程中斷 (P2)

描述:
發布過程中某步驟失敗,導致版本狀態不一致或需要手動修復。

發生場景:
- 測試失敗但已升級版本號
- Git commit 成功但 push 失敗
- Tag 建立成功但遠端推送失敗
- Marketplace 更新失敗

影響:
- 版本狀態不一致
- 需要手動回滾或修復
- 可能誤發布不完整版本

機率: Low (15%)

緩解策略:
1. 使用狀態機追蹤進度
2. 支援從中斷點恢復
3. 提供回滾命令
4. 詳細日誌記錄
5. 事務性操作 (盡可能)

實作:
```python
from enum import Enum

class ReleaseState(Enum):
    INIT = "init"
    VALIDATED = "validated"
    TESTED = "tested"
    VERSION_BUMPED = "version_bumped"
    CHANGELOG_GENERATED = "changelog_generated"
    COMMITTED = "committed"
    TAGGED = "tagged"
    PUSHED = "pushed"
    MARKETPLACE_UPDATED = "marketplace_updated"
    COMPLETED = "completed"

class StatefulRelease:
    def __init__(self):
        self.state_file = Path(".plugin-dev/release-state.json")
        self.state = self.load_state()
    
    def release(self, resume=False):
        if resume:
            print(f"從狀態 {self.state} 繼續發布...")
        
        try:
            if self.state == ReleaseState.INIT:
                self.validate()
                self.update_state(ReleaseState.VALIDATED)
            
            if self.state == ReleaseState.VALIDATED:
                self.test()
                self.update_state(ReleaseState.TESTED)
            
            if self.state == ReleaseState.TESTED:
                self.bump_version()
                self.update_state(ReleaseState.VERSION_BUMPED)
            
            # ... 其他步驟
            
            self.update_state(ReleaseState.COMPLETED)
            self.cleanup_state()
            
        except Exception as e:
            self.save_state()
            print(f"\n發布中斷於步驟: {self.state.value}")
            print(f"錯誤: {e}")
            print(f"\n可使用以下命令恢復:")
            print(f"  plugin release --resume")
            print(f"或回滾:")
            print(f"  plugin release --rollback")
            raise
    
    def rollback(self):
        """回滾發布"""
        print(f"回滾發布 (當前狀態: {self.state.value})...")
        
        if self.state.value >= "tagged":
            # 刪除本地 tag
            git("tag", "-d", self.version)
        
        if self.state.value >= "committed":
            # 回退 commit (soft reset)
            git("reset", "--soft", "HEAD~1")
        
        if self.state.value >= "version_bumped":
            # 還原版本號
            git("checkout", "HEAD", "plugin.json", "CLAUDE.md", ...)
        
        self.cleanup_state()
        print("回滾完成")
```

使用者介面:
```bash
# 正常發布
$ plugin release
驗證 Plugin... ✓
執行測試... ✓
升級版本... ✓
生成變更日誌... ✓
Git commit... ✓
建立 tag... ✓
推送到遠端... ✗ 錯誤: 網路連線失敗

發布中斷於步驟: tagged
錯誤: GitPushError: Connection timeout

可使用以下命令恢復:
  plugin release --resume
或回滾:
  plugin release --rollback

# 恢復
$ plugin release --resume
從狀態 tagged 繼續發布...
推送到遠端... ✓
更新 Marketplace... ✓
發布完成!

# 回滾
$ plugin release --rollback
回滾發布 (當前狀態: tagged)...
刪除本地 tag v2.4.0... ✓
回退 commit... ✓
回滾完成
```

---

## 風險緩解時程

| 風險 | Phase | 緩解措施 |
|------|-------|---------|
| R1: 快取路徑變更 | Phase 1 | 可配置路徑、自動檢測 |
| R2: 跨平台相容性 | Phase 2 | 平台檢測、多平台測試 |
| R3: 效能問題 | Phase 2 | 防抖動、排除規則 |
| R4: 版本誤判 | Phase 3 | 多層檢測、人工確認 |
| R5: Git 操作失敗 | Phase 4 | 狀態機、恢復/回滾 |
| R6: 快取損壞 | Phase 1 | 驗證、自動修復 |
| R7: 同步中斷 | Phase 2 | 原子性操作、訊號處理 |
| R8: 發布中斷 | Phase 4 | 狀態追蹤、恢復機制 |

## 失敗場景模擬

### 場景 1: 快取目錄被手動刪除

步驟:
1. 使用者啟動 `plugin dev watch`
2. 另一視窗手動 `rm -rf ~/.claude/plugins/cache/multi-agent-workflow`
3. 源碼檔案變更觸發同步

預期行為:
- 檢測到快取目錄不存在
- 自動重新建立目錄
- 執行全量同步
- 顯示警告訊息

測試驗證:
```python
def test_cache_dir_deleted():
    watch = DevCommands()
    watch.start()
    
    # 模擬刪除
    shutil.rmtree(cache_dir)
    
    # 觸發同步
    trigger_file_change()
    
    # 驗證
    assert cache_dir.exists()
    assert all_files_synced()
```

### 場景 2: 網路斷線時發布

步驟:
1. 執行 `plugin release`
2. 在 Git push 階段斷開網路
3. Push 超時失敗

預期行為:
- 顯示錯誤訊息: "網路連線失敗"
- 保存發布狀態為 "tagged"
- 提示使用 `--resume` 或 `--rollback`
- 本地變更已保存 (commit + tag)

測試驗證:
```python
@mock.patch('subprocess.run')
def test_release_network_failure(mock_run):
    # 模擬 git push 失敗
    mock_run.side_effect = [
        CompletedProcess(returncode=0),  # commit
        CompletedProcess(returncode=0),  # tag
        TimeoutExpired(cmd=['git', 'push'], timeout=30),  # push 超時
    ]
    
    release = ReleaseCommands()
    with pytest.raises(GitPushError):
        release.release()
    
    # 驗證狀態保存
    state = load_release_state()
    assert state == ReleaseState.TAGGED
```

### 場景 3: 磁碟空間不足

步驟:
1. 磁碟剩餘空間 < 100MB
2. 執行 `plugin dev sync`
3. 同步過程中空間耗盡

預期行為:
- 同步前檢查磁碟空間
- 顯示錯誤: "磁碟空間不足"
- 建議清理或增加空間
- 不建立損壞的快取

測試驗證:
```python
def test_insufficient_disk_space(tmp_path, monkeypatch):
    # 模擬磁碟空間不足
    def mock_disk_usage(path):
        return (100 * 1024**3, 50 * 1024**3, 10 * 1024**2)  # 100MB free
    
    monkeypatch.setattr(shutil, 'disk_usage', mock_disk_usage)
    
    sync = DevCommands()
    with pytest.raises(InsufficientDiskSpaceError):
        sync.sync()
```

## 監控與告警

### 關鍵指標

| 指標 | 閾值 | 告警方式 |
|------|------|---------|
| 同步失敗率 | > 5% | 日誌警告 |
| 同步延遲 | > 3s (p95) | 日誌警告 |
| CPU 使用率 | > 10% | 日誌警告 |
| 記憶體使用 | > 200MB | 日誌警告 |
| 快取驗證失敗 | > 0 | 錯誤提示 |
| 發布失敗 | > 0 | 錯誤提示 |

### 日誌記錄

```python
import logging

logger = logging.getLogger("plugin-workflow")

# 同步事件
logger.info("開始同步 %d 個檔案", len(files))
logger.debug("檔案清單: %s", files)
logger.info("同步完成,耗時 %.2fs", elapsed)

# 錯誤
logger.error("同步失敗: %s", error, exc_info=True)

# 警告
logger.warning("檔案 hash 不一致,觸發全量同步")
```

日誌位置:
- 開發模式: 終端機輸出
- 生產模式: ~/.plugin-dev/logs/plugin-workflow.log

## 應急預案

### 預案 1: 快取損壞無法修復

症狀:
- `plugin cache repair` 失敗
- Claude Code 無法載入 Plugin

應對步驟:
1. 備份當前快取目錄
2. 完全刪除快取
3. 重新安裝 Plugin (`/plugin install ...`)
4. 驗證 Plugin 可正常載入
5. 分析備份找出根因

### 預案 2: 發布後發現重大 Bug

症狀:
- 新版本發布後使用者回報嚴重問題
- 需要緊急回滾

應對步驟:
1. 評估影響範圍和嚴重性
2. 決定修復 vs 回滾
3. 如回滾:
   - Git revert 或 reset
   - 重新標記版本
   - 更新 Marketplace
4. 通知使用者
5. 建立 hotfix 分支修復
6. 發布 patch 版本

### 預案 3: Marketplace 無法更新

症狀:
- 發布成功但 Marketplace 未同步
- 使用者無法安裝新版本

應對步驟:
1. 檢查 Marketplace API 狀態
2. 手動更新 .claude-plugin/marketplace.json
3. 聯繫 Claude Code 支援團隊
4. 文檔說明手動安裝方法
5. 監控 Marketplace 恢復

---

視角完成日期: 2026-02-01  
審核狀態: 待審核  
風險總數: 8 (P1: 1, P2: 4, P3: 2, P4: 1)
