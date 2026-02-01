"""Git 基本操作

封裝常用 Git 命令，提供高階 API。
基於 GitExecutor，不直接呼叫 subprocess。

這層專注於「做什麼」（what），而非「怎麼做」（how）。
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .executor import GitExecutor


@dataclass
class CommitResult:
    """Commit 結果

    Attributes:
        success: commit 是否成功
        commit_hash: 成功時的 commit hash（40 字元）
        error: 失敗時的錯誤訊息
    """

    success: bool
    commit_hash: Optional[str] = None
    error: Optional[str] = None


class GitOps:
    """Git 基本操作 - 封裝常用命令

    提供常用 Git 操作的高階介面，隱藏命令細節。

    Example:
        git = GitOps(Path("/my/project"))

        if git.has_changes():
            git.stage(["."])
            result = git.commit("Initial commit")
            if result.success:
                print(f"Committed: {result.commit_hash[:8]}")
    """

    def __init__(self, project_dir: Path):
        """初始化

        Args:
            project_dir: 專案根目錄
        """
        self.project_dir = Path(project_dir)
        self.executor = GitExecutor(self.project_dir)

    def has_changes(self, pathspecs: Optional[List[str]] = None) -> bool:
        """檢查是否有未提交的變更

        Args:
            pathspecs: 限定檢查的路徑，None 表示全部

        Returns:
            True 如果有變更，否則 False
        """
        args = ["status", "--porcelain"]
        if pathspecs:
            args.extend(["--"] + pathspecs)

        result = self.executor.run(args)
        return bool(result.stdout.strip())

    def stage(self, pathspecs: List[str]) -> None:
        """Stage 檔案

        Args:
            pathspecs: 要 stage 的路徑列表
                      支援 :! 或 :(exclude) 排除語法

        Raises:
            GitExecutionError: stage 失敗時
        """
        # 分離正向和排除的 pathspecs
        include_paths = []
        exclude_paths = []

        for spec in pathspecs:
            if spec.startswith(":!"):
                exclude_paths.append(spec[2:])  # 移除 :! 前綴
            elif spec.startswith(":(exclude)"):
                exclude_paths.append(spec[10:])  # 移除 :(exclude) 前綴
            else:
                include_paths.append(spec)

        # 先 stage 正向路徑
        if include_paths:
            args = ["add", "--"] + include_paths
            self.executor.run(args, check=True)

        # 然後 unstage 排除路徑
        for exclude in exclude_paths:
            # 使用 git reset HEAD 來 unstage
            self.executor.run(
                ["reset", "HEAD", "--", exclude],
                check=False  # 如果路徑不存在不報錯
            )

    def commit(self, message: str) -> CommitResult:
        """建立 commit

        Args:
            message: commit message

        Returns:
            CommitResult 物件
        """
        result = self.executor.run(["commit", "-m", message])

        if result.success:
            # 取得 commit hash
            hash_result = self.executor.run(["rev-parse", "HEAD"])
            return CommitResult(success=True, commit_hash=hash_result.stdout.strip())
        else:
            return CommitResult(success=False, error=result.stderr)

    def get_changed_files(
        self, pathspecs: Optional[List[str]] = None, cached: bool = False
    ) -> List[str]:
        """取得變更的檔案列表

        Args:
            pathspecs: 限定檢查的路徑
            cached: True 表示只查看已 stage 的變更

        Returns:
            變更檔案的路徑列表
        """
        args = ["diff", "--name-only"]
        if cached:
            args.append("--cached")
        if pathspecs:
            args.extend(["--"] + pathspecs)

        result = self.executor.run(args)
        return [f for f in result.stdout.strip().split("\n") if f]

    def get_status(self, pathspecs: Optional[List[str]] = None) -> str:
        """取得 git status 輸出

        Args:
            pathspecs: 限定檢查的路徑

        Returns:
            porcelain 格式的 status 輸出
        """
        args = ["status", "--porcelain"]
        if pathspecs:
            args.extend(["--"] + pathspecs)

        result = self.executor.run(args)
        return result.stdout.strip()

    def get_untracked_files(self, pathspecs: Optional[List[str]] = None) -> List[str]:
        """取得未追蹤的檔案列表

        Args:
            pathspecs: 限定檢查的路徑

        Returns:
            未追蹤檔案的路徑列表
        """
        status = self.get_status(pathspecs)
        untracked = []
        for line in status.split("\n"):
            if line.startswith("??"):
                # 格式: "?? path/to/file"
                untracked.append(line[3:].strip())
        return untracked

    def get_current_branch(self) -> Optional[str]:
        """取得當前分支名稱

        Returns:
            分支名稱，若在 detached HEAD 狀態則返回 None
        """
        result = self.executor.run(["branch", "--show-current"])
        branch = result.stdout.strip()
        return branch if branch else None
