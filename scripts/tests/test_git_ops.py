"""GitOps 單元測試"""

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from git_lib import GitOps


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


class TestGitOpsHasChanges:
    """has_changes() 方法測試"""

    def test_has_changes_empty(self, git_repo):
        """測試空 repo 無變更"""
        git = GitOps(git_repo)
        assert not git.has_changes()

    def test_has_changes_with_file(self, git_repo):
        """測試有檔案變更"""
        git = GitOps(git_repo)
        (git_repo / "test.txt").write_text("hello")
        assert git.has_changes()

    def test_has_changes_with_pathspecs(self, git_repo):
        """測試使用 pathspecs 過濾"""
        git = GitOps(git_repo)

        # 建立兩個檔案
        (git_repo / "a.txt").write_text("a")
        subdir = git_repo / "subdir"
        subdir.mkdir()
        (subdir / "b.txt").write_text("b")

        # 只檢查 subdir
        assert git.has_changes(["subdir/"])
        assert git.has_changes(["a.txt"])


class TestGitOpsStageAndCommit:
    """stage() 和 commit() 方法測試"""

    def test_stage_single_file(self, git_repo):
        """測試 stage 單一檔案"""
        git = GitOps(git_repo)

        (git_repo / "test.txt").write_text("hello")
        git.stage(["test.txt"])

        # 驗證已 staged
        result = git.executor.run(["diff", "--cached", "--name-only"])
        assert "test.txt" in result.stdout

    def test_stage_multiple_files(self, git_repo):
        """測試 stage 多個檔案"""
        git = GitOps(git_repo)

        (git_repo / "a.txt").write_text("a")
        (git_repo / "b.txt").write_text("b")
        git.stage(["a.txt", "b.txt"])

        result = git.executor.run(["diff", "--cached", "--name-only"])
        assert "a.txt" in result.stdout
        assert "b.txt" in result.stdout

    def test_commit_success(self, git_repo):
        """測試成功 commit"""
        git = GitOps(git_repo)

        (git_repo / "test.txt").write_text("hello")
        git.stage(["."])
        result = git.commit("Initial commit")

        assert result.success
        assert result.commit_hash is not None
        assert len(result.commit_hash) == 40

    def test_commit_no_changes(self, git_repo):
        """測試無變更時 commit"""
        git = GitOps(git_repo)

        # 先建立一個 commit
        (git_repo / "test.txt").write_text("hello")
        git.stage(["."])
        git.commit("Initial")

        # 嘗試再次 commit（無變更）
        result = git.commit("Empty commit")

        assert not result.success
        assert result.error is not None


class TestGitOpsGetChangedFiles:
    """get_changed_files() 方法測試"""

    def test_get_changed_files_unstaged(self, git_repo):
        """測試取得未 staged 的變更檔案"""
        git = GitOps(git_repo)

        # 建立並 commit 初始檔案
        (git_repo / "a.txt").write_text("a")
        git.stage(["."])
        git.commit("Initial")

        # 修改檔案
        (git_repo / "a.txt").write_text("modified a")

        changed = git.get_changed_files()
        assert "a.txt" in changed

    def test_get_changed_files_cached(self, git_repo):
        """測試取得已 staged 的變更檔案"""
        git = GitOps(git_repo)

        # 建立並 commit 初始檔案
        (git_repo / "a.txt").write_text("a")
        git.stage(["."])
        git.commit("Initial")

        # 修改並 stage
        (git_repo / "a.txt").write_text("modified a")
        git.stage(["a.txt"])

        changed = git.get_changed_files(cached=True)
        assert "a.txt" in changed


class TestGitOpsGetStatus:
    """get_status() 方法測試"""

    def test_get_status_empty(self, git_repo):
        """測試空 repo 狀態"""
        git = GitOps(git_repo)
        status = git.get_status()
        assert status == ""

    def test_get_status_with_changes(self, git_repo):
        """測試有變更時的狀態"""
        git = GitOps(git_repo)

        (git_repo / "test.txt").write_text("hello")
        status = git.get_status()

        assert "test.txt" in status
        assert "??" in status  # untracked 標記


class TestGitOpsGetUntrackedFiles:
    """get_untracked_files() 方法測試"""

    def test_get_untracked_files(self, git_repo):
        """測試取得未追蹤檔案"""
        git = GitOps(git_repo)

        (git_repo / "untracked.txt").write_text("hello")
        untracked = git.get_untracked_files()

        assert "untracked.txt" in untracked

    def test_get_untracked_files_none(self, git_repo):
        """測試無未追蹤檔案"""
        git = GitOps(git_repo)
        untracked = git.get_untracked_files()
        assert untracked == []


class TestGitOpsGetCurrentBranch:
    """get_current_branch() 方法測試"""

    def test_get_current_branch_default(self, git_repo):
        """測試取得預設分支"""
        git = GitOps(git_repo)

        # 需要先有一個 commit
        (git_repo / "test.txt").write_text("hello")
        git.stage(["."])
        git.commit("Initial")

        branch = git.get_current_branch()
        assert branch in ["main", "master"]
