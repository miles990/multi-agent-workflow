# Git 使用優化實作計劃

> multi-agent-workflow plugin Git 使用優化完整實作計劃

**計劃日期**: 2026-02-01
**基於研究**: [git-optimization 研究報告](../research/git-optimization/synthesis.md)
**設計原則**: 完美、優雅、可靠性、可維護性、可擴充性、可移植性、DRY、SOLID

---

## 1. 目標

### 1.1 核心目標

1. **消除 DRY 違反**：統一所有重複的 Git 操作邏輯
2. **建立抽象層**：分層架構，職責分離
3. **統一 Hook 系統**：整合 templates/ 和 scripts/hooks/
4. **提升可測試性**：從 0% 到 80%+ 測試覆蓋
5. **改善可維護性**：減少 54% Hook 代碼量

### 1.2 設計原則遵循

| 原則 | 目標 |
|------|------|
| DRY | 消除 65 行重複的 `_get_current_workflow_id()` |
| SRP | 每個類別單一職責 |
| OCP | 配置驅動，新增 commit type 不需改代碼 |
| DIP | 依賴抽象介面，易於測試和替換 |

---

## 2. 架構設計

### 2.1 模組結構

```
scripts/
├── git_lib/                      # 統一 Git 操作模組
│   ├── __init__.py               # 匯出公開 API
│   ├── exceptions.py             # 自訂例外
│   ├── executor.py               # GitExecutor - 底層命令執行
│   ├── operations.py             # GitOps - 基本 Git 操作
│   ├── context.py                # WorkflowContext - Workflow 狀態
│   ├── config.py                 # ConfigManager - 設定讀取
│   ├── commit.py                 # CommitManager - Commit 業務邏輯
│   ├── worktree.py               # WorktreeManager - Worktree 管理
│   └── facade.py                 # WorkflowCommitFacade - 簡化入口
├── hooks/
│   ├── post_task.py              # 重構：使用 git_lib
│   ├── subagent_stop.py          # 重構：使用 git_lib
│   ├── update_state.py           # 保持不變
│   └── log_action.py             # 保持不變
└── tests/
    ├── test_git_executor.py
    ├── test_git_ops.py
    ├── test_workflow_context.py
    ├── test_commit_manager.py
    └── test_integration.py
```

### 2.2 類別關係圖

```
┌─────────────────────────────────────────────────────────────────┐
│                         使用者層                                 │
│  post_task.py | subagent_stop.py | workflow_hooks.py            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   WorkflowCommitFacade                           │
│  簡化入口，封裝複雜性                                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ + auto_commit_after_task(description, success)           │  │
│  │ + auto_commit_memory(memory_type, memory_id)             │  │
│  │ + get_workflow_id() -> str                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
┌───────────────────────────┐ ┌───────────────────────────┐
│     CommitManager          │ │    WorkflowContext        │
│ 業務邏輯層                  │ │ 狀態管理層                 │
│ ┌───────────────────────┐ │ │ ┌───────────────────────┐ │
│ │ + commit_task()       │ │ │ │ + get_workflow_id()   │ │
│ │ + commit_memory()     │ │ │ │ + get_commit_type()   │ │
│ │ + build_pathspecs()   │ │ │ │ + get_workflow_state()│ │
│ └───────────────────────┘ │ │ └───────────────────────┘ │
└───────────────────────────┘ └───────────────────────────┘
            │                           │
            ▼                           ▼
┌───────────────────────────┐ ┌───────────────────────────┐
│       GitOps               │ │    ConfigManager          │
│ 基本操作層                  │ │ 設定管理層                 │
│ ┌───────────────────────┐ │ │ ┌───────────────────────┐ │
│ │ + has_changes()       │ │ │ │ + get_commit_settings│ │
│ │ + stage()             │ │ │ │ + get_commit_type()  │ │
│ │ + commit()            │ │ │ │ + get_co_author()    │ │
│ │ + get_changed_files() │ │ │ └───────────────────────┘ │
│ └───────────────────────┘ │ └───────────────────────────┘
└───────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────┐
│                         GitExecutor                            │
│ 底層命令執行層                                                   │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ + run(args, check, capture_output, timeout) -> Result     │ │
│ │ 統一錯誤處理、日誌記錄                                       │ │
│ └───────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
            │
            ▼
      subprocess.run(["git", ...])
```

---

## 3. 詳細設計

### 3.1 exceptions.py

```python
"""自訂例外類別"""

class GitLibError(Exception):
    """Git 模組基礎例外"""
    pass

class GitExecutionError(GitLibError):
    """Git 命令執行失敗"""
    def __init__(self, cmd: list, returncode: int, stderr: str):
        self.cmd = cmd
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"Git command failed: {' '.join(cmd)}, rc={returncode}")

class GitTimeoutError(GitLibError):
    """Git 命令超時"""
    def __init__(self, cmd: list, timeout: int):
        self.cmd = cmd
        self.timeout = timeout
        super().__init__(f"Git command timeout: {' '.join(cmd)}, {timeout}s")

class WorkflowNotFoundError(GitLibError):
    """Workflow 不存在"""
    pass

class WorktreeError(GitLibError):
    """Worktree 操作失敗"""
    pass
```

### 3.2 executor.py

```python
"""Git 命令執行器"""
import subprocess
import logging
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from .exceptions import GitExecutionError, GitTimeoutError

logger = logging.getLogger(__name__)

@dataclass
class GitResult:
    """Git 命令執行結果"""
    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.returncode == 0

class GitExecutor:
    """Git 命令執行器 - 統一底層介面"""

    def __init__(self, cwd: Path):
        self.cwd = Path(cwd)

    def run(
        self,
        args: List[str],
        check: bool = False,
        capture_output: bool = True,
        text: bool = True,
        timeout: Optional[int] = 60
    ) -> GitResult:
        """執行 git 命令

        Args:
            args: git 參數列表，如 ["status", "--porcelain"]
            check: 是否在失敗時拋出例外
            capture_output: 是否捕獲輸出
            text: 是否以文字模式處理輸出
            timeout: 超時秒數

        Returns:
            GitResult 物件

        Raises:
            GitExecutionError: 當 check=True 且命令失敗
            GitTimeoutError: 命令超時
        """
        cmd = ["git"] + args
        logger.debug(f"執行: {' '.join(cmd)} (cwd={self.cwd})")

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.cwd),
                capture_output=capture_output,
                text=text,
                timeout=timeout
            )

            git_result = GitResult(
                returncode=result.returncode,
                stdout=result.stdout if hasattr(result, 'stdout') else "",
                stderr=result.stderr if hasattr(result, 'stderr') else ""
            )

            if check and not git_result.success:
                raise GitExecutionError(cmd, result.returncode, git_result.stderr)

            return git_result

        except subprocess.TimeoutExpired as e:
            raise GitTimeoutError(cmd, timeout) from e
```

### 3.3 operations.py

```python
"""Git 基本操作"""
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from .executor import GitExecutor, GitResult
from .exceptions import GitExecutionError

@dataclass
class CommitResult:
    """Commit 結果"""
    success: bool
    commit_hash: Optional[str] = None
    error: Optional[str] = None

class GitOps:
    """Git 基本操作 - 封裝常用命令"""

    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.executor = GitExecutor(self.project_dir)

    def has_changes(self, pathspecs: Optional[List[str]] = None) -> bool:
        """檢查是否有未提交的變更"""
        args = ["status", "--porcelain"]
        if pathspecs:
            args.extend(["--"] + pathspecs)

        result = self.executor.run(args)
        return bool(result.stdout.strip())

    def stage(self, pathspecs: List[str]) -> None:
        """Stage 檔案"""
        args = ["add", "--"] + pathspecs
        self.executor.run(args, check=True)

    def commit(self, message: str) -> CommitResult:
        """建立 commit"""
        result = self.executor.run(["commit", "-m", message])

        if result.success:
            # 取得 commit hash
            hash_result = self.executor.run(["rev-parse", "HEAD"])
            return CommitResult(
                success=True,
                commit_hash=hash_result.stdout.strip()
            )
        else:
            return CommitResult(
                success=False,
                error=result.stderr
            )

    def get_changed_files(
        self,
        pathspecs: Optional[List[str]] = None,
        cached: bool = False
    ) -> List[str]:
        """取得變更的檔案列表"""
        args = ["diff", "--name-only"]
        if cached:
            args.append("--cached")
        if pathspecs:
            args.extend(["--"] + pathspecs)

        result = self.executor.run(args)
        return [f for f in result.stdout.strip().split('\n') if f]

    def get_status(self, pathspecs: Optional[List[str]] = None) -> str:
        """取得 git status 輸出"""
        args = ["status", "--porcelain"]
        if pathspecs:
            args.extend(["--"] + pathspecs)

        result = self.executor.run(args)
        return result.stdout.strip()
```

### 3.4 context.py

```python
"""Workflow 狀態管理"""
import json
from pathlib import Path
from typing import Optional, Dict

from .exceptions import WorkflowNotFoundError

class WorkflowContext:
    """Workflow 狀態管理 - 統一 workflow 相關操作"""

    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.workflow_base = self.project_dir / ".claude" / "workflow"

    def get_current_workflow_id(self) -> Optional[str]:
        """取得當前活躍的 workflow ID

        這是統一的實作，取代之前分散在 5 個 hook 中的重複代碼。

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
                if d.is_dir() and not d.name.startswith(('_', '.')):
                    state_file = d / "current.json"
                    if state_file.exists():
                        try:
                            with open(state_file) as f:
                                state = json.load(f)
                                if state.get("status") != "completed":
                                    return state.get("workflow_id", d.name)
                        except (json.JSONDecodeError, KeyError):
                            continue

        return None

    def get_workflow_state(self, workflow_id: Optional[str] = None) -> Dict:
        """取得 workflow 狀態"""
        if workflow_id is None:
            workflow_id = self.get_current_workflow_id()
            if workflow_id is None:
                raise WorkflowNotFoundError("No active workflow")

        state_file = self.workflow_base / workflow_id / "current.json"
        if not state_file.exists():
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

        with open(state_file) as f:
            return json.load(f)
```

### 3.5 config.py

```python
"""設定管理"""
from pathlib import Path
from typing import Dict
from functools import lru_cache

try:
    import yaml
except ImportError:
    yaml = None

class ConfigManager:
    """設定管理 - 統一讀取和快取設定"""

    # Co-Author 常數（統一定義，消除重複）
    CO_AUTHOR = "Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

    # 預設 commit type 映射
    DEFAULT_COMMIT_TYPES = {
        "research": "docs",
        "plans": "feat",
        "tasks": "feat",
        "implement": "feat",
        "review": "docs",
        "verify": "test",
    }

    # 預設排除模式
    DEFAULT_EXCLUDE_PATTERNS = [
        "*.pyc",
        "__pycache__/",
        ".pytest_cache/",
        "*.egg-info/",
        ".DS_Store",
        "*.log",
        ".env*",
        "node_modules/",
    ]

    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)

    @lru_cache(maxsize=1)
    def get_commit_settings(self) -> Dict:
        """讀取 commit 設定（帶快取）"""
        default = {
            "enabled": True,
            "include_memory": False,
            "include_logs": False,
            "exclude_patterns": self.DEFAULT_EXCLUDE_PATTERNS.copy(),
        }

        if yaml is None:
            return default

        config_path = self.project_dir / "shared/config/commit-settings.yaml"
        if not config_path.exists():
            return default

        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
                return config.get("task_commit", default)
        except Exception:
            return default

    def get_commit_type(self, memory_type: str) -> str:
        """取得 memory type 對應的 commit type"""
        # 嘗試從設定檔讀取
        if yaml:
            config_path = self.project_dir / "shared/config/commit-settings.yaml"
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        config = yaml.safe_load(f)
                        type_mapping = config.get("commit_types", {})
                        if memory_type in type_mapping:
                            return type_mapping[memory_type]
                except Exception:
                    pass

        return self.DEFAULT_COMMIT_TYPES.get(memory_type, "chore")

    def get_co_author(self) -> str:
        """取得 Co-Author 字串"""
        return self.CO_AUTHOR
```

### 3.6 commit.py

```python
"""Commit 業務邏輯"""
from pathlib import Path
from typing import Optional, List, Dict

from .operations import GitOps, CommitResult
from .context import WorkflowContext
from .config import ConfigManager

class CommitManager:
    """Commit 管理 - 高階業務邏輯"""

    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.git = GitOps(project_dir)
        self.context = WorkflowContext(project_dir)
        self.config = ConfigManager(project_dir)

    def commit_task_changes(
        self,
        description: str,
        include_memory: bool = False,
        include_logs: bool = False,
        exclude_patterns: Optional[List[str]] = None
    ) -> Optional[CommitResult]:
        """Task 完成後自動 commit

        Args:
            description: task 描述
            include_memory: 是否包含 .claude/memory/
            include_logs: 是否包含 .claude/workflow/ 和 logs
            exclude_patterns: 額外排除模式

        Returns:
            CommitResult 或 None（無變更）
        """
        # 建立 pathspecs
        pathspecs = self._build_pathspecs(
            include_memory,
            include_logs,
            exclude_patterns or []
        )

        # 檢查變更
        if not self.git.has_changes(pathspecs):
            return None

        # Stage
        self.git.stage(pathspecs)

        # 建立 commit message
        task_summary = description[:50] if description else "task completed"
        message = self._format_message(
            commit_type="chore",
            scope="task",
            description=task_summary
        )

        # Commit
        return self.git.commit(message)

    def commit_memory_changes(
        self,
        memory_type: str,
        memory_id: str
    ) -> Optional[CommitResult]:
        """Memory 變更後自動 commit

        Args:
            memory_type: memory 類型（research, plans, ...）
            memory_id: memory ID

        Returns:
            CommitResult 或 None（無變更）
        """
        memory_dir = f".claude/memory/{memory_type}/{memory_id}"

        # 檢查變更
        if not self.git.has_changes([memory_dir]):
            return None

        # Stage
        self.git.stage([memory_dir])

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
        if len(changed_files) > 3:
            summary_lines.append(f"- ... and {len(changed_files) - 3} more files")

        message = self._format_message(
            commit_type=commit_type,
            scope=memory_type,
            description=f"complete {topic}",
            body="\n".join(summary_lines),
            footer=f"Memory: {memory_dir}/"
        )

        # Commit
        return self.git.commit(message)

    def _build_pathspecs(
        self,
        include_memory: bool,
        include_logs: bool,
        exclude_patterns: List[str]
    ) -> List[str]:
        """建立 pathspec 列表"""
        pathspecs = ["."]

        if not include_memory:
            pathspecs.append(":!.claude/memory/")

        if not include_logs:
            pathspecs.append(":!.claude/workflow/")
            pathspecs.append(":!.claude/logs/")

        for pattern in exclude_patterns:
            pathspecs.append(f":!{pattern}")

        return pathspecs

    def _format_message(
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
        lines.append(self.config.get_co_author())

        return "\n".join(lines)
```

### 3.7 facade.py

```python
"""簡化入口 - Facade 模式"""
from pathlib import Path
from typing import Optional

from .operations import CommitResult
from .commit import CommitManager
from .context import WorkflowContext
from .config import ConfigManager

class WorkflowCommitFacade:
    """Workflow Commit 統一入口

    提供簡化的 API，隱藏內部複雜性。
    Hooks 只需要使用這個類別即可完成所有 Git 操作。
    """

    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.context = WorkflowContext(project_dir)
        self.config = ConfigManager(project_dir)
        self._commit_manager = None

    @property
    def commit_manager(self) -> CommitManager:
        """延遲初始化 CommitManager"""
        if self._commit_manager is None:
            self._commit_manager = CommitManager(self.project_dir)
        return self._commit_manager

    def get_workflow_id(self) -> Optional[str]:
        """取得當前 workflow ID"""
        return self.context.get_current_workflow_id()

    def auto_commit_after_task(
        self,
        description: str,
        success: bool
    ) -> Optional[CommitResult]:
        """Task 完成後自動 commit

        這是 post_task hook 的簡化入口。

        Args:
            description: task 描述
            success: task 是否成功

        Returns:
            CommitResult 或 None
        """
        if not success:
            return None

        settings = self.config.get_commit_settings()
        if not settings.get("enabled", True):
            return None

        return self.commit_manager.commit_task_changes(
            description=description,
            include_memory=settings.get("include_memory", False),
            include_logs=settings.get("include_logs", False),
            exclude_patterns=settings.get("exclude_patterns", [])
        )

    def auto_commit_memory(
        self,
        memory_type: str,
        memory_id: str
    ) -> Optional[CommitResult]:
        """Memory 變更自動 commit

        這是 subagent_stop hook 的簡化入口。

        Args:
            memory_type: memory 類型
            memory_id: memory ID

        Returns:
            CommitResult 或 None
        """
        return self.commit_manager.commit_memory_changes(
            memory_type=memory_type,
            memory_id=memory_id
        )
```

### 3.8 __init__.py

```python
"""Git 操作統一模組

使用範例：
    from git_lib import WorkflowCommitFacade

    facade = WorkflowCommitFacade(project_dir)
    facade.auto_commit_after_task(description, success)

進階使用：
    from git_lib import GitOps, CommitManager, WorkflowContext

    git = GitOps(project_dir)
    if git.has_changes():
        git.stage(["."])
        git.commit("message")
"""

from .exceptions import (
    GitLibError,
    GitExecutionError,
    GitTimeoutError,
    WorkflowNotFoundError,
    WorktreeError,
)
from .executor import GitExecutor, GitResult
from .operations import GitOps, CommitResult
from .context import WorkflowContext
from .config import ConfigManager
from .commit import CommitManager
from .facade import WorkflowCommitFacade

__all__ = [
    # Exceptions
    "GitLibError",
    "GitExecutionError",
    "GitTimeoutError",
    "WorkflowNotFoundError",
    "WorktreeError",
    # Core
    "GitExecutor",
    "GitResult",
    "GitOps",
    "CommitResult",
    # Business Logic
    "WorkflowContext",
    "ConfigManager",
    "CommitManager",
    # Facade
    "WorkflowCommitFacade",
]
```

---

## 4. Hook 重構範例

### 4.1 重構後的 post_task.py

```python
#!/usr/bin/env python3
"""Post-Task Hook - 在 Agent 完成後更新狀態並自動 commit

重構版本：使用 git_lib 統一模組
"""

import json
import os
import sys
from pathlib import Path

# 加入 git_lib 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from git_lib import WorkflowCommitFacade
from update_state import update_state
from log_action import log_action


def main():
    # 讀取輸入
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    # 解析參數
    project_dir = Path(input_data.get("cwd", os.getcwd()))
    tool_input = input_data.get("tool_input", {})
    tool_response = input_data.get("tool_response", {})

    description = tool_input.get("description", "")
    agent_id = description.lower().replace(" ", "-")[:30]

    # 判斷成功或失敗
    tool_output = str(tool_response)
    success = "error" not in tool_output.lower() and "failed" not in tool_output.lower()
    status = "completed" if success else "failed"

    # 使用統一 Facade
    facade = WorkflowCommitFacade(project_dir)
    workflow_id = facade.get_workflow_id()

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
        output_preview=tool_output[:200] if tool_output else None,
        project_dir=str(project_dir),
        workflow_id=workflow_id,
        agent_id=agent_id,
    )

    # 自動 commit（使用 Facade 簡化 API）
    result = facade.auto_commit_after_task(description, success)

    if result and result.success:
        print(f"✅ Auto-committed: {result.commit_hash[:8]}", file=sys.stderr)


if __name__ == "__main__":
    main()
```

**對比**：
- 原本：166 行
- 重構後：~65 行
- **減少 61%**

### 4.2 重構後的 subagent_stop.py

```python
#!/usr/bin/env python3
"""SubagentStop Hook - 在子代理完成時執行 git commit

重構版本：使用 git_lib 統一模組
"""

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from git_lib import WorkflowCommitFacade, GitOps
from log_action import log_action


def main():
    # 讀取輸入
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    # 防止無限循環
    if input_data.get("stop_hook_active", False):
        return

    project_dir = Path(input_data.get("cwd", os.getcwd()))
    session_id = input_data.get("session_id", "")

    # 使用統一 Facade
    facade = WorkflowCommitFacade(project_dir)
    workflow_id = facade.get_workflow_id()

    # 記錄 subagent 完成
    log_action(
        tool="SubagentStop",
        status="success",
        input_data={"session_id": session_id},
        project_dir=str(project_dir),
        workflow_id=workflow_id or "",
    )

    # 檢查 memory 變更
    memory_dir = project_dir / ".claude" / "memory"
    if not memory_dir.exists():
        return

    # 使用 GitOps 取得變更
    git = GitOps(project_dir)
    status_output = git.get_status([str(memory_dir)])

    if not status_output:
        return

    # 解析變更的 memory 路徑
    memory_paths = set()
    for line in status_output.split('\n'):
        if not line:
            continue
        # 格式: " M path/to/file" 或 "?? path/to/file"
        parts = line.split()
        if len(parts) >= 2:
            file_path = parts[-1]
            match = re.search(r'\.claude/memory/([^/]+)/([^/]+)', file_path)
            if match:
                memory_paths.add((match.group(1), match.group(2)))

    # 對每個 memory 路徑執行 commit
    for memory_type, memory_id in memory_paths:
        result = facade.auto_commit_memory(memory_type, memory_id)

        if result and result.success:
            print(
                f"Committed: .claude/memory/{memory_type}/{memory_id}",
                file=sys.stderr
            )


if __name__ == "__main__":
    main()
```

**對比**：
- 原本：197 行
- 重構後：~80 行
- **減少 59%**

### 4.3 整合 workflow_hooks.py

```python
#!/usr/bin/env python3
"""Workflow Hooks - 統一的 hook 處理入口

使用委派模式，將請求轉發到 scripts/hooks/ 的完整實作。
"""

import json
import sys
from pathlib import Path

# 委派到 scripts/hooks/
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts" / "hooks"
sys.path.insert(0, str(SCRIPTS_DIR.parent))

from hooks.post_task import main as post_task_main
from hooks.subagent_stop import main as subagent_stop_main


def handle_post_task(input_data: dict) -> None:
    """委派給 scripts/hooks/post_task.py"""
    # 將 input_data 寫入 stdin 模擬
    import io
    sys.stdin = io.StringIO(json.dumps(input_data))
    post_task_main()


def handle_subagent_stop(input_data: dict) -> None:
    """委派給 scripts/hooks/subagent_stop.py"""
    import io
    sys.stdin = io.StringIO(json.dumps(input_data))
    subagent_stop_main()


def main():
    if len(sys.argv) < 2:
        print("Usage: workflow_hooks.py <hook_type>", file=sys.stderr)
        sys.exit(1)

    hook_type = sys.argv[1]

    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        input_data = {}

    handlers = {
        "post_task": handle_post_task,
        "subagent_stop": handle_subagent_stop,
    }

    handler = handlers.get(hook_type)
    if handler:
        handler(input_data)
    else:
        print(f"Unknown hook type: {hook_type}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## 5. 設定檔更新

### 5.1 更新 commit-settings.yaml

```yaml
# shared/config/commit-settings.yaml
# Git Commit 統一設定

# Task commit 設定
task_commit:
  # 是否啟用自動 commit
  enabled: true

  # 是否包含 .claude/memory/ 目錄
  # 預設 false：memory 由 SubagentStop hook 單獨 commit
  include_memory: false

  # 是否包含 .claude/workflow/ logs
  # 預設 false：logs 通常不需要 commit
  include_logs: false

  # 排除的檔案模式（總是排除）
  exclude_patterns:
    - "*.pyc"
    - "__pycache__/"
    - ".pytest_cache/"
    - "*.egg-info/"
    - ".DS_Store"
    - "*.log"
    - ".env*"
    - "node_modules/"
    - "dist/"
    - ".venv/"

# Memory commit type 映射（支援 OCP - 可擴展無需改代碼）
commit_types:
  research: docs
  plans: feat
  tasks: feat
  implement: feat
  review: docs
  verify: test
  refactor: refactor
  # 新增類型只需在此添加

# Commit message 設定
commit_message:
  # Co-Author 簽名
  co_author: "Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

  # 模板
  templates:
    task: "{type}({scope}): {description}"
    memory: "{type}({scope}): complete {topic}\n\n{summary}\n\nMemory: {path}/"
```

---

## 6. 測試計劃

### 6.1 單元測試

```python
# tests/test_git_ops.py
import pytest
import subprocess
from pathlib import Path
from git_lib import GitOps, GitExecutor

@pytest.fixture
def git_repo(tmp_path):
    """建立測試用 git repo"""
    repo = tmp_path / "test_repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=repo, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo, check=True, capture_output=True
    )
    return repo

def test_has_changes_empty(git_repo):
    git = GitOps(git_repo)
    assert not git.has_changes()

def test_has_changes_with_file(git_repo):
    git = GitOps(git_repo)
    (git_repo / "test.txt").write_text("hello")
    assert git.has_changes()

def test_stage_and_commit(git_repo):
    git = GitOps(git_repo)

    # 建立檔案
    (git_repo / "test.txt").write_text("hello")

    # Stage
    git.stage(["."])

    # Commit
    result = git.commit("Initial commit")

    assert result.success
    assert len(result.commit_hash) == 40
    assert not git.has_changes()

def test_get_changed_files(git_repo):
    git = GitOps(git_repo)

    # 建立並 commit 初始檔案
    (git_repo / "a.txt").write_text("a")
    git.stage(["."])
    git.commit("Initial")

    # 修改檔案
    (git_repo / "a.txt").write_text("modified a")
    (git_repo / "b.txt").write_text("b")

    # 檢查變更
    changed = git.get_changed_files()
    assert "a.txt" in changed
    # b.txt 是 untracked，不在 diff 中
```

### 6.2 整合測試

```python
# tests/test_integration.py
import pytest
from pathlib import Path
from git_lib import WorkflowCommitFacade

@pytest.fixture
def workflow_project(git_repo):
    """建立帶 workflow 的測試專案"""
    # 建立 workflow 結構
    workflow_dir = git_repo / ".claude" / "workflow"
    workflow_dir.mkdir(parents=True)

    current = workflow_dir / "current.json"
    current.write_text('{"workflow_id": "test-workflow"}')

    # 建立 memory 結構
    memory_dir = git_repo / ".claude" / "memory" / "research" / "test-topic"
    memory_dir.mkdir(parents=True)
    (memory_dir / "report.md").write_text("# Test Report")

    return git_repo

def test_facade_get_workflow_id(workflow_project):
    facade = WorkflowCommitFacade(workflow_project)
    assert facade.get_workflow_id() == "test-workflow"

def test_facade_auto_commit_task(workflow_project):
    facade = WorkflowCommitFacade(workflow_project)

    # 建立一些程式碼變更
    (workflow_project / "src").mkdir()
    (workflow_project / "src" / "main.py").write_text("print('hello')")

    # Auto commit
    result = facade.auto_commit_after_task("add main module", success=True)

    assert result is not None
    assert result.success

    # 驗證 commit message
    import subprocess
    log = subprocess.run(
        ["git", "log", "-1", "--pretty=%B"],
        cwd=workflow_project,
        capture_output=True,
        text=True
    )
    assert "chore(task): add main module" in log.stdout
    assert "Co-Authored-By" in log.stdout

def test_facade_auto_commit_memory(workflow_project):
    facade = WorkflowCommitFacade(workflow_project)

    # 修改 memory
    memory_file = workflow_project / ".claude" / "memory" / "research" / "test-topic" / "report.md"
    memory_file.write_text("# Updated Report\n\nNew content")

    # Auto commit
    result = facade.auto_commit_memory("research", "test-topic")

    assert result is not None
    assert result.success

    # 驗證 commit message
    import subprocess
    log = subprocess.run(
        ["git", "log", "-1", "--pretty=%B"],
        cwd=workflow_project,
        capture_output=True,
        text=True
    )
    assert "docs(research): complete test topic" in log.stdout
```

---

## 7. 實施時程

### Phase 1: 基礎設施（Day 1-2）

| 任務 | 時間 | 產出 |
|------|------|------|
| 建立目錄結構 | 0.5h | `scripts/git_lib/` |
| 實作 exceptions.py | 1h | 自訂例外 |
| 實作 executor.py | 2h | GitExecutor |
| 實作 operations.py | 2h | GitOps |
| 撰寫單元測試 | 2h | test_git_executor.py, test_git_ops.py |

### Phase 2: 管理層（Day 3-4）

| 任務 | 時間 | 產出 |
|------|------|------|
| 實作 context.py | 2h | WorkflowContext |
| 實作 config.py | 2h | ConfigManager |
| 實作 commit.py | 3h | CommitManager |
| 更新 commit-settings.yaml | 1h | 擴展設定檔 |
| 撰寫測試 | 2h | test_workflow_context.py, test_commit_manager.py |

### Phase 3: Hook 重構（Day 5-6）

| 任務 | 時間 | 產出 |
|------|------|------|
| 實作 facade.py | 2h | WorkflowCommitFacade |
| 重構 post_task.py | 2h | 使用 git_lib |
| 重構 subagent_stop.py | 2h | 使用 git_lib |
| 整合 workflow_hooks.py | 1h | 委派模式 |
| 撰寫整合測試 | 2h | test_integration.py |
| 迴歸測試 | 1h | 驗證行為一致 |

### Phase 4: 文件更新（Day 7）

| 任務 | 時間 | 產出 |
|------|------|------|
| 更新 CLAUDE.md | 1h | Git 優化經驗 |
| 更新 README.md | 1h | git_lib 使用說明 |
| 更新 commit-protocol.md | 1h | 新架構說明 |
| API 文件 | 2h | git_lib docstrings |

---

## 8. 驗收標準

### 8.1 功能驗收

- [ ] 所有現有 hook 行為不變
- [ ] `_get_current_workflow_id()` 統一實作
- [ ] Commit message 格式一致
- [ ] Co-Author 自動添加

### 8.2 品質驗收

- [ ] 測試覆蓋率 ≥ 80%
- [ ] Hook 代碼減少 ≥ 50%
- [ ] 無重複的 Git 操作代碼
- [ ] 所有 DRY 違反已修復

### 8.3 文件驗收

- [ ] CLAUDE.md 包含優化經驗
- [ ] README.md 包含 git_lib 使用說明
- [ ] API 有完整 docstrings
- [ ] commit-protocol.md 更新

---

## 9. 風險與緩解

| 風險 | 機率 | 影響 | 緩解措施 |
|------|-----|------|---------|
| 破壞現有行為 | 中 | 高 | 完整測試 + 逐步重構 |
| 遷移時間超預期 | 中 | 中 | 分 Phase 可暫停 |
| 測試環境問題 | 低 | 中 | 使用 tmp_path fixture |

---

## 附錄：檔案清單

### 新增檔案

```
scripts/git_lib/__init__.py
scripts/git_lib/exceptions.py
scripts/git_lib/executor.py
scripts/git_lib/operations.py
scripts/git_lib/context.py
scripts/git_lib/config.py
scripts/git_lib/commit.py
scripts/git_lib/facade.py
tests/test_git_executor.py
tests/test_git_ops.py
tests/test_workflow_context.py
tests/test_commit_manager.py
tests/test_integration.py
```

### 修改檔案

```
scripts/hooks/post_task.py
scripts/hooks/subagent_stop.py
templates/hooks/workflow_hooks.py
shared/config/commit-settings.yaml
CLAUDE.md
README.md
shared/git/commit-protocol.md
```

---

**計劃完成時間**: 2026-02-01
**預估實作時間**: 7 天
**設計者**: Claude Code (Orchestrator)
