# Git Workflow Optimization - 工作流視角分析

> 分析 multi-agent-workflow plugin 的 Git 使用工作流，發現痛點並提出優化方案

## 執行摘要

經過深入分析，發現當前 Git 工作流存在 **架構分散** 和 **狀態管理混亂** 兩大核心問題。本報告提出統一 Hook 系統、集中狀態管理、優化 Worktree 生命週期等改進方案。

## 1. 現有工作流架構

### 1.1 Hook 系統雙軌制

```
templates/hooks/workflow_hooks.py   (簡化版，統一入口)
         │
         ├─ post_task handler
         └─ subagent_stop handler

scripts/hooks/                      (完整版，獨立模組)
         ├─ post_task.py
         ├─ subagent_stop.py
         ├─ update_state.py
         ├─ log_action.py
         └─ init_workflow.py
```

**問題**：
- `templates/hooks/workflow_hooks.py` 是簡化版統一入口，但**沒有使用** `scripts/hooks/` 的模組
- `scripts/hooks/*.py` 是完整實作，但**沒有被統一入口調用**
- settings.hooks.json 指向 `scripts/hooks/workflow_hooks.py`，但該檔案不存在
- 造成功能重複實作、維護困難

### 1.2 觸發流程

```yaml
當前實作:
  PostToolUse (Task 完成):
    templates/workflow_hooks.py post_task:
      - auto_commit() # 直接實作
      - run_verification()
    
    scripts/post_task.py:
      - _commit_task_changes() # 重複實作
      - update_state()
      - log_action()

  SubagentStop (Agent 結束):
    templates/workflow_hooks.py subagent_stop:
      - 檢查 .claude/memory/ 變更
      - 提示用戶執行 /memory-commit
    
    scripts/subagent_stop.py:
      - _commit_memory() # 自動 commit
      - log_action()
```

### 1.3 狀態追蹤分散

```
current.json 被多處讀寫：
  - scripts/hooks/update_state.py
  - scripts/hooks/post_task.py
  - scripts/hooks/subagent_stop.py
  - scripts/hooks/init_workflow.py
  - cli/io/state.py (StateTracker)
  - shared/tools/workflow-status.py
```

**問題**：
- 沒有統一的狀態管理抽象
- 各處直接讀寫 JSON 檔案
- 容易造成狀態不一致

## 2. 工作流痛點分析

### 2.1 Hook 系統痛點

| 痛點 | 影響 | 嚴重度 |
|------|------|--------|
| **雙軌實作** | 功能重複、維護困難 | 🔴 高 |
| **路徑錯誤** | settings.hooks.json 指向不存在的檔案 | 🔴 高 |
| **行為不一致** | templates 版本只提示，scripts 版本自動 commit | 🟡 中 |
| **缺乏統一** | 無法確定哪個是「正式版本」 | 🟡 中 |

### 2.2 Commit 時機痛點

```yaml
目前 Commit 時機:
  Task 完成 (PostToolUse):
    templates版: 
      - 立即 commit 程式碼變更
      - 排除 memory/logs
      - 測試失敗只警告
    
    scripts版:
      - 可設定 include_memory/logs
      - 依據 commit-settings.yaml
      - 成功才 commit

  Subagent 結束 (SubagentStop):
    templates版:
      - 只檢查、不 commit
      - 提示用戶執行 /memory-commit
    
    scripts版:
      - 自動 commit .claude/memory/
      - 按 memory type 分類 commit
      - 記錄 action log
```

**痛點**：
- **行為不一致**：同一事件，兩個版本處理邏輯不同
- **時機混亂**：到底該在 Task 完成 commit 還是 Subagent 結束 commit？
- **粒度問題**：memory 變更是該單獨 commit 還是合併 commit？

### 2.3 狀態管理痛點

```yaml
current.json 狀態問題:
  讀取點:
    - 8 個不同模組都在讀 current.json
    - 無統一 API，各自解析 JSON
  
  寫入點:
    - 5 個模組會寫 current.json
    - 無鎖機制，可能並行寫入
  
  格式不一致:
    - workflow_id vs workflow.id
    - agents[] 結構各處定義不同
    - progress 計算邏輯分散
```

**痛點**：
- **並行衝突風險**：多個 hook 可能同時寫入
- **格式漂移**：缺乏 schema 驗證
- **難以除錯**：狀態來源不明確

### 2.4 Worktree 生命週期痛點

```yaml
Worktree 管理問題:
  創建 (CP0.5):
    文檔: PLAN 完成後創建
    實作: 分散在多處，無統一入口
    痛點: 創建失敗無標準錯誤處理
  
  使用:
    文檔: IMPLEMENT/REVIEW/VERIFY 在 worktree 中
    實作: 路徑解析分散
    痛點: worktree 內外路徑轉換容易出錯
  
  完成 (CP6.5):
    文檔: SHIP_IT/BLOCKED/ABORT 三種結果
    實作: 缺乏統一的完成處理流程
    痛點: merge/cleanup 邏輯不完整
```

## 3. 優化方案設計

### 3.1 統一 Hook 系統

#### 方案 A：Templates 為主（推薦）

```python
# templates/hooks/workflow_hooks.py (統一入口)
import sys
from pathlib import Path

# 動態載入 scripts/hooks/ 模組
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts/hooks"))

from post_task import handle_post_task as scripts_post_task
from subagent_stop import handle_subagent_stop as scripts_subagent_stop

def handle_post_task(input_data: dict) -> None:
    """委派給 scripts 版本"""
    scripts_post_task(input_data)

def handle_subagent_stop(input_data: dict) -> None:
    """委派給 scripts 版本"""
    scripts_subagent_stop(input_data)
```

**優點**：
- 保持統一入口（templates/hooks/workflow_hooks.py）
- 使用完整實作（scripts/hooks/*.py）
- 向後兼容現有設定

#### 方案 B：Scripts 為主

```json
// settings.hooks.json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Task",
      "hooks": [{
        "type": "command",
        "command": "python3 \"$CLAUDE_PROJECT_DIR/scripts/hooks/post_task.py\""
      }]
    }],
    "SubagentStop": [{
      "hooks": [{
        "type": "command",
        "command": "python3 \"$CLAUDE_PROJECT_DIR/scripts/hooks/subagent_stop.py\""
      }]
    }]
  }
}
```

**優點**：
- 直接使用完整版
- 刪除 templates 版本，減少重複
- 配置更直接

**推薦：方案 A**，因為保持單一入口點更易於版本控制和更新。

### 3.2 統一狀態管理

#### 設計：WorkflowState 抽象層

```python
# cli/io/workflow_state.py (新增)
from pathlib import Path
from typing import Optional
import json
import fcntl  # 檔案鎖
from datetime import datetime

class WorkflowState:
    """統一的 Workflow 狀態管理"""
    
    def __init__(self, workflow_id: str, base_path: str = None):
        self.workflow_id = workflow_id
        self.state_file = self._locate_state_file(workflow_id, base_path)
        self._lock_file = None
    
    def __enter__(self):
        """自動加鎖"""
        self._lock_file = open(self.state_file.parent / ".lock", "w")
        fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX)
        return self
    
    def __exit__(self, *args):
        """自動解鎖"""
        if self._lock_file:
            fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
            self._lock_file.close()
    
    # 讀取方法
    def get_stage(self) -> Optional[str]:
        """取得當前階段"""
        return self._load().get("stage")
    
    def get_agents(self) -> list:
        """取得 agents 列表"""
        return self._load().get("agents", [])
    
    # 更新方法
    def set_stage(self, stage: str):
        """設定階段"""
        with self:  # 自動加鎖
            state = self._load()
            state["stage"] = stage
            state["updated_at"] = datetime.utcnow().isoformat()
            self._save(state)
    
    def update_agent_status(self, agent_id: str, status: str):
        """更新 agent 狀態"""
        with self:
            state = self._load()
            for agent in state.get("agents", []):
                if agent["id"] == agent_id:
                    agent["status"] = status
                    break
            self._save(state)
```

#### 統一使用方式

```python
# 所有 hooks 統一使用
from cli.io.workflow_state import WorkflowState

def handle_post_task(input_data: dict):
    workflow_id = _get_workflow_id(input_data)
    state = WorkflowState(workflow_id)
    
    # 原子更新
    state.update_agent_status(
        agent_id="task-123",
        status="completed"
    )
```

### 3.3 優化 Commit 時機

#### 統一 Commit 策略

```yaml
Commit 時機重新設計:
  
  1. Task 完成 (PostToolUse):
    行為: 
      - 立即 commit 程式碼變更
      - 不包含 .claude/memory/
      - 測試失敗 → 只警告，仍然 commit
    
    理由:
      - 保存工作進度（即使測試失敗）
      - Memory 有獨立 commit 流程
      - 程式碼與 Memory 分離便於審查
  
  2. Subagent 結束 (SubagentStop):
    行為:
      - 自動 commit .claude/memory/ 變更
      - 按 memory type 分類（research/plans/etc.）
      - 每個 type/id 獨立 commit
    
    理由:
      - Memory 是知識產出，應獨立版本控制
      - 分類 commit 便於追蹤特定 memory 演變
      - 與程式碼 commit 隔離
  
  3. Checkpoint Commit (CP4):
    行為:
      - Skill 階段完成後觸發
      - Commit 該階段所有產出（memory + code）
      - 使用標準化 commit message
    
    理由:
      - 階段性里程碑
      - 便於 rollback 到特定階段
      - 符合工作流語義
```

#### Commit Message 標準化

```yaml
格式規範:
  Task Commit (程式碼):
    format: "chore(task): {description}"
    example: "chore(task): implement user login validation"
    content: 程式碼變更（不含 memory）
  
  Memory Commit (知識):
    format: "{type}({memory_type}): {topic}"
    example: "docs(research): complete user-auth research"
    content: .claude/memory/{type}/{id}/
  
  Checkpoint Commit (里程碑):
    format: "{type}({skill}): {milestone}"
    example: "feat(plan): complete user-auth implementation plan"
    content: 該階段所有產出
```

### 3.4 優化 Worktree 生命週期

#### 統一 Worktree 管理器

```python
# shared/git/worktree_manager.py (新增)
class WorktreeManager:
    """統一的 Worktree 生命週期管理"""
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.worktree_path = Path(f".worktrees/{workflow_id}")
        self.branch_name = f"feature/{workflow_id}"
    
    # 創建 (CP0.5)
    def create(self) -> bool:
        """創建 worktree（含完整檢查與 setup）"""
        try:
            # 1. 前置檢查
            self._validate_preconditions()
            
            # 2. 創建 worktree
            self._git_worktree_add()
            
            # 3. 環境 setup
            self._setup_environment()
            
            # 4. Baseline 驗證
            self._verify_baseline()
            
            # 5. 更新狀態
            self._update_workflow_state("active")
            
            return True
        except Exception as e:
            self._handle_creation_error(e)
            return False
    
    # 完成 (CP6.5)
    def complete(self, result: str) -> bool:
        """處理完成（SHIP_IT/BLOCKED/ABORT）"""
        handlers = {
            "SHIP_IT": self._handle_ship_it,
            "BLOCKED": self._handle_blocked,
            "ABORT": self._handle_abort,
        }
        
        handler = handlers.get(result)
        if handler:
            return handler()
        else:
            raise ValueError(f"Unknown result: {result}")
    
    def _handle_ship_it(self) -> bool:
        """合併並清理"""
        # 1. Push branch
        self._git_push()
        
        # 2. Create/Merge PR
        if self._auto_merge_enabled():
            self._auto_merge()
        else:
            self._create_pr()
        
        # 3. Cleanup
        self._cleanup_worktree()
        self._update_workflow_state("merged")
        
        return True
    
    def _handle_blocked(self) -> bool:
        """保留以便迭代"""
        self._update_workflow_state("blocked")
        # 不刪除 worktree
        return True
    
    def _handle_abort(self) -> bool:
        """詢問保留或刪除"""
        choice = self._prompt_abort_options()
        
        if choice == "preserve_patch":
            self._save_patch()
            self._cleanup_worktree()
        elif choice == "delete_all":
            self._cleanup_worktree()
        elif choice == "lock":
            self._lock_worktree()
        
        self._update_workflow_state("abandoned")
        return True
```

#### 在 Skills 中使用

```python
# skills/verify/handlers.py
from shared.git.worktree_manager import WorktreeManager

def handle_verify_complete(workflow_id: str, result: str):
    """Verify 完成後處理"""
    manager = WorktreeManager(workflow_id)
    
    # CP6.5: Worktree Completion
    success = manager.complete(result)
    
    if success:
        log_checkpoint("CP6.5", "Worktree completion", "success")
    else:
        log_checkpoint("CP6.5", "Worktree completion", "failed")
```

### 3.5 錯誤處理與回退

#### 統一錯誤處理策略

```yaml
Hook 錯誤處理:
  原則: "Fail Graceful, Never Block"
  
  處理層級:
    L1_Critical (阻塞工作流):
      - Worktree 創建失敗
      - State 寫入失敗（檔案鎖超時）
      action: 停止工作流，提示用戶
    
    L2_Important (警告但繼續):
      - Commit 失敗（pre-commit hook）
      - 測試失敗
      action: 記錄警告，繼續工作流
    
    L3_Optional (靜默失敗):
      - Action log 寫入失敗
      - Metrics 記錄失敗
      action: 靜默失敗，不影響工作流
```

#### Rollback 機制

```python
# shared/git/rollback.py
class RollbackManager:
    """統一的 Rollback 管理"""
    
    def rollback_to_checkpoint(self, checkpoint: str):
        """Rollback 到特定 checkpoint"""
        # 1. 找到 checkpoint commit
        commit_hash = self._find_checkpoint_commit(checkpoint)
        
        # 2. 保存當前進度
        self._save_rollback_patch()
        
        # 3. Reset 到 checkpoint
        self._git_reset(commit_hash)
        
        # 4. 更新狀態
        self._update_workflow_state(f"rolled_back_to_{checkpoint}")
```

## 4. 實施計劃

### Phase 1: Hook 系統統一（優先級：高）

```yaml
Tasks:
  1. 重構 templates/hooks/workflow_hooks.py:
    - 改為委派模式，調用 scripts/hooks/
    - 保持統一入口點
    - 測試向後兼容性
  
  2. 刪除重複實作:
    - 移除 templates 中的重複邏輯
    - 統一使用 scripts 版本
  
  3. 更新文檔:
    - 明確說明 hook 架構
    - 更新配置範例
```

### Phase 2: 狀態管理重構（優先級：高）

```yaml
Tasks:
  1. 實作 WorkflowState 抽象層:
    - 檔案鎖機制
    - Schema 驗證
    - 統一 API
  
  2. 遷移現有代碼:
    - 替換所有直接 JSON 讀寫
    - 使用 WorkflowState API
  
  3. 測試並行安全:
    - 模擬並行 hook 觸發
    - 驗證無狀態衝突
```

### Phase 3: Commit 時機優化（優先級：中）

```yaml
Tasks:
  1. 統一 Commit 策略:
    - 實作新的 commit 邏輯
    - 標準化 commit message
  
  2. 更新 hooks:
    - PostToolUse: 只 commit 程式碼
    - SubagentStop: 只 commit memory
    - CP4: Checkpoint commit
  
  3. 回歸測試:
    - 確保 git history 清晰
    - 驗證 rollback 可行性
```

### Phase 4: Worktree 生命週期（優先級：中）

```yaml
Tasks:
  1. 實作 WorktreeManager:
    - create() 方法
    - complete() 方法
    - 錯誤處理
  
  2. 整合到 Skills:
    - PLAN 完成後創建
    - VERIFY 完成後處理
  
  3. 測試端到端:
    - 完整工作流測試
    - 各種結果路徑（SHIP_IT/BLOCKED/ABORT）
```

### Phase 5: 錯誤處理強化（優先級：低）

```yaml
Tasks:
  1. 實作 RollbackManager:
    - Checkpoint rollback
    - Patch 保存
  
  2. 錯誤分級處理:
    - L1/L2/L3 分級
    - 適當的錯誤訊息
  
  3. 監控與告警:
    - Hook 失敗率追蹤
    - 異常狀態偵測
```

## 5. 預期效果

### 5.1 量化指標

```yaml
改進指標:
  程式碼品質:
    重複代碼: -60% (移除 templates 重複實作)
    模組耦合度: -40% (統一狀態管理)
  
  維護成本:
    修改 hook 邏輯時間: -70% (單一入口)
    除錯時間: -50% (統一狀態追蹤)
  
  可靠性:
    狀態不一致風險: -80% (檔案鎖)
    Worktree 孤立風險: -90% (統一管理)
```

### 5.2 質性改善

```yaml
開發體驗:
  - Hook 行為可預測（統一邏輯）
  - 狀態變更可追蹤（統一 API）
  - 錯誤訊息清晰（分級處理）

維護性:
  - 修改一處即可（無重複）
  - 測試更容易（解耦設計）
  - 文檔更準確（實作一致）

擴展性:
  - 新增 hook 簡單（統一模式）
  - 新增狀態欄位安全（schema 驗證）
  - 支援更多工作流（抽象層）
```

## 6. 風險與緩解

### 6.1 向後兼容性風險

**風險**：重構可能破壞現有工作流

**緩解**：
1. 保持統一入口點（templates/hooks/workflow_hooks.py）
2. 漸進式遷移（先委派，再重構）
3. 完整測試覆蓋（integration tests）
4. 版本化 breaking changes

### 6.2 檔案鎖效能風險

**風險**：檔案鎖可能造成 hook 延遲

**緩解**：
1. 使用非阻塞鎖（timeout 機制）
2. 減少持鎖時間（快速讀寫）
3. 監控鎖競爭情況
4. 必要時改用 SQLite（原子性更好）

### 6.3 遷移成本風險

**風險**：重構工作量大，影響開發進度

**緩解**：
1. 分階段實施（5 個 Phase）
2. 優先處理高優先級項目
3. 保持現有功能運作（並行重構）
4. 團隊培訓與文檔更新

## 7. 結論

### 7.1 核心發現

1. **架構分散**是最大痛點：Hook 雙軌制、狀態管理分散
2. **時機混亂**導致行為不一致：不同 hook 版本處理邏輯不同
3. **缺乏抽象**增加維護成本：直接操作檔案，無統一 API

### 7.2 優化價值

通過統一 Hook 系統、集中狀態管理、優化 Commit 時機，可以：
- **降低複雜度**：從雙軌變單軌
- **提升可靠性**：檔案鎖防止狀態衝突
- **改善體驗**：清晰的錯誤訊息、可預測的行為

### 7.3 實施建議

**立即執行**（Phase 1 & 2）：
- 統一 Hook 系統
- 實作 WorkflowState

**短期規劃**（Phase 3 & 4）：
- 優化 Commit 時機
- Worktree 生命週期管理

**長期優化**（Phase 5）：
- 錯誤處理強化
- 監控與告警

### 7.4 成功指標

```yaml
6 個月後驗證:
  - Hook 相關 bug 數量 < 5/月
  - 狀態不一致事件 = 0
  - Worktree 孤立率 < 1%
  - 開發者滿意度 > 8/10
```

---

**撰寫時間**: 2026-02-01  
**分析者**: Workflow Designer Agent  
**版本**: v1.0
