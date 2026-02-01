"""Git 操作統一模組

提供統一的 Git 操作 API，消除 DRY 違反，遵循 SOLID 原則。

使用範例（簡單）：
    from git_lib import WorkflowCommitFacade

    facade = WorkflowCommitFacade(project_dir)
    facade.auto_commit_after_task(description, success)

進階使用：
    from git_lib import GitOps, CommitManager, WorkflowContext

    git = GitOps(project_dir)
    if git.has_changes():
        git.stage(["."])
        git.commit("message")

模組結構：
    - exceptions: 自訂例外類別
    - executor: GitExecutor - 底層命令執行
    - operations: GitOps - 基本 Git 操作
    - context: WorkflowContext - Workflow 狀態管理
    - config: ConfigManager - 設定管理
    - commit: CommitManager - Commit 業務邏輯
    - facade: WorkflowCommitFacade - 簡化入口

設計原則：
    - DRY: 統一所有重複的 Git 操作邏輯
    - SRP: 每個類別單一職責
    - OCP: 配置驅動，新增 commit type 不需改代碼
    - DIP: 依賴抽象介面，易於測試和替換
"""

from .commit import CommitManager
from .config import ConfigManager
from .context import WorkflowContext
from .exceptions import (
    GitExecutionError,
    GitLibError,
    GitTimeoutError,
    WorkflowNotFoundError,
    WorktreeError,
)
from .executor import GitExecutor, GitResult
from .facade import WorkflowCommitFacade
from .operations import CommitResult, GitOps

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

__version__ = "1.0.0"
