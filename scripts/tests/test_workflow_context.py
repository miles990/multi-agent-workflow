"""WorkflowContext 單元測試"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from git_lib import WorkflowContext, WorkflowNotFoundError


@pytest.fixture
def project_dir(tmp_path):
    """建立測試專案目錄"""
    return tmp_path / "project"


@pytest.fixture
def workflow_project(project_dir):
    """建立帶 workflow 的測試專案"""
    project_dir.mkdir()

    # 建立 workflow 結構
    workflow_dir = project_dir / ".claude" / "workflow"
    workflow_dir.mkdir(parents=True)

    # 建立 global current.json
    current = workflow_dir / "current.json"
    current.write_text(json.dumps({"workflow_id": "test-workflow"}))

    return project_dir


@pytest.fixture
def workflow_with_subdirs(project_dir):
    """建立有多個 workflow 子目錄的測試專案"""
    project_dir.mkdir()

    workflow_dir = project_dir / ".claude" / "workflow"
    workflow_dir.mkdir(parents=True)

    # 建立第一個 workflow
    wf1 = workflow_dir / "workflow-001"
    wf1.mkdir()
    (wf1 / "current.json").write_text(
        json.dumps({"workflow_id": "workflow-001", "status": "completed"})
    )

    # 建立第二個 workflow（活躍中）
    wf2 = workflow_dir / "workflow-002"
    wf2.mkdir()
    (wf2 / "current.json").write_text(
        json.dumps({"workflow_id": "workflow-002", "status": "in_progress", "stage": "implement"})
    )

    return project_dir


class TestWorkflowContextGetCurrentWorkflowId:
    """get_current_workflow_id() 方法測試"""

    def test_get_from_global_current(self, workflow_project):
        """測試從全域 current.json 取得 workflow ID"""
        ctx = WorkflowContext(workflow_project)
        workflow_id = ctx.get_current_workflow_id()

        assert workflow_id == "test-workflow"

    def test_get_from_subdirs(self, workflow_with_subdirs):
        """測試從子目錄取得活躍 workflow ID"""
        ctx = WorkflowContext(workflow_with_subdirs)
        workflow_id = ctx.get_current_workflow_id()

        # 應該取得活躍的 workflow-002
        assert workflow_id == "workflow-002"

    def test_no_workflow(self, project_dir):
        """測試無 workflow 時返回 None"""
        project_dir.mkdir()
        ctx = WorkflowContext(project_dir)
        workflow_id = ctx.get_current_workflow_id()

        assert workflow_id is None

    def test_empty_workflow_dir(self, project_dir):
        """測試空 workflow 目錄時返回 None"""
        project_dir.mkdir()
        (project_dir / ".claude" / "workflow").mkdir(parents=True)

        ctx = WorkflowContext(project_dir)
        workflow_id = ctx.get_current_workflow_id()

        assert workflow_id is None


class TestWorkflowContextGetWorkflowState:
    """get_workflow_state() 方法測試"""

    def test_get_state_by_id(self, workflow_with_subdirs):
        """測試使用 ID 取得狀態"""
        ctx = WorkflowContext(workflow_with_subdirs)
        state = ctx.get_workflow_state("workflow-002")

        assert state["workflow_id"] == "workflow-002"
        assert state["status"] == "in_progress"
        assert state["stage"] == "implement"

    def test_get_state_current(self, workflow_with_subdirs):
        """測試取得當前 workflow 狀態"""
        ctx = WorkflowContext(workflow_with_subdirs)
        state = ctx.get_workflow_state()  # 不傳 ID

        assert state["workflow_id"] == "workflow-002"

    def test_workflow_not_found(self, workflow_project):
        """測試 workflow 不存在時拋出例外"""
        ctx = WorkflowContext(workflow_project)

        with pytest.raises(WorkflowNotFoundError):
            ctx.get_workflow_state("nonexistent-workflow")

    def test_no_active_workflow(self, project_dir):
        """測試無活躍 workflow 時拋出例外"""
        project_dir.mkdir()
        ctx = WorkflowContext(project_dir)

        with pytest.raises(WorkflowNotFoundError):
            ctx.get_workflow_state()


class TestWorkflowContextGetWorkflowStage:
    """get_workflow_stage() 方法測試"""

    def test_get_stage(self, workflow_with_subdirs):
        """測試取得階段"""
        ctx = WorkflowContext(workflow_with_subdirs)
        stage = ctx.get_workflow_stage("workflow-002")

        assert stage == "implement"

    def test_get_stage_none(self, project_dir):
        """測試無 workflow 時返回 None"""
        project_dir.mkdir()
        ctx = WorkflowContext(project_dir)
        stage = ctx.get_workflow_stage()

        assert stage is None


class TestWorkflowContextIsWorkflowActive:
    """is_workflow_active() 方法測試"""

    def test_active_workflow(self, workflow_with_subdirs):
        """測試活躍 workflow"""
        ctx = WorkflowContext(workflow_with_subdirs)

        assert ctx.is_workflow_active("workflow-002")

    def test_completed_workflow(self, workflow_with_subdirs):
        """測試已完成 workflow"""
        ctx = WorkflowContext(workflow_with_subdirs)

        assert not ctx.is_workflow_active("workflow-001")

    def test_nonexistent_workflow(self, project_dir):
        """測試不存在 workflow"""
        project_dir.mkdir()
        ctx = WorkflowContext(project_dir)

        assert not ctx.is_workflow_active("nonexistent")
