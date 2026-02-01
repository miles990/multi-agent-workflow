"""CommitManager 單元測試"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from git_lib import CommitManager, ConfigManager


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
    """建立帶 workflow 的測試專案"""
    # 建立 workflow 結構
    workflow_dir = git_repo / ".claude" / "workflow"
    workflow_dir.mkdir(parents=True)

    current = workflow_dir / "current.json"
    current.write_text(json.dumps({"workflow_id": "test-workflow"}))

    # 建立 memory 結構
    memory_dir = git_repo / ".claude" / "memory" / "research" / "test-topic"
    memory_dir.mkdir(parents=True)
    (memory_dir / "report.md").write_text("# Test Report")

    return git_repo


class TestCommitManagerTaskChanges:
    """commit_task_changes() 方法測試"""

    def test_commit_task_changes_success(self, workflow_project):
        """測試成功 commit task 變更"""
        manager = CommitManager(workflow_project)

        # 建立程式碼變更
        src = workflow_project / "src"
        src.mkdir()
        (src / "main.py").write_text("print('hello')")

        result = manager.commit_task_changes("add main module")

        assert result is not None
        assert result.success
        assert result.commit_hash is not None

        # 驗證 commit message
        log = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            cwd=workflow_project,
            capture_output=True,
            text=True,
        )
        assert "chore(task): add main module" in log.stdout
        assert ConfigManager.CO_AUTHOR in log.stdout

    def test_commit_task_changes_no_changes(self, workflow_project):
        """測試無變更時返回 None"""
        manager = CommitManager(workflow_project)

        # 先 commit memory 目錄（已存在的內容）
        subprocess.run(["git", "add", "."], cwd=workflow_project, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=workflow_project,
            capture_output=True,
        )

        result = manager.commit_task_changes("no changes")

        assert result is None

    def test_commit_task_changes_exclude_memory(self, workflow_project):
        """測試排除 memory 目錄"""
        manager = CommitManager(workflow_project)

        # 修改 memory
        memory_file = (
            workflow_project / ".claude" / "memory" / "research" / "test-topic" / "report.md"
        )
        memory_file.write_text("# Updated Report")

        # 只修改 memory，不應該有 commit
        result = manager.commit_task_changes(
            "no code changes", include_memory=False
        )

        assert result is None


class TestCommitManagerMemoryChanges:
    """commit_memory_changes() 方法測試"""

    def test_commit_memory_changes_success(self, workflow_project):
        """測試成功 commit memory 變更"""
        manager = CommitManager(workflow_project)

        # 修改 memory
        memory_file = (
            workflow_project / ".claude" / "memory" / "research" / "test-topic" / "report.md"
        )
        memory_file.write_text("# Updated Report\n\nNew content")

        result = manager.commit_memory_changes("research", "test-topic")

        assert result is not None
        assert result.success

        # 驗證 commit message
        log = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            cwd=workflow_project,
            capture_output=True,
            text=True,
        )
        assert "docs(research): complete test topic" in log.stdout
        assert ConfigManager.CO_AUTHOR in log.stdout

    def test_commit_memory_changes_no_changes(self, workflow_project):
        """測試無變更時返回 None"""
        manager = CommitManager(workflow_project)

        # 先 commit 現有內容
        subprocess.run(["git", "add", "."], cwd=workflow_project, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=workflow_project,
            capture_output=True,
        )

        result = manager.commit_memory_changes("research", "test-topic")

        assert result is None


class TestCommitManagerMessageFormat:
    """_format_message() 方法測試"""

    def test_format_simple_message(self, workflow_project):
        """測試簡單訊息格式"""
        manager = CommitManager(workflow_project)

        message = manager._format_message(
            commit_type="feat", scope="auth", description="add login"
        )

        lines = message.split("\n")
        assert lines[0] == "feat(auth): add login"
        assert ConfigManager.CO_AUTHOR in message

    def test_format_message_with_body(self, workflow_project):
        """測試帶 body 的訊息格式"""
        manager = CommitManager(workflow_project)

        message = manager._format_message(
            commit_type="feat",
            scope="auth",
            description="add login",
            body="- Add login form\n- Add validation",
        )

        assert "Add login form" in message
        assert "Add validation" in message

    def test_format_message_with_footer(self, workflow_project):
        """測試帶 footer 的訊息格式"""
        manager = CommitManager(workflow_project)

        message = manager._format_message(
            commit_type="docs",
            scope="research",
            description="complete analysis",
            footer="Memory: .claude/memory/research/test/",
        )

        assert "Memory: .claude/memory/research/test/" in message


class TestCommitManagerBuildPathspecs:
    """_build_pathspecs() 方法測試"""

    def test_build_pathspecs_default(self, workflow_project):
        """測試預設 pathspecs"""
        manager = CommitManager(workflow_project)

        pathspecs = manager._build_pathspecs(
            include_memory=False, include_logs=False, exclude_patterns=[]
        )

        assert "." in pathspecs
        assert ":(exclude).claude/memory/" in pathspecs
        assert ":(exclude).claude/workflow/" in pathspecs
        assert ":(exclude).claude/logs/" in pathspecs

    def test_build_pathspecs_include_memory(self, workflow_project):
        """測試包含 memory"""
        manager = CommitManager(workflow_project)

        pathspecs = manager._build_pathspecs(
            include_memory=True, include_logs=False, exclude_patterns=[]
        )

        assert ":(exclude).claude/memory/" not in pathspecs

    def test_build_pathspecs_with_exclude(self, workflow_project):
        """測試自訂排除模式"""
        manager = CommitManager(workflow_project)

        pathspecs = manager._build_pathspecs(
            include_memory=False,
            include_logs=False,
            exclude_patterns=["*.log", "node_modules/"],
        )

        assert ":(exclude)*.log" in pathspecs
        assert ":(exclude)node_modules/" in pathspecs
