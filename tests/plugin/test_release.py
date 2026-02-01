"""Tests for ReleaseCommands."""

import json
import subprocess
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cli"))

from plugin.release import (
    ReleaseCommands,
    ReleaseStep,
    ReleaseProgress,
    ValidationResult,
)
from plugin.version import BumpLevel
from plugin.exceptions import DirtyWorkspaceError, ValidationError


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary plugin project with git."""
    project_dir = tmp_path / "test-plugin"
    project_dir.mkdir()

    # Initialize git
    subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=project_dir, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=project_dir, capture_output=True
    )

    # Create plugin.json
    plugin_json = {
        "name": "test-plugin",
        "version": "1.0.0",
        "description": "Test plugin"
    }
    (project_dir / "plugin.json").write_text(json.dumps(plugin_json, indent=2))

    # Create .claude-plugin/marketplace.json
    claude_plugin = project_dir / ".claude-plugin"
    claude_plugin.mkdir()
    marketplace_json = {
        "name": "test-plugin",
        "plugins": [{"name": "test-plugin", "version": "1.0.0"}]
    }
    (claude_plugin / "marketplace.json").write_text(json.dumps(marketplace_json, indent=2))

    # Create skills
    skills_dir = project_dir / "skills" / "test-skill"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text("# Test Skill")

    # Initial commit
    subprocess.run(["git", "add", "-A"], cwd=project_dir, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=project_dir, capture_output=True
    )

    return project_dir


@pytest.fixture
def release_commands(temp_project):
    """Create ReleaseCommands instance."""
    return ReleaseCommands(project_dir=temp_project)


class TestReleaseProgress:
    """Tests for ReleaseProgress class."""

    def test_to_dict(self):
        """Test dictionary conversion."""
        progress = ReleaseProgress(
            current_step=ReleaseStep.VALIDATE,
            new_version="1.1.0",
            started_at=datetime(2026, 1, 15, 12, 0, 0),
        )
        d = progress.to_dict()

        assert d["current_step"] == "validate"
        assert d["new_version"] == "1.1.0"
        assert "2026-01-15" in d["started_at"]

    def test_from_dict(self):
        """Test creation from dictionary."""
        d = {
            "current_step": "test",
            "completed_steps": ["validate"],
            "new_version": "1.1.0",
            "started_at": "2026-01-15T12:00:00",
        }
        progress = ReleaseProgress.from_dict(d)

        assert progress.current_step == ReleaseStep.TEST
        assert ReleaseStep.VALIDATE in progress.completed_steps
        assert progress.new_version == "1.1.0"


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_add_check_pass(self):
        """Test adding passing check."""
        result = ValidationResult(passed=True)
        result.add_check("test", True)

        assert result.checks["test"] is True
        assert result.passed is True

    def test_add_check_fail(self):
        """Test adding failing check."""
        result = ValidationResult(passed=True)
        result.add_check("test", False, "Error message")

        assert result.checks["test"] is False
        assert result.passed is False
        assert "Error message" in result.errors


class TestReleaseCommands:
    """Tests for ReleaseCommands class."""

    def test_validate_pass(self, release_commands):
        """Test validation passes for valid plugin."""
        result = release_commands.validate()

        assert result.passed
        assert result.checks.get("plugin_json") is True
        assert result.checks.get("skills_structure") is True

    def test_validate_missing_plugin_json(self, release_commands, temp_project):
        """Test validation fails without plugin.json."""
        (temp_project / "plugin.json").unlink()

        result = release_commands.validate()

        assert not result.passed
        assert result.checks.get("plugin_json") is False

    def test_validate_missing_skill_md(self, release_commands, temp_project):
        """Test validation fails without SKILL.md."""
        (temp_project / "skills" / "test-skill" / "SKILL.md").unlink()

        result = release_commands.validate()

        assert not result.passed
        assert result.checks.get("skills_structure") is False

    def test_validate_dirty_workspace(self, release_commands, temp_project):
        """Test validation detects uncommitted changes."""
        # Create uncommitted file
        (temp_project / "new_file.txt").write_text("uncommitted")

        result = release_commands.validate()

        # Still passes but warns
        assert result.checks.get("git_clean") is False

    def test_release_dry_run(self, release_commands):
        """Test release in dry run mode."""
        steps_executed = []

        def on_step(step, message):
            steps_executed.append(step)

        progress = release_commands.release(
            bump_level=BumpLevel.PATCH,
            dry_run=True,
            skip_tests=True,
            on_step=on_step,
        )

        assert progress.current_step == ReleaseStep.COMPLETE
        assert ReleaseStep.VALIDATE in progress.completed_steps
        assert progress.new_version == "1.0.1"

    def test_release_updates_version(self, release_commands, temp_project):
        """Test release updates version files."""
        release_commands.release(
            bump_level=BumpLevel.MINOR,
            dry_run=False,
            skip_tests=True,
        )

        # Check plugin.json updated
        data = json.loads((temp_project / "plugin.json").read_text())
        assert data["version"] == "1.1.0"

    def test_release_creates_tag(self, release_commands, temp_project):
        """Test release creates git tag."""
        release_commands.release(
            bump_level=BumpLevel.PATCH,
            dry_run=False,
            skip_tests=True,
        )

        # Check tag exists
        result = subprocess.run(
            ["git", "tag", "-l", "v1.0.1"],
            cwd=temp_project,
            capture_output=True,
            text=True,
        )
        assert "v1.0.1" in result.stdout

    def test_release_fails_validation(self, release_commands, temp_project):
        """Test release fails on validation error."""
        # Remove plugin.json to cause validation failure
        (temp_project / "plugin.json").unlink()

        with pytest.raises(ValidationError):
            release_commands.release(
                bump_level=BumpLevel.PATCH,
                dry_run=False,
                skip_tests=True,
            )

    def test_rollback(self, release_commands, temp_project):
        """Test rollback removes tag."""
        # First, create a release
        release_commands.release(
            bump_level=BumpLevel.PATCH,
            dry_run=False,
            skip_tests=True,
        )

        # Then rollback
        result = release_commands.rollback("v1.0.1")
        assert result

        # Check tag is gone
        tag_result = subprocess.run(
            ["git", "tag", "-l", "v1.0.1"],
            cwd=temp_project,
            capture_output=True,
            text=True,
        )
        assert "v1.0.1" not in tag_result.stdout

    def test_progress_saved_on_failure(self, release_commands, temp_project):
        """Test progress is saved when release fails."""
        # Remove plugin.json to cause validation failure
        (temp_project / "plugin.json").unlink()

        try:
            release_commands.release(
                bump_level=BumpLevel.PATCH,
                dry_run=False,
                skip_tests=True,
            )
        except ValidationError:
            pass

        # Check progress file exists
        progress_file = temp_project / ".plugin-dev" / "release-progress.json"
        assert progress_file.exists()

        # Check progress has failed step
        progress = release_commands._load_progress()
        assert progress.failed_step is not None
