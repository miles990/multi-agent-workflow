"""自訂例外類別

Git 操作統一模組的例外定義。遵循例外階層設計，
所有例外繼承自 GitLibError 基礎類別。
"""

from typing import List


class GitLibError(Exception):
    """Git 模組基礎例外

    所有 git_lib 模組的例外都繼承此類別，
    方便統一捕獲和處理。
    """

    pass


class GitExecutionError(GitLibError):
    """Git 命令執行失敗

    當 git 命令返回非零狀態碼時拋出此例外。

    Attributes:
        cmd: 執行的完整命令列表
        returncode: 命令返回碼
        stderr: 標準錯誤輸出
    """

    def __init__(self, cmd: List[str], returncode: int, stderr: str):
        self.cmd = cmd
        self.returncode = returncode
        self.stderr = stderr
        cmd_str = " ".join(cmd)
        super().__init__(f"Git command failed: {cmd_str}, rc={returncode}")


class GitTimeoutError(GitLibError):
    """Git 命令超時

    當 git 命令執行超過指定時間時拋出此例外。

    Attributes:
        cmd: 執行的完整命令列表
        timeout: 超時秒數
    """

    def __init__(self, cmd: List[str], timeout: int):
        self.cmd = cmd
        self.timeout = timeout
        cmd_str = " ".join(cmd)
        super().__init__(f"Git command timeout: {cmd_str}, {timeout}s")


class WorkflowNotFoundError(GitLibError):
    """Workflow 不存在

    當嘗試存取不存在的 workflow 時拋出此例外。
    """

    pass


class WorktreeError(GitLibError):
    """Worktree 操作失敗

    當 git worktree 相關操作失敗時拋出此例外。
    """

    pass
