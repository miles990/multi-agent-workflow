"""Integration 測試"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from git_lib import (
    CommitManager,
    ConfigManager,
    GitOps,
    WorkflowCommitFacade,
    WorkflowContext,
)


@pytest.fixture
def git_repo(tmp_path):
    """建立測試用 git repo"""
    repo = tmp_path / "test_repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return repo


@pytest.fixture
def workflow_project(git_repo):
    """建立完整的 workflow 專案"""
    # 建立 workflow 結構
    workflow_dir = git_repo / ".claude" / "workflow"
    workflow_dir.mkdir(parents=True)

    wf_subdir = workflow_dir / "test-workflow"
    wf_subdir.mkdir()
    (wf_subdir / "current.json").write_text(
        json.dumps(
            {"workflow_id": "test-workflow", "status": "in_progress", "stage": "implement"}
        )
    )

    # 建立 global current.json
    (workflow_dir / "current.json").write_text(
        json.dumps({"workflow_id": "test-workflow"})
    )

    # 建立 memory 結構
    memory_dir = git_repo / ".claude" / "memory" / "research" / "api-design"
    memory_dir.mkdir(parents=True)
    (memory_dir / "analysis.md").write_text("# API Design Analysis")
    (memory_dir / "recommendations.md").write_text("# Recommendations")

    # 建立 src 結構
    src_dir = git_repo / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("# Main module")

    return git_repo


class TestWorkflowCommitFacade:
    """WorkflowCommitFacade 整合測試"""

    def test_facade_get_workflow_id(self, workflow_project):
        """測試取得 workflow ID"""
        facade = WorkflowCommitFacade(workflow_project)
        assert facade.get_workflow_id() == "test-workflow"

    def test_facade_auto_commit_task(self, workflow_project):
        """測試自動 commit task"""
        facade = WorkflowCommitFacade(workflow_project)

        # 先 commit 初始狀態（包含 workflow 和 memory）
        subprocess.run(["git", "add", "."], cwd=workflow_project, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=workflow_project,
            capture_output=True,
        )

        # 建立程式碼變更
        (workflow_project / "src" / "feature.py").write_text("def feature(): pass")

        result = facade.auto_commit_after_task("add feature module", success=True)

        assert result is not None
        assert result.success

        # 驗證 memory 沒有被 commit
        log = subprocess.run(
            ["git", "log", "-1", "--name-only"],
            cwd=workflow_project,
            capture_output=True,
            text=True,
        )
        assert "src/feature.py" in log.stdout
        assert ".claude/memory" not in log.stdout

    def test_facade_auto_commit_task_failed(self, workflow_project):
        """測試 task 失敗時不 commit"""
        facade = WorkflowCommitFacade(workflow_project)

        # 建立變更
        (workflow_project / "src" / "broken.py").write_text("broken code")

        result = facade.auto_commit_after_task("broken feature", success=False)

        assert result is None

    def test_facade_auto_commit_memory(self, workflow_project):
        """測試自動 commit memory"""
        facade = WorkflowCommitFacade(workflow_project)

        # 修改 memory
        memory_file = (
            workflow_project / ".claude" / "memory" / "research" / "api-design" / "analysis.md"
        )
        memory_file.write_text("# Updated API Design Analysis\n\nNew insights...")

        result = facade.auto_commit_memory("research", "api-design")

        assert result is not None
        assert result.success

        # 驗證 commit message
        log = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            cwd=workflow_project,
            capture_output=True,
            text=True,
        )
        assert "docs(research): complete api design" in log.stdout

    def test_facade_is_commit_enabled(self, workflow_project):
        """測試檢查 commit 是否啟用"""
        facade = WorkflowCommitFacade(workflow_project)
        assert facade.is_commit_enabled()


class TestEndToEndWorkflow:
    """端到端工作流測試"""

    def test_complete_workflow(self, workflow_project):
        """測試完整工作流程"""
        # 1. 取得 workflow context
        ctx = WorkflowContext(workflow_project)
        assert ctx.get_current_workflow_id() == "test-workflow"
        assert ctx.get_workflow_stage() == "implement"

        # 2. 程式碼變更並 commit
        git = GitOps(workflow_project)
        (workflow_project / "src" / "api.py").write_text("class API: pass")

        assert git.has_changes()
        git.stage(["src/"])

        config = ConfigManager(workflow_project)
        message = f"feat(api): add API class\n\n{config.get_co_author()}"
        result = git.commit(message)

        assert result.success

        # 3. 驗證 commit 歷史
        log = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=workflow_project,
            capture_output=True,
            text=True,
        )
        assert "add API class" in log.stdout

    def test_multiple_memory_commits(self, workflow_project):
        """測試多個 memory 目錄 commit"""
        facade = WorkflowCommitFacade(workflow_project)

        # 建立另一個 memory 目錄
        plans_dir = workflow_project / ".claude" / "memory" / "plans" / "implementation"
        plans_dir.mkdir(parents=True)
        (plans_dir / "plan.md").write_text("# Implementation Plan")

        # Commit 第一個 memory
        result1 = facade.auto_commit_memory("research", "api-design")
        assert result1 is None or result1.success  # 可能無變更

        # 修改並 commit
        (plans_dir / "plan.md").write_text("# Updated Plan\n\n## Phase 1")
        result2 = facade.auto_commit_memory("plans", "implementation")

        assert result2 is not None
        assert result2.success

        # 驗證 commit type
        log = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            cwd=workflow_project,
            capture_output=True,
            text=True,
        )
        assert "feat(plans):" in log.stdout


class TestConfigIntegration:
    """設定整合測試"""

    def test_config_commit_types(self, workflow_project):
        """測試 commit type 映射"""
        config = ConfigManager(workflow_project)

        assert config.get_commit_type("research") == "docs"
        assert config.get_commit_type("plans") == "feat"
        assert config.get_commit_type("verify") == "test"
        assert config.get_commit_type("unknown") == "chore"

    def test_config_co_author(self, workflow_project):
        """測試 Co-Author"""
        config = ConfigManager(workflow_project)
        co_author = config.get_co_author()

        assert "Claude Opus 4.5" in co_author
        assert "Co-Authored-By:" in co_author

    def test_config_exclude_patterns(self, workflow_project):
        """測試排除模式"""
        config = ConfigManager(workflow_project)
        patterns = config.get_exclude_patterns()

        assert "*.pyc" in patterns
        assert "__pycache__/" in patterns
