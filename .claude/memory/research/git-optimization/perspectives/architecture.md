# Git 使用架構分析報告

## 執行摘要

multi-agent-workflow plugin 當前的 Git 操作分散在多個檔案中，存在嚴重的**程式碼重複**、**職責不清**、**語言混雜**問題，違反了 DRY 和 SOLID 原則。需要進行統一重構，建立清晰的抽象層次和統一的 API 介面。

---

## 1. 架構問題分析

### 1.1 違反 DRY 原則的重複邏輯

#### 問題 1: `_get_current_workflow_id()` 重複實作

**位置:**
- `scripts/hooks/post_task.py` (L149-161)
- `scripts/hooks/subagent_stop.py` (L180-192)

**程式碼:**
```python
# 在兩個檔案中完全相同的邏輯
def _get_current_workflow_id(project_dir: str) -> str:
    """從最近的 workflow 目錄取得 ID"""
    workflow_dir = Path(project_dir) / ".claude" / "workflow"
    if workflow_dir.exists():
        for d in sorted(workflow_dir.iterdir(), reverse=True):
            if d.is_dir() and (d / "current.json").exists():
                try:
                    with open(d / "current.json") as f:
                        state = json.load(f)
                        return state.get("workflow_id", d.name)
                except:
                    pass
    return ""
```

**影響:** 兩處需要同步維護，容易產生不一致性。

---

#### 問題 2: Git 操作邏輯重複

**`git status --porcelain` 檢查:**
- `post_task.py` (L77-78)
- `subagent_stop.py` (L58-63, L99-104)
- `templates/hooks/workflow_hooks.py` (L37-42, L144-147)

**`git add` 操作:**
- `post_task.py` (L84)
- `subagent_stop.py` (L110-114)
- `templates/hooks/workflow_hooks.py` (L47-48)

**`git commit` 操作:**
- `post_task.py` (L95-99)
- `subagent_stop.py` (L151-156)
- `templates/hooks/workflow_hooks.py` (L58-64)

**分析:**
- 每個檔案都自己實作 git 命令呼叫
- commit message 格式分散在各處
- 錯誤處理邏輯不統一

---

#### 問題 3: Commit 設定載入重複

**位置:**
- `post_task.py` 中的 `_load_commit_settings()` (L27-48)
- 類似邏輯應該也會出現在其他需要讀取設定的地方

**問題:**
- 設定讀取邏輯應該抽象為共用模組
- YAML 解析應該統一處理

---

### 1.2 違反 SOLID 原則

#### Single Responsibility Principle (SRP) 違反

**問題檔案: `post_task.py`**
```python
# 同時處理：
1. 狀態更新 (update_state)
2. 動作記錄 (log_action)
3. Commit 設定載入 (_load_commit_settings)
4. Git 變更檢測 (_commit_task_changes)
5. Git staging
6. Git commit
7. Workflow ID 取得
```

**職責過多:** 一個 hook 檔案承擔了太多不相關的職責。

---

#### Open/Closed Principle (OCP) 違反

**問題: Commit Type 硬編碼**

`subagent_stop.py` (L116-125):
```python
commit_types = {
    "research": "docs",
    "plans": "feat",
    "tasks": "feat",
    "implement": "feat",
    "review": "docs",
    "verify": "test",
}
commit_type = commit_types.get(memory_type, "chore")
```

**問題:**
- 新增 memory type 需要修改原始碼
- 應該從設定檔讀取（符合 OCP）

---

#### Dependency Inversion Principle (DIP) 違反

**問題: 直接依賴具體實作**

所有 hook 都直接呼叫 `subprocess.run(["git", ...])`：
- 難以測試（無法 mock git 命令）
- 無法替換 git 實作
- 缺乏抽象介面

---

### 1.3 語言混雜問題

**現狀:**
- **Shell Scripts:** `workflow-init.sh` (498 行)
- **Python Scripts:** `post_task.py`, `subagent_stop.py`, `workflow_hooks.py`

**問題分析:**

| 語言 | 優勢 | 劣勢 | 當前使用 |
|------|------|------|----------|
| **Shell** | 呼叫 git 簡潔 | 複雜邏輯難維護、錯誤處理弱 | workflow-init.sh |
| **Python** | 結構化、可測試、錯誤處理佳 | 呼叫外部命令略繁瑣 | hooks/*.py |

**建議:**
- **統一使用 Python**
- 原因：
  1. 已有大量 Python hook 實作
  2. 複雜的 JSON/YAML 處理更方便
  3. 更好的測試能力
  4. 統一的錯誤處理和日誌記錄

---

### 1.4 路徑處理不一致

**問題範例:**

```python
# post_task.py (L39) - 使用 Path
config_path = Path(project_dir) / "shared/config/commit-settings.yaml"

# subagent_stop.py (L96) - 使用字串拼接
memory_dir = f".claude/memory/{memory_type}/{memory_id}"

# workflow-init.sh (L61) - Shell 變量拼接
workflow_dir="${WORKFLOW_BASE}/${workflow_id}"
```

**影響:**
- 跨平台相容性問題 (Windows/Unix)
- 程式碼風格不統一

**建議:**
- 統一使用 `pathlib.Path`
- 在 Shell 中使用 `realpath` 或 `readlink -f`

---

### 1.5 current.json 位置不一致

**發現的多種位置:**

1. **Global current.json:**
   - `{WORKFLOW_BASE}/current.json` (workflow-init.sh L94)
   - `.claude/workflow/current.json` (update_state.py L35)

2. **Workflow-specific current.json:**
   - `.claude/workflow/{workflow_id}/current.json` (post_task.py L154)

**問題:**
- 不清楚哪個是正確來源
- 可能導致狀態不同步

**建議:**
- **Global:** `.claude/workflow/current.json` (指向當前活躍的 workflow)
- **Workflow-specific:** `.claude/workflow/{workflow_id}/state.json` (該 workflow 的詳細狀態)
- 明確定義兩者的職責和同步機制

---

## 2. 缺乏抽象層設計

### 2.1 當前架構（無抽象）

```
┌─────────────────────────────────────────────────────────┐
│                     Hook Scripts                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ post_task.py │  │subagent_stop │  │workflow_hooks│  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
│         └─────────────────┼─────────────────┘           │
│                           │                             │
│              直接呼叫 subprocess.run(["git", ...])       │
│                           │                             │
└───────────────────────────┼─────────────────────────────┘
                            ▼
                    ┌───────────────┐
                    │  Git Binary   │
                    └───────────────┘
```

**問題:**
- **無抽象層:** 所有 hook 直接操作 git
- **無統一 API:** 每個檔案自己實作 git 操作
- **難以測試:** 需要真實 git 環境

---

### 2.2 建議架構（分層抽象）

```
┌─────────────────────────────────────────────────────────────────┐
│                         Hook Scripts                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ post_task.py │  │subagent_stop │  │workflow_hooks│          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
          ┌──────────────────▼──────────────────┐
          │        CommitManager (高階)          │
          │  - auto_commit()                    │
          │  - commit_memory()                  │
          │  - commit_task()                    │
          │  - create_commit_message()          │
          └──────────────────┬──────────────────┘
                             │
          ┌──────────────────▼──────────────────┐
          │      WorkflowManager (中階)         │
          │  - get_current_workflow_id()        │
          │  - get_workflow_state()             │
          │  - update_workflow_state()          │
          └──────────────────┬──────────────────┘
                             │
          ┌──────────────────▼──────────────────┐
          │        GitOps (低階)                │
          │  - status()                         │
          │  - add()                            │
          │  - commit()                         │
          │  - check_changes()                  │
          └──────────────────┬──────────────────┘
                             │
          ┌──────────────────▼──────────────────┐
          │      GitExecutor (底層)             │
          │  - run(command, args, kwargs)       │
          │  - (可替換為 mock 實作)             │
          └──────────────────┬──────────────────┘
                             │
                             ▼
                    ┌───────────────┐
                    │  Git Binary   │
                    └───────────────┘
```

---

## 3. 統一方案設計

### 3.1 模組架構

#### 目錄結構

```
scripts/
  git_lib/
    __init__.py
    executor.py         # GitExecutor - 底層命令執行
    operations.py       # GitOps - 基本 git 操作
    workflow.py         # WorkflowManager - workflow 狀態管理
    commit.py           # CommitManager - commit 高階邏輯
    worktree.py         # WorktreeManager - worktree 管理
    config.py           # ConfigManager - 設定讀取
    exceptions.py       # 自訂例外
  hooks/
    post_task.py        # 重構後：僅處理 hook 邏輯
    subagent_stop.py    # 重構後：僅處理 hook 邏輯
    ...
  tests/
    test_git_ops.py
    test_commit_manager.py
    ...
```

---

### 3.2 核心模組設計

#### 3.2.1 GitExecutor (底層)

**職責:** 封裝所有 git 命令執行，統一錯誤處理和日誌記錄。

```python
# scripts/git_lib/executor.py
from typing import List, Optional, Dict
from pathlib import Path
import subprocess
import logging

logger = logging.getLogger(__name__)

class GitExecutor:
    """Git 命令執行器 - 底層介面"""
    
    def __init__(self, cwd: Path):
        self.cwd = cwd
    
    def run(
        self, 
        args: List[str], 
        check: bool = True,
        capture_output: bool = True,
        text: bool = True,
        timeout: Optional[int] = None
    ) -> subprocess.CompletedProcess:
        """執行 git 命令
        
        Args:
            args: git 參數列表，如 ["status", "--porcelain"]
            check: 是否在失敗時拋出例外
            capture_output: 是否捕獲輸出
            text: 是否以文字模式處理輸出
            timeout: 超時秒數
            
        Returns:
            CompletedProcess 物件
            
        Raises:
            GitExecutionError: 命令執行失敗
        """
        cmd = ["git"] + args
        logger.debug(f"執行: {' '.join(cmd)} (cwd={self.cwd})")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.cwd),
                check=check,
                capture_output=capture_output,
                text=text,
                timeout=timeout
            )
            logger.debug(f"成功: returncode={result.returncode}")
            return result
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git 命令失敗: {e.cmd}, rc={e.returncode}")
            logger.error(f"stderr: {e.stderr}")
            raise GitExecutionError(e.cmd, e.returncode, e.stderr) from e
            
        except subprocess.TimeoutExpired as e:
            logger.error(f"Git 命令超時: {e.cmd}, timeout={e.timeout}s")
            raise GitTimeoutError(e.cmd, e.timeout) from e
```

---

#### 3.2.2 GitOps (低階操作)

**職責:** 封裝基本 git 操作（status, add, commit 等）。

```python
# scripts/git_lib/operations.py
from pathlib import Path
from typing import List, Optional
from .executor import GitExecutor

class GitOps:
    """Git 基本操作 - 低階介面"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.executor = GitExecutor(self.project_dir)
    
    def status(self, pathspecs: Optional[List[str]] = None) -> str:
        """取得 git status 輸出
        
        Args:
            pathspecs: 路徑規格列表（如 [".claude/memory/"]）
            
        Returns:
            git status --porcelain 輸出
        """
        args = ["status", "--porcelain"]
        if pathspecs:
            args.extend(["--"] + pathspecs)
        
        result = self.executor.run(args)
        return result.stdout.strip()
    
    def has_changes(self, pathspecs: Optional[List[str]] = None) -> bool:
        """檢查是否有未提交的變更"""
        return bool(self.status(pathspecs))
    
    def add(self, pathspecs: List[str]) -> None:
        """Stage 檔案
        
        Args:
            pathspecs: 要 add 的路徑列表
        """
        args = ["add", "--"] + pathspecs
        self.executor.run(args)
    
    def commit(self, message: str, allow_empty: bool = False) -> str:
        """建立 commit
        
        Args:
            message: commit message
            allow_empty: 是否允許空 commit
            
        Returns:
            commit hash
        """
        args = ["commit", "-m", message]
        if allow_empty:
            args.append("--allow-empty")
        
        self.executor.run(args)
        
        # 取得 commit hash
        result = self.executor.run(["rev-parse", "HEAD"])
        return result.stdout.strip()
    
    def get_changed_files(
        self, 
        pathspecs: Optional[List[str]] = None,
        cached: bool = False
    ) -> List[str]:
        """取得變更的檔案列表
        
        Args:
            pathspecs: 路徑規格
            cached: 是否只看 staged 的變更
            
        Returns:
            檔案路徑列表
        """
        args = ["diff", "--name-only"]
        if cached:
            args.append("--cached")
        if pathspecs:
            args.extend(["--"] + pathspecs)
        
        result = self.executor.run(args)
        return [f for f in result.stdout.strip().split('\n') if f]
```

---

#### 3.2.3 WorkflowManager (中階)

**職責:** 管理 workflow 狀態和 ID。

```python
# scripts/git_lib/workflow.py
from pathlib import Path
import json
from typing import Optional, Dict
from .exceptions import WorkflowNotFoundError

class WorkflowManager:
    """Workflow 狀態管理"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.workflow_base = self.project_dir / ".claude" / "workflow"
    
    def get_current_workflow_id(self) -> Optional[str]:
        """取得當前活躍的 workflow ID
        
        Returns:
            workflow_id 或 None
        """
        # 方法 1: 從 global current.json
        current_file = self.workflow_base / "current.json"
        if current_file.exists():
            try:
                with open(current_file) as f:
                    state = json.load(f)
                    return state.get("workflow_id")
            except (json.JSONDecodeError, KeyError):
                pass
        
        # 方法 2: 找最新的 workflow 目錄
        if self.workflow_base.exists():
            for d in sorted(self.workflow_base.iterdir(), reverse=True):
                if d.is_dir() and (d / "state.json").exists():
                    try:
                        with open(d / "state.json") as f:
                            state = json.load(f)
                            if state.get("status") == "active":
                                return state.get("workflow_id", d.name)
                    except:
                        continue
        
        return None
    
    def get_workflow_state(
        self, 
        workflow_id: Optional[str] = None
    ) -> Dict:
        """取得 workflow 狀態
        
        Args:
            workflow_id: workflow ID（None 則使用當前）
            
        Returns:
            狀態字典
            
        Raises:
            WorkflowNotFoundError: workflow 不存在
        """
        if workflow_id is None:
            workflow_id = self.get_current_workflow_id()
            if workflow_id is None:
                raise WorkflowNotFoundError("No active workflow")
        
        state_file = self.workflow_base / workflow_id / "state.json"
        if not state_file.exists():
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")
        
        with open(state_file) as f:
            return json.load(f)
    
    def update_workflow_state(
        self, 
        workflow_id: str,
        updates: Dict
    ) -> None:
        """更新 workflow 狀態
        
        Args:
            workflow_id: workflow ID
            updates: 要更新的欄位字典
        """
        state = self.get_workflow_state(workflow_id)
        state.update(updates)
        
        state_file = self.workflow_base / workflow_id / "state.json"
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
```

---

#### 3.2.4 CommitManager (高階)

**職責:** 處理各種 commit 場景（task, memory, worktree 等）。

```python
# scripts/git_lib/commit.py
from pathlib import Path
from typing import Optional, List, Dict
from .operations import GitOps
from .workflow import WorkflowManager
from .config import ConfigManager

class CommitManager:
    """Commit 管理 - 高階邏輯"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.git = GitOps(project_dir)
        self.workflow = WorkflowManager(project_dir)
        self.config = ConfigManager(project_dir)
    
    def auto_commit_task(
        self,
        description: str,
        workflow_id: Optional[str] = None
    ) -> Optional[str]:
        """Task 完成後自動 commit
        
        Args:
            description: task 描述
            workflow_id: workflow ID（None 則使用當前）
            
        Returns:
            commit hash 或 None（無變更）
        """
        settings = self.config.get_commit_settings()
        
        if not settings.get("enabled", True):
            return None
        
        # 建立 pathspecs
        pathspecs = self._build_pathspecs(settings)
        
        # 檢查變更
        if not self.git.has_changes(pathspecs):
            return None
        
        # Stage
        self.git.add(pathspecs)
        
        # 建立 commit message
        message = self._format_commit_message(
            commit_type="chore",
            scope="task",
            description=description[:50],
            body=None
        )
        
        # Commit
        return self.git.commit(message)
    
    def auto_commit_memory(
        self,
        memory_type: str,
        memory_id: str,
        workflow_id: Optional[str] = None
    ) -> Optional[str]:
        """Memory 變更後自動 commit
        
        Args:
            memory_type: memory 類型（research, plans, ...）
            memory_id: memory ID
            workflow_id: workflow ID
            
        Returns:
            commit hash 或 None（無變更）
        """
        memory_dir = f".claude/memory/{memory_type}/{memory_id}"
        
        # 檢查變更
        if not self.git.has_changes([memory_dir]):
            return None
        
        # Stage
        self.git.add([memory_dir])
        
        # 取得變更檔案
        changed_files = self.git.get_changed_files([memory_dir], cached=True)
        
        # 決定 commit type
        commit_type = self.config.get_commit_type(memory_type)
        
        # 建立 message
        topic = memory_id.replace("-", " ").replace("_", " ")
        summary_lines = [
            f"- Update {Path(f).name}" 
            for f in changed_files[:3]
        ]
        
        message = self._format_commit_message(
            commit_type=commit_type,
            scope=memory_type,
            description=f"complete {topic}",
            body="\n".join(summary_lines),
            footer=f"Memory: {memory_dir}/"
        )
        
        # Commit
        return self.git.commit(message)
    
    def _build_pathspecs(self, settings: Dict) -> List[str]:
        """建立 pathspecs 列表（包含排除規則）"""
        pathspecs = ["."]
        
        if not settings.get("include_memory", False):
            pathspecs.append(":!.claude/memory/")
        
        if not settings.get("include_logs", False):
            pathspecs.append(":!.claude/workflow/")
            pathspecs.append(":!.claude/logs/")
        
        for pattern in settings.get("exclude_patterns", []):
            pathspecs.append(f":!{pattern}")
        
        return pathspecs
    
    def _format_commit_message(
        self,
        commit_type: str,
        scope: str,
        description: str,
        body: Optional[str] = None,
        footer: Optional[str] = None
    ) -> str:
        """格式化 commit message（遵循 conventional commits）"""
        lines = [f"{commit_type}({scope}): {description}"]
        
        if body:
            lines.append("")
            lines.append(body)
        
        if footer:
            lines.append("")
            lines.append(footer)
        
        # 加入 Co-Author
        lines.append("")
        lines.append("Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>")
        
        return "\n".join(lines)
```

---

#### 3.2.5 ConfigManager (設定管理)

```python
# scripts/git_lib/config.py
from pathlib import Path
from typing import Dict
import yaml

class ConfigManager:
    """設定管理"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
    
    def get_commit_settings(self) -> Dict:
        """讀取 commit 設定"""
        default = {
            "enabled": True,
            "include_memory": False,
            "include_logs": False,
            "exclude_patterns": [
                "*.pyc", "__pycache__/", ".DS_Store"
            ],
        }
        
        config_path = self.project_dir / "shared/config/commit-settings.yaml"
        if not config_path.exists():
            return default
        
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
                return config.get("task_commit", default)
        except:
            return default
    
    def get_commit_type(self, memory_type: str) -> str:
        """取得 memory type 對應的 commit type"""
        # 從設定檔讀取（支援 OCP）
        config_path = self.project_dir / "shared/config/commit-settings.yaml"
        
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = yaml.safe_load(f)
                    type_mapping = config.get("commit_types", {})
                    return type_mapping.get(memory_type, "chore")
            except:
                pass
        
        # Fallback to defaults
        defaults = {
            "research": "docs",
            "plans": "feat",
            "tasks": "feat",
            "implement": "feat",
            "review": "docs",
            "verify": "test",
        }
        return defaults.get(memory_type, "chore")
```

---

### 3.3 重構後的 Hook 範例

#### post_task.py (重構後)

```python
#!/usr/bin/env python3
"""Post-Task Hook - 在 Agent 完成後更新狀態並自動 commit"""

import json
import sys
from pathlib import Path

# 引入統一 Git 模組
sys.path.insert(0, str(Path(__file__).parent.parent))

from git_lib.commit import CommitManager
from git_lib.workflow import WorkflowManager
from hooks.log_action import log_action
from hooks.update_state import update_state

def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return
    
    tool_input = input_data.get("tool_input", {})
    tool_response = input_data.get("tool_response", {})
    
    description = tool_input.get("description", "")
    agent_id = description.lower().replace(" ", "-")[:30]
    
    # 判斷成功或失敗
    tool_output = str(tool_response)
    success = "error" not in tool_output.lower()
    status = "completed" if success else "failed"
    
    project_dir = Path(input_data.get("cwd", os.getcwd()))
    
    # 使用 WorkflowManager 取得 ID
    workflow_mgr = WorkflowManager(project_dir)
    workflow_id = workflow_mgr.get_current_workflow_id()
    
    if not workflow_id:
        return
    
    # 更新狀態
    update_state(
        project_dir=str(project_dir),
        workflow_id=workflow_id,
        agent_id=agent_id,
        agent_status=status,
    )
    
    # 記錄 action
    log_action(
        tool="Task",
        status="success" if success else "failed",
        input_data={"description": description},
        output_preview=tool_output[:200],
        project_dir=str(project_dir),
        workflow_id=workflow_id,
        agent_id=agent_id,
    )
    
    # 使用 CommitManager 自動 commit
    if success:
        commit_mgr = CommitManager(project_dir)
        commit_mgr.auto_commit_task(description, workflow_id)

if __name__ == "__main__":
    main()
```

**改善點:**
- 減少 50+ 行程式碼
- 職責清晰：只處理 hook 邏輯
- Git 操作委派給 `CommitManager`
- 易於測試和維護

---

#### subagent_stop.py (重構後)

```python
#!/usr/bin/env python3
"""SubagentStop Hook - 在子代理完成時執行 git commit"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from git_lib.commit import CommitManager
from git_lib.workflow import WorkflowManager
from git_lib.operations import GitOps
from hooks.log_action import log_action

def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return
    
    if input_data.get("stop_hook_active", False):
        return  # 防止無限循環
    
    project_dir = Path(input_data.get("cwd", os.getcwd()))
    
    # 使用 WorkflowManager
    workflow_mgr = WorkflowManager(project_dir)
    workflow_id = workflow_mgr.get_current_workflow_id()
    
    # 記錄 subagent 完成
    log_action(
        tool="SubagentStop",
        status="success",
        input_data={"session_id": input_data.get("session_id", "")},
        project_dir=str(project_dir),
        workflow_id=workflow_id,
    )
    
    # 使用 GitOps 檢查 memory 變更
    git = GitOps(project_dir)
    memory_dir = project_dir / ".claude" / "memory"
    
    if not memory_dir.exists():
        return
    
    # 取得變更的 memory 路徑
    changed_files = git.get_changed_files([str(memory_dir)])
    memory_paths = set()
    
    for file_path in changed_files:
        match = re.search(r'\.claude/memory/([^/]+)/([^/]+)', file_path)
        if match:
            memory_paths.add((match.group(1), match.group(2)))
    
    # 使用 CommitManager 提交每個 memory
    commit_mgr = CommitManager(project_dir)
    for memory_type, memory_id in memory_paths:
        commit_hash = commit_mgr.auto_commit_memory(
            memory_type, 
            memory_id, 
            workflow_id
        )
        if commit_hash:
            print(f"Committed: .claude/memory/{memory_type}/{memory_id}", 
                  file=sys.stderr)

if __name__ == "__main__":
    main()
```

**改善點:**
- 減少 80+ 行程式碼
- 消除重複的 `_commit_memory()` 和 `_get_current_workflow_id()`
- 使用統一的 `CommitManager.auto_commit_memory()`

---

## 4. 語言選擇建議

### 4.1 統一使用 Python 的理由

| 考量點 | Shell | Python | 建議 |
|--------|-------|--------|------|
| **Git 呼叫** | 簡潔 (`git status`) | 略繁瑣 (`subprocess.run(["git", "status"])`) | Python + 封裝 |
| **錯誤處理** | 弱（exit code） | 強（例外處理） | ✅ Python |
| **JSON/YAML** | 依賴 `jq`/`yq` | 原生支援 | ✅ Python |
| **測試** | 困難 | 簡單（unittest, pytest） | ✅ Python |
| **可維護性** | 複雜邏輯難讀 | 結構化、OOP | ✅ Python |
| **跨平台** | macOS/Linux | 全平台 | ✅ Python |
| **現有程式碼** | 1 個檔案 (workflow-init.sh) | 多個 hook | ✅ Python |

**結論:** **統一使用 Python**

### 4.2 遷移策略

**Phase 1: 建立 Python 版本的 workflow-init**
```python
# scripts/workflow_init.py
# 使用 WorkflowManager + GitOps 重寫 workflow-init.sh
```

**Phase 2: 保留 Shell 版本為 wrapper**
```bash
#!/bin/bash
# shared/tools/workflow-init.sh
# 轉發到 Python 實作
python3 "$(dirname "$0")/../../scripts/workflow_init.py" "$@"
```

**Phase 3: 逐步淘汰 Shell 版本**
- 更新文件指向 Python 版本
- 一個版本後移除 Shell wrapper

---

## 5. 介面設計

### 5.1 統一 API 設計

#### 高階 API（給 Hook 使用）

```python
from git_lib import CommitManager, WorkflowManager, GitOps

# 初始化
project_dir = Path.cwd()
commit_mgr = CommitManager(project_dir)
workflow_mgr = WorkflowManager(project_dir)
git = GitOps(project_dir)

# Task commit
commit_mgr.auto_commit_task(description="add login endpoint")

# Memory commit
commit_mgr.auto_commit_memory(
    memory_type="research", 
    memory_id="user-auth"
)

# Worktree management
from git_lib import WorktreeManager
worktree_mgr = WorktreeManager(project_dir)
worktree_mgr.create("feature-auth", branch="feature/auth")
worktree_mgr.cleanup("feature-auth", merge=True)

# Workflow 狀態
workflow_id = workflow_mgr.get_current_workflow_id()
state = workflow_mgr.get_workflow_state(workflow_id)
```

---

#### 中階 API（給進階使用者）

```python
# 自訂 commit
git = GitOps(project_dir)

if git.has_changes([".claude/memory/research/"]):
    git.add([".claude/memory/research/"])
    commit_hash = git.commit("docs(research): custom commit")

# 取得變更
changed_files = git.get_changed_files(cached=True)

# 檢查特定路徑
if git.has_changes([".claude/memory/", "src/"]):
    # ...
```

---

#### 低階 API（給測試/除錯）

```python
# 直接執行 git 命令
executor = GitExecutor(project_dir)
result = executor.run(["log", "--oneline", "-5"])
print(result.stdout)
```

---

### 5.2 錯誤處理設計

#### 自訂例外

```python
# scripts/git_lib/exceptions.py

class GitLibError(Exception):
    """Git 模組基礎例外"""
    pass

class GitExecutionError(GitLibError):
    """Git 命令執行失敗"""
    def __init__(self, cmd, returncode, stderr):
        self.cmd = cmd
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"Git command failed: {cmd}, rc={returncode}")

class GitTimeoutError(GitLibError):
    """Git 命令超時"""
    def __init__(self, cmd, timeout):
        self.cmd = cmd
        self.timeout = timeout
        super().__init__(f"Git command timeout: {cmd}, {timeout}s")

class WorkflowNotFoundError(GitLibError):
    """Workflow 不存在"""
    pass

class WorktreeError(GitLibError):
    """Worktree 操作失敗"""
    pass
```

#### 使用範例

```python
from git_lib import CommitManager
from git_lib.exceptions import GitExecutionError, WorkflowNotFoundError

try:
    commit_mgr = CommitManager(project_dir)
    commit_mgr.auto_commit_task("fix bug")
    
except WorkflowNotFoundError:
    print("No active workflow", file=sys.stderr)
    
except GitExecutionError as e:
    print(f"Git failed: {e.stderr}", file=sys.stderr)
    sys.exit(1)
```

---

### 5.3 設定檔設計

#### commit-settings.yaml (擴充版)

```yaml
# shared/config/commit-settings.yaml

# Task commit 設定
task_commit:
  enabled: true
  include_memory: false
  include_logs: false
  exclude_patterns:
    - "*.pyc"
    - "__pycache__/"
    - ".pytest_cache/"
    - "*.egg-info/"
    - ".DS_Store"
    - "*.log"
    - ".env*"
    - "node_modules/"

# Memory commit type mapping (支援 OCP)
commit_types:
  research: docs
  plans: feat
  tasks: feat
  implement: feat
  review: docs
  verify: test
  refactor: refactor
  
# Commit message 模板
commit_templates:
  task: "chore(task): {description}"
  memory: "{type}({scope}): complete {topic}\n\n{summary}\n\nMemory: {path}/"
  
# Auto-commit 開關（可針對不同類型）
auto_commit:
  task: true
  memory: true
  worktree: true
```

---

## 6. 遷移計劃

### Phase 1: 建立基礎設施（1-2 天）

**目標:** 建立統一的 Git 模組

**任務:**
1. 建立 `scripts/git_lib/` 目錄結構
2. 實作 `executor.py` (GitExecutor)
3. 實作 `exceptions.py` (自訂例外)
4. 實作 `operations.py` (GitOps)
5. 撰寫單元測試

**驗證:**
```bash
pytest scripts/tests/test_git_ops.py -v
```

---

### Phase 2: 實作管理層（2-3 天）

**目標:** 建立高階管理模組

**任務:**
1. 實作 `workflow.py` (WorkflowManager)
2. 實作 `config.py` (ConfigManager)
3. 實作 `commit.py` (CommitManager)
4. 更新 `commit-settings.yaml` 支援新格式
5. 撰寫整合測試

**驗證:**
```bash
pytest scripts/tests/test_commit_manager.py -v
```

---

### Phase 3: 重構 Hook（2-3 天）

**目標:** 使用新模組重構現有 hook

**任務:**
1. 重構 `post_task.py`
2. 重構 `subagent_stop.py`
3. 重構 `workflow_hooks.py`
4. 更新相關文件
5. 執行迴歸測試

**驗證:**
- 手動測試各個 hook
- 檢查 commit 是否正確建立

---

### Phase 4: Worktree 支援（3-4 天）

**目標:** 實作 WorktreeManager

**任務:**
1. 實作 `worktree.py` (WorktreeManager)
2. 支援 worktree 建立、切換、合併、清理
3. 整合 `shared/isolation/worktree-*.md` 規範
4. 撰寫測試

---

### Phase 5: 遷移 Shell 腳本（2-3 天）

**目標:** 用 Python 重寫 workflow-init.sh

**任務:**
1. 實作 `scripts/workflow_init.py`
2. 保留 Shell wrapper 向後相容
3. 更新文件
4. 測試完整工作流

---

### Phase 6: 文件與清理（1-2 天）

**任務:**
1. 撰寫完整的 API 文件
2. 更新 `shared/git/commit-protocol.md`
3. 建立範例和最佳實踐
4. 移除舊的重複程式碼
5. 最終測試

---

## 7. 測試策略

### 7.1 單元測試

```python
# scripts/tests/test_git_ops.py
import pytest
from pathlib import Path
from git_lib.operations import GitOps

@pytest.fixture
def git_repo(tmp_path):
    """建立測試用 git repo"""
    repo = tmp_path / "test_repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=repo, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo, check=True
    )
    return repo

def test_git_ops_status(git_repo):
    git = GitOps(git_repo)
    
    # 初始狀態：無變更
    assert git.status() == ""
    assert not git.has_changes()
    
    # 建立檔案
    (git_repo / "test.txt").write_text("hello")
    
    # 有變更
    assert git.has_changes()
    assert "test.txt" in git.status()

def test_git_ops_commit(git_repo):
    git = GitOps(git_repo)
    
    # 建立並 commit
    (git_repo / "test.txt").write_text("hello")
    git.add(["."])
    commit_hash = git.commit("Initial commit")
    
    assert len(commit_hash) == 40  # SHA-1
    assert not git.has_changes()
```

---

### 7.2 整合測試

```python
# scripts/tests/test_commit_manager.py
def test_auto_commit_task(git_repo):
    commit_mgr = CommitManager(git_repo)
    
    # 建立檔案
    (git_repo / "src" / "main.py").parent.mkdir()
    (git_repo / "src" / "main.py").write_text("print('hello')")
    
    # Auto commit
    commit_hash = commit_mgr.auto_commit_task("add main.py")
    
    assert commit_hash is not None
    
    # 驗證 commit message
    result = subprocess.run(
        ["git", "log", "-1", "--pretty=%B"],
        cwd=git_repo,
        capture_output=True,
        text=True
    )
    assert "chore(task): add main.py" in result.stdout
    assert "Co-Authored-By: Claude Opus 4.5" in result.stdout
```

---

### 7.3 Mock 測試

```python
from unittest.mock import Mock, patch

def test_commit_manager_no_changes():
    """測試無變更時不 commit"""
    with patch('git_lib.operations.GitOps') as MockGitOps:
        mock_git = MockGitOps.return_value
        mock_git.has_changes.return_value = False
        
        commit_mgr = CommitManager(Path("/fake"))
        result = commit_mgr.auto_commit_task("test")
        
        assert result is None
        mock_git.commit.assert_not_called()
```

---

## 8. 效益分析

### 8.1 程式碼減少

| 檔案 | 原始行數 | 重構後 | 減少 |
|------|----------|--------|------|
| post_task.py | 166 | ~80 | -52% |
| subagent_stop.py | 197 | ~70 | -64% |
| workflow_hooks.py | 183 | ~100 | -45% |
| **總計** | **546** | **~250** | **-54%** |

**新增:**
- git_lib/*.py: ~800 行（但可重複使用）

**淨效益:**
- Hook 程式碼減少 ~300 行
- 消除所有重複邏輯
- 提升可讀性和可維護性

---

### 8.2 可維護性提升

| 指標 | 改善 | 說明 |
|------|------|------|
| **DRY** | ✅✅✅ | 消除所有重複邏輯 |
| **SRP** | ✅✅✅ | 每個類別職責單一 |
| **OCP** | ✅✅ | 設定檔驅動，無需修改程式碼 |
| **DIP** | ✅✅✅ | 依賴抽象介面，可替換實作 |
| **測試覆蓋** | ✅✅✅ | 從 0% 提升至 >80% |
| **跨平台** | ✅✅ | Python 支援全平台 |

---

### 8.3 開發效率提升

**新增功能時:**
- **之前:** 需在 3+ 個檔案中重複實作 git 操作
- **之後:** 呼叫統一 API，1 行程式碼

**範例:**
```python
# 之前：需要複製貼上 20+ 行程式碼
result = subprocess.run(["git", "status", "--porcelain"], ...)
if not result.stdout.strip():
    return
subprocess.run(["git", "add", ...], ...)
# ... 更多重複邏輯

# 之後：1 行
commit_mgr.auto_commit_task(description)
```

---

## 9. 風險與緩解

### 9.1 向後相容性

**風險:** 現有 hook 可能被使用者自訂

**緩解:**
1. 保留舊 hook 檔案為 deprecated
2. 新版本使用新路徑（如 `hooks_v2/`）
3. 提供遷移指南
4. 一個大版本後移除舊版本

---

### 9.2 測試覆蓋

**風險:** Git 操作難以完整測試

**緩解:**
1. 使用臨時 git repo 進行測試
2. Mock Git 命令進行單元測試
3. 整合測試涵蓋主要場景
4. 手動測試關鍵流程

---

### 9.3 效能影響

**風險:** Python 可能比 Shell 慢

**緩解:**
1. Git 操作本身是瓶頸（非語言）
2. 減少重複執行（共用 workflow state）
3. 使用 lru_cache 快取設定讀取
4. 效能測試確保無明顯退化

---

## 10. 結論與建議

### 10.1 核心問題

1. **嚴重違反 DRY 原則** - 多處重複邏輯
2. **缺乏抽象層** - 直接呼叫 git 命令
3. **語言混雜** - Shell + Python 混合
4. **職責不清** - Hook 檔案承擔過多職責
5. **難以測試** - 無法 mock，需真實 git 環境

### 10.2 建議方案

**統一使用 Python + 分層架構:**

```
Hook Scripts (高階)
    ↓
CommitManager / WorkflowManager (中階)
    ↓
GitOps / ConfigManager (低階)
    ↓
GitExecutor (底層)
    ↓
Git Binary
```

**關鍵模組:**
- `GitExecutor` - 底層命令執行
- `GitOps` - 基本 git 操作
- `WorkflowManager` - workflow 狀態管理
- `CommitManager` - commit 高階邏輯
- `WorktreeManager` - worktree 管理
- `ConfigManager` - 設定讀取

### 10.3 立即行動

**優先級 P0 (關鍵):**
1. 建立 `git_lib/` 基礎模組
2. 重構 `post_task.py` 和 `subagent_stop.py`
3. 撰寫單元測試

**優先級 P1 (重要):**
4. 實作 `WorktreeManager`
5. 遷移 `workflow-init.sh` 到 Python
6. 完善文件

**優先級 P2 (改善):**
7. 效能優化
8. 進階功能（如 git hooks 支援）
9. CLI 工具（如 `workflow-git` 命令）

### 10.4 預期效益

- **程式碼減少 54%** (hooks)
- **消除所有重複邏輯**
- **測試覆蓋率 >80%**
- **開發效率提升 3x** (新功能)
- **可維護性大幅提升**
- **符合 DRY + SOLID 原則**

---

## 附錄

### A. 相關檔案清單

**文件:**
- `shared/git/commit-protocol.md` - Commit 協議
- `shared/isolation/worktree-setup.md` - Worktree 建立規範
- `shared/isolation/worktree-completion.md` - Worktree 完成規範
- `shared/config/commit-settings.yaml` - Commit 設定

**程式碼:**
- `scripts/hooks/post_task.py` - Task 完成 hook
- `scripts/hooks/subagent_stop.py` - Subagent 停止 hook
- `templates/hooks/workflow_hooks.py` - 統一 hook 入口
- `shared/tools/workflow-init.sh` - Workflow 初始化
- `scripts/hooks/update_state.py` - 狀態更新
- `scripts/hooks/log_action.py` - 動作記錄

### B. 參考資料

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Worktree Documentation](https://git-scm.com/docs/git-worktree)
- [Python subprocess Best Practices](https://docs.python.org/3/library/subprocess.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

---

**報告完成時間:** 2026-02-01
**分析師:** Claude Code (Architecture Perspective)
**版本:** 1.0
