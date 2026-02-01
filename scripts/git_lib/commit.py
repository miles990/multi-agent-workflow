"""Commit 業務邏輯

高階 commit 操作，整合 GitOps、WorkflowContext、ConfigManager。
提供 Task 和 Memory commit 的完整業務邏輯。
"""

from pathlib import Path
from typing import List, Optional

from .config import ConfigManager
from .context import WorkflowContext
from .operations import CommitResult, GitOps


class CommitManager:
    """Commit 管理 - 高階業務邏輯

    整合所有底層模組，提供：
    - Task commit（程式碼變更）
    - Memory commit（記憶/研究變更）
    - 統一的 message 格式化

    Example:
        manager = CommitManager(Path("/my/project"))

        # Task commit
        result = manager.commit_task_changes("add authentication module")

        # Memory commit
        result = manager.commit_memory_changes("research", "auth-patterns")
    """

    def __init__(self, project_dir: Path):
        """初始化

        Args:
            project_dir: 專案根目錄
        """
        self.project_dir = Path(project_dir)
        self.git = GitOps(project_dir)
        self.context = WorkflowContext(project_dir)
        self.config = ConfigManager(project_dir)

    def commit_task_changes(
        self,
        description: str,
        include_memory: bool = False,
        include_logs: bool = False,
        exclude_patterns: Optional[List[str]] = None,
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
            include_memory, include_logs, exclude_patterns or []
        )

        # 檢查變更
        if not self.git.has_changes(pathspecs):
            return None

        # Stage
        self.git.stage(pathspecs)

        # 建立 commit message
        task_summary = description[:50] if description else "task completed"
        message = self._format_message(
            commit_type="chore", scope="task", description=task_summary
        )

        # Commit
        return self.git.commit(message)

    def commit_memory_changes(
        self, memory_type: str, memory_id: str
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
        summary_lines = [f"- Update {Path(f).name}" for f in changed_files[:3]]
        if len(changed_files) > 3:
            summary_lines.append(f"- ... and {len(changed_files) - 3} more files")

        message = self._format_message(
            commit_type=commit_type,
            scope=memory_type,
            description=f"complete {topic}",
            body="\n".join(summary_lines),
            footer=f"Memory: {memory_dir}/",
        )

        # Commit
        return self.git.commit(message)

    def _build_pathspecs(
        self, include_memory: bool, include_logs: bool, exclude_patterns: List[str]
    ) -> List[str]:
        """建立 pathspec 列表

        Args:
            include_memory: 是否包含 memory 目錄
            include_logs: 是否包含 logs 目錄
            exclude_patterns: 額外排除模式

        Returns:
            pathspec 列表（用於 git add/status）

        Note:
            使用 :(exclude) 語法而非 :! 因為 :! 後面跟 _ 開頭的路徑
            會被 git 解析錯誤（如 __pycache__/）
        """
        pathspecs = ["."]

        if not include_memory:
            pathspecs.append(":(exclude).claude/memory/")

        if not include_logs:
            pathspecs.append(":(exclude).claude/workflow/")
            pathspecs.append(":(exclude).claude/logs/")

        for pattern in exclude_patterns:
            pathspecs.append(f":(exclude){pattern}")

        return pathspecs

    def _format_message(
        self,
        commit_type: str,
        scope: str,
        description: str,
        body: Optional[str] = None,
        footer: Optional[str] = None,
    ) -> str:
        """格式化 commit message（遵循 conventional commits）

        Args:
            commit_type: commit 類型（feat, fix, docs, etc.）
            scope: 範圍（task, research, etc.）
            description: 簡短描述
            body: 詳細說明（可選）
            footer: 頁尾資訊（可選）

        Returns:
            完整的 commit message
        """
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
