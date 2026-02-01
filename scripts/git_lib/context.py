"""Workflow 狀態管理

統一 Workflow 相關操作，消除之前分散在多個 Hook 中的重複代碼。
這是解決 DRY 違反的核心模組。
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .exceptions import WorkflowNotFoundError


class WorkflowContext:
    """Workflow 狀態管理 - 統一 workflow 相關操作

    統一實作 _get_current_workflow_id()，取代之前分散在
    5 個 hook 檔案中的 65 行重複代碼。

    Example:
        ctx = WorkflowContext(Path("/my/project"))
        workflow_id = ctx.get_current_workflow_id()
        if workflow_id:
            state = ctx.get_workflow_state(workflow_id)
            print(f"Current stage: {state.get('stage')}")
    """

    def __init__(self, project_dir: Path):
        """初始化

        Args:
            project_dir: 專案根目錄
        """
        self.project_dir = Path(project_dir)
        self.workflow_base = self.project_dir / ".claude" / "workflow"

    def get_current_workflow_id(self) -> Optional[str]:
        """取得當前活躍的 workflow ID

        這是統一的實作，取代之前分散在 5 個 hook 中的重複代碼。

        搜尋順序：
        1. 全域 current.json（.claude/workflow/current.json）
        2. 各 workflow 目錄下的 current.json

        Returns:
            workflow_id 或 None（無活躍 workflow）
        """
        # 方法 1: 從 global current.json
        current_file = self.workflow_base / "current.json"
        if current_file.exists():
            try:
                with open(current_file) as f:
                    state = json.load(f)
                    workflow_id = state.get("workflow_id")
                    if workflow_id:
                        return workflow_id
            except (json.JSONDecodeError, KeyError):
                pass

        # 方法 2: 找最新的 workflow 目錄
        if self.workflow_base.exists():
            for d in sorted(self.workflow_base.iterdir(), reverse=True):
                if d.is_dir() and not d.name.startswith(("_", ".")):
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

    def get_workflow_state(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """取得 workflow 狀態

        Args:
            workflow_id: workflow ID，None 表示使用當前 workflow

        Returns:
            workflow 狀態字典

        Raises:
            WorkflowNotFoundError: workflow 不存在
        """
        if workflow_id is None:
            workflow_id = self.get_current_workflow_id()
            if workflow_id is None:
                raise WorkflowNotFoundError("No active workflow")

        state_file = self.workflow_base / workflow_id / "current.json"
        if not state_file.exists():
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

        with open(state_file) as f:
            return json.load(f)

    def get_workflow_stage(self, workflow_id: Optional[str] = None) -> Optional[str]:
        """取得 workflow 當前階段

        Args:
            workflow_id: workflow ID，None 表示使用當前 workflow

        Returns:
            階段名稱（如 "research", "implement"）或 None
        """
        try:
            state = self.get_workflow_state(workflow_id)
            return state.get("stage")
        except WorkflowNotFoundError:
            return None

    def is_workflow_active(self, workflow_id: Optional[str] = None) -> bool:
        """檢查 workflow 是否處於活躍狀態

        Args:
            workflow_id: workflow ID，None 表示使用當前 workflow

        Returns:
            True 如果 workflow 活躍中
        """
        try:
            state = self.get_workflow_state(workflow_id)
            return state.get("status") not in ("completed", "cancelled", "failed")
        except WorkflowNotFoundError:
            return False
