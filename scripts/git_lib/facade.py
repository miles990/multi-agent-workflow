"""簡化入口 - Facade 模式

提供統一的高階 API，隱藏內部複雜性。
Hooks 只需要使用 WorkflowCommitFacade 即可完成所有 Git 操作。

這是 git_lib 模組對外的主要入口點。
"""

from pathlib import Path
from typing import Optional

from .commit import CommitManager
from .config import ConfigManager
from .context import WorkflowContext
from .operations import CommitResult


class WorkflowCommitFacade:
    """Workflow Commit 統一入口

    提供簡化的 API，隱藏內部複雜性。
    Hooks 只需要使用這個類別即可完成所有 Git 操作。

    設計原則：
    - Facade Pattern：統一入口，簡化使用
    - Lazy Initialization：延遲初始化，按需建立
    - Single Responsibility：每個方法對應一個明確場景

    Example:
        facade = WorkflowCommitFacade(project_dir)

        # 在 post_task hook 中
        result = facade.auto_commit_after_task("add feature", success=True)

        # 在 subagent_stop hook 中
        result = facade.auto_commit_memory("research", "api-design")
    """

    def __init__(self, project_dir: Path):
        """初始化

        Args:
            project_dir: 專案根目錄
        """
        self.project_dir = Path(project_dir)
        self.context = WorkflowContext(project_dir)
        self.config = ConfigManager(project_dir)
        self._commit_manager: Optional[CommitManager] = None

    @property
    def commit_manager(self) -> CommitManager:
        """延遲初始化 CommitManager

        Returns:
            CommitManager 實例
        """
        if self._commit_manager is None:
            self._commit_manager = CommitManager(self.project_dir)
        return self._commit_manager

    def get_workflow_id(self) -> Optional[str]:
        """取得當前 workflow ID

        Returns:
            workflow ID 或 None
        """
        return self.context.get_current_workflow_id()

    def auto_commit_after_task(
        self, description: str, success: bool
    ) -> Optional[CommitResult]:
        """Task 完成後自動 commit

        這是 post_task hook 的簡化入口。

        Args:
            description: task 描述
            success: task 是否成功

        Returns:
            CommitResult 或 None（無變更或 task 失敗）
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
            exclude_patterns=settings.get("exclude_patterns", []),
        )

    def auto_commit_memory(
        self, memory_type: str, memory_id: str
    ) -> Optional[CommitResult]:
        """Memory 變更自動 commit

        這是 subagent_stop hook 的簡化入口。

        Args:
            memory_type: memory 類型（research, plans, ...）
            memory_id: memory ID

        Returns:
            CommitResult 或 None（無變更）
        """
        return self.commit_manager.commit_memory_changes(
            memory_type=memory_type, memory_id=memory_id
        )

    def is_commit_enabled(self) -> bool:
        """檢查自動 commit 是否啟用

        Returns:
            True 如果啟用
        """
        settings = self.config.get_commit_settings()
        return settings.get("enabled", True)

    def auto_commit_checkpoint(self, checkpoint_file: str) -> Optional[CommitResult]:
        """檢查點檔案自動 commit

        當寫入工作流階段的檢查點檔案時自動觸發 commit。
        這解決了 context compaction 後直接 Write 而沒有 SubagentStop 事件的問題。

        Args:
            checkpoint_file: 檢查點檔案路徑

        Returns:
            CommitResult 或 None（無變更或未啟用）
        """
        # 檢查 checkpoint commit 是否啟用
        settings = self.config.get_commit_settings()
        checkpoint_settings = settings.get("checkpoint_commit", {})
        if not checkpoint_settings.get("enabled", True):
            return None

        # 從檔案路徑推斷階段
        stage = self._detect_stage_from_checkpoint(checkpoint_file)

        # 建立 commit message
        message = f"chore(checkpoint): complete {stage}"

        return self.commit_manager.commit_all_changes(
            message=message,
            include_memory=True,
        )

    def _detect_stage_from_checkpoint(self, checkpoint_file: str) -> str:
        """從檢查點檔案路徑推斷工作流階段

        Args:
            checkpoint_file: 檢查點檔案路徑

        Returns:
            階段名稱
        """
        file_name = Path(checkpoint_file).name.lower()

        stage_map = {
            "synthesis.md": "research",
            "implementation-plan.md": "plan",
            "tasks.yaml": "tasks",
            "summary.md": "implement",
            "review-summary.md": "review",
            "verify-summary.md": "verify",
        }

        return stage_map.get(file_name, "workflow")
