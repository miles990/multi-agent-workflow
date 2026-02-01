"""Git 命令執行器

提供統一的 Git 命令執行介面，封裝 subprocess 呼叫，
實現統一的錯誤處理和日誌記錄。

這是 git_lib 的最底層，所有 Git 操作最終都通過此模組執行。
"""

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .exceptions import GitExecutionError, GitTimeoutError

logger = logging.getLogger(__name__)


@dataclass
class GitResult:
    """Git 命令執行結果

    Attributes:
        returncode: 命令返回碼
        stdout: 標準輸出
        stderr: 標準錯誤輸出
    """

    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        """命令是否成功執行"""
        return self.returncode == 0


class GitExecutor:
    """Git 命令執行器 - 統一底層介面

    封裝所有 subprocess.run 呼叫，提供：
    - 統一的錯誤處理
    - 自動日誌記錄
    - 可配置的超時處理
    - 一致的結果格式

    Example:
        executor = GitExecutor(Path("/my/project"))
        result = executor.run(["status", "--porcelain"])
        if result.success:
            print(result.stdout)
    """

    def __init__(self, cwd: Path):
        """初始化執行器

        Args:
            cwd: 命令執行的工作目錄
        """
        self.cwd = Path(cwd)

    def run(
        self,
        args: List[str],
        check: bool = False,
        capture_output: bool = True,
        text: bool = True,
        timeout: Optional[int] = 60,
    ) -> GitResult:
        """執行 git 命令

        Args:
            args: git 參數列表，如 ["status", "--porcelain"]
            check: 是否在失敗時拋出例外
            capture_output: 是否捕獲輸出
            text: 是否以文字模式處理輸出
            timeout: 超時秒數，None 表示不限時

        Returns:
            GitResult 物件，包含執行結果

        Raises:
            GitExecutionError: 當 check=True 且命令失敗時
            GitTimeoutError: 當命令執行超時時
        """
        cmd = ["git"] + args
        logger.debug("執行: %s (cwd=%s)", " ".join(cmd), self.cwd)

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.cwd),
                capture_output=capture_output,
                text=text,
                timeout=timeout,
            )

            git_result = GitResult(
                returncode=result.returncode,
                stdout=result.stdout if hasattr(result, "stdout") and result.stdout else "",
                stderr=result.stderr if hasattr(result, "stderr") and result.stderr else "",
            )

            if check and not git_result.success:
                logger.error("Git 命令失敗: %s, stderr=%s", cmd, git_result.stderr)
                raise GitExecutionError(cmd, result.returncode, git_result.stderr)

            return git_result

        except subprocess.TimeoutExpired as e:
            logger.error("Git 命令超時: %s, timeout=%s", cmd, timeout)
            raise GitTimeoutError(cmd, timeout or 0) from e
