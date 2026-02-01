"""GitExecutor 單元測試"""

import subprocess
import sys
from pathlib import Path

import pytest

# 加入 git_lib 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from git_lib import GitExecutionError, GitExecutor, GitTimeoutError


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


class TestGitExecutor:
    """GitExecutor 測試"""

    def test_run_success(self, git_repo):
        """測試成功執行命令"""
        executor = GitExecutor(git_repo)
        result = executor.run(["status"])

        assert result.success
        assert result.returncode == 0

    def test_run_with_output(self, git_repo):
        """測試捕獲輸出"""
        executor = GitExecutor(git_repo)

        # 建立檔案
        (git_repo / "test.txt").write_text("hello")

        result = executor.run(["status", "--porcelain"])

        assert result.success
        assert "test.txt" in result.stdout

    def test_run_failure_without_check(self, git_repo):
        """測試命令失敗但不拋出例外"""
        executor = GitExecutor(git_repo)

        # 嘗試 checkout 不存在的分支
        result = executor.run(["checkout", "nonexistent-branch"])

        assert not result.success
        assert result.returncode != 0

    def test_run_failure_with_check(self, git_repo):
        """測試命令失敗時拋出例外"""
        executor = GitExecutor(git_repo)

        with pytest.raises(GitExecutionError) as exc_info:
            executor.run(["checkout", "nonexistent-branch"], check=True)

        assert "nonexistent-branch" in str(exc_info.value.cmd)
        assert exc_info.value.returncode != 0

    def test_git_result_success_property(self, git_repo):
        """測試 GitResult.success 屬性"""
        executor = GitExecutor(git_repo)

        success_result = executor.run(["status"])
        assert success_result.success

        failure_result = executor.run(["checkout", "nonexistent"])
        assert not failure_result.success


class TestGitExecutorEdgeCases:
    """GitExecutor 邊界情況測試"""

    def test_empty_stdout(self, git_repo):
        """測試空輸出"""
        executor = GitExecutor(git_repo)
        result = executor.run(["status", "--porcelain"])

        # 空 repo 沒有變更
        assert result.stdout == ""

    def test_multiline_output(self, git_repo):
        """測試多行輸出"""
        executor = GitExecutor(git_repo)

        # 建立多個檔案
        (git_repo / "a.txt").write_text("a")
        (git_repo / "b.txt").write_text("b")

        result = executor.run(["status", "--porcelain"])

        lines = [line for line in result.stdout.strip().split("\n") if line]
        assert len(lines) == 2
