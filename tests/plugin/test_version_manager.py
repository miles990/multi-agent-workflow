"""Tests for VersionManager."""

import json
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cli"))

from plugin.version import (
    VersionManager,
    SemanticVersion,
    BumpLevel,
    ChangelogEntry,
    Changelog,
)
from plugin.exceptions import InvalidVersionError


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary plugin project."""
    project_dir = tmp_path / "test-plugin"
    project_dir.mkdir()

    # Create plugin.json
    plugin_json = {
        "name": "test-plugin",
        "version": "1.2.3",
        "description": "Test plugin"
    }
    (project_dir / "plugin.json").write_text(json.dumps(plugin_json, indent=2))

    # Create marketplace.json
    claude_plugin_dir = project_dir / ".claude-plugin"
    claude_plugin_dir.mkdir()
    marketplace_json = {
        "name": "test-plugin",
        "plugins": [{"name": "test-plugin", "version": "1.2.3"}]
    }
    (claude_plugin_dir / "marketplace.json").write_text(json.dumps(marketplace_json, indent=2))

    return project_dir


@pytest.fixture
def version_manager(temp_project):
    """Create a VersionManager instance."""
    return VersionManager(project_dir=temp_project)


class TestSemanticVersion:
    """Tests for SemanticVersion class."""

    def test_parse_basic(self):
        """Test basic version parsing."""
        v = SemanticVersion.parse("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
        assert v.prerelease is None
        assert v.build is None

    def test_parse_prerelease(self):
        """Test version with prerelease."""
        v = SemanticVersion.parse("1.2.3-beta.1")
        assert v.major == 1
        assert v.prerelease == "beta.1"

    def test_parse_build(self):
        """Test version with build metadata."""
        v = SemanticVersion.parse("1.2.3+build.123")
        assert v.major == 1
        assert v.build == "build.123"

    def test_parse_full(self):
        """Test full version with prerelease and build."""
        v = SemanticVersion.parse("1.2.3-rc.1+build.456")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
        assert v.prerelease == "rc.1"
        assert v.build == "build.456"

    def test_parse_invalid(self):
        """Test invalid version formats."""
        with pytest.raises(InvalidVersionError):
            SemanticVersion.parse("invalid")

        with pytest.raises(InvalidVersionError):
            SemanticVersion.parse("1.2")

        with pytest.raises(InvalidVersionError):
            SemanticVersion.parse("1.2.3.4")

    def test_bump_major(self):
        """Test major version bump."""
        v = SemanticVersion.parse("1.2.3")
        new_v = v.bump(BumpLevel.MAJOR)
        assert str(new_v) == "2.0.0"

    def test_bump_minor(self):
        """Test minor version bump."""
        v = SemanticVersion.parse("1.2.3")
        new_v = v.bump(BumpLevel.MINOR)
        assert str(new_v) == "1.3.0"

    def test_bump_patch(self):
        """Test patch version bump."""
        v = SemanticVersion.parse("1.2.3")
        new_v = v.bump(BumpLevel.PATCH)
        assert str(new_v) == "1.2.4"

    def test_comparison(self):
        """Test version comparison."""
        v1 = SemanticVersion.parse("1.0.0")
        v2 = SemanticVersion.parse("1.0.1")
        v3 = SemanticVersion.parse("1.1.0")
        v4 = SemanticVersion.parse("2.0.0")

        assert v1 < v2 < v3 < v4
        assert v1 == SemanticVersion.parse("1.0.0")

    def test_str(self):
        """Test string conversion."""
        assert str(SemanticVersion(1, 2, 3)) == "1.2.3"
        assert str(SemanticVersion(1, 2, 3, "beta")) == "1.2.3-beta"
        assert str(SemanticVersion(1, 2, 3, None, "build")) == "1.2.3+build"


class TestChangelogEntry:
    """Tests for ChangelogEntry class."""

    def test_from_commit_basic(self):
        """Test parsing conventional commit."""
        line = "abc1234|feat(auth): add login feature|John Doe"
        entry = ChangelogEntry.from_commit(line)

        assert entry is not None
        assert entry.type == "feat"
        assert entry.scope == "auth"
        assert entry.description == "add login feature"
        assert entry.commit_hash == "abc1234"
        assert entry.author == "John Doe"

    def test_from_commit_no_scope(self):
        """Test commit without scope."""
        line = "abc1234|fix: correct typo|Author"
        entry = ChangelogEntry.from_commit(line)

        assert entry is not None
        assert entry.type == "fix"
        assert entry.scope is None

    def test_from_commit_breaking(self):
        """Test breaking change detection."""
        line = "abc1234|feat(api): BREAKING CHANGE: remove old endpoint|Author"
        entry = ChangelogEntry.from_commit(line)

        assert entry is not None
        assert entry.breaking is True

    def test_from_commit_invalid(self):
        """Test invalid commit format."""
        line = "not a conventional commit"
        entry = ChangelogEntry.from_commit(line)
        assert entry is None


class TestChangelog:
    """Tests for Changelog class."""

    def test_has_breaking_changes(self):
        """Test breaking change detection."""
        changelog = Changelog(
            version="1.0.0",
            date=pytest.importorskip("datetime").datetime.now(),
            entries=[
                ChangelogEntry("feat", "scope", "desc", "abc", breaking=False),
                ChangelogEntry("fix", "scope", "desc", "def", breaking=True),
            ]
        )
        assert changelog.has_breaking_changes is True

    def test_grouped_entries(self):
        """Test entry grouping by type."""
        from datetime import datetime
        changelog = Changelog(
            version="1.0.0",
            date=datetime.now(),
            entries=[
                ChangelogEntry("feat", None, "feature 1", "abc"),
                ChangelogEntry("feat", None, "feature 2", "def"),
                ChangelogEntry("fix", None, "bug fix", "ghi"),
            ]
        )

        groups = changelog.grouped_entries
        assert len(groups["feat"]) == 2
        assert len(groups["fix"]) == 1

    def test_to_markdown(self):
        """Test markdown generation."""
        from datetime import datetime
        changelog = Changelog(
            version="1.0.0",
            date=datetime(2026, 1, 15),
            entries=[
                ChangelogEntry("feat", "api", "add new endpoint", "abc1234"),
            ]
        )

        md = changelog.to_markdown()
        assert "[1.0.0] - 2026-01-15" in md
        assert "Features" in md
        assert "add new endpoint" in md


class TestVersionManager:
    """Tests for VersionManager class."""

    def test_get_current_version(self, version_manager):
        """Test reading current version."""
        v = version_manager.get_current_version()
        assert str(v) == "1.2.3"

    def test_get_all_versions(self, version_manager):
        """Test getting versions from all files."""
        versions = version_manager.get_all_versions()
        assert "plugin.json" in versions
        assert versions["plugin.json"] == "1.2.3"

    def test_check_version_consistency_pass(self, version_manager):
        """Test version consistency check (pass)."""
        assert version_manager.check_version_consistency() is True

    def test_check_version_consistency_fail(self, version_manager, temp_project):
        """Test version consistency check (fail)."""
        from plugin.exceptions import VersionConflictError

        # Make versions inconsistent
        marketplace = temp_project / ".claude-plugin" / "marketplace.json"
        data = json.loads(marketplace.read_text())
        data["plugins"][0]["version"] = "9.9.9"
        marketplace.write_text(json.dumps(data))

        with pytest.raises(VersionConflictError):
            version_manager.check_version_consistency()

    def test_bump_dry_run(self, version_manager, temp_project):
        """Test version bump in dry run mode."""
        original = (temp_project / "plugin.json").read_text()

        new_v = version_manager.bump(BumpLevel.MINOR, dry_run=True)

        assert str(new_v) == "1.3.0"
        # File should not change
        assert (temp_project / "plugin.json").read_text() == original

    def test_bump_actual(self, version_manager, temp_project):
        """Test actual version bump."""
        version_manager.bump(BumpLevel.PATCH, dry_run=False)

        # Read updated file
        data = json.loads((temp_project / "plugin.json").read_text())
        assert data["version"] == "1.2.4"

    def test_suggest_commit_message(self, version_manager):
        """Test commit message suggestion."""
        v = SemanticVersion.parse("1.3.0")

        msg = version_manager.suggest_commit_message(BumpLevel.MINOR, v)
        assert "feat(version)" in msg
        assert "1.3.0" in msg

    def test_check_compatibility_same_major(self, version_manager):
        """Test compatibility check within same major."""
        result = version_manager.check_compatibility("1.5.0")
        assert result["compatible"] is True

    def test_check_compatibility_different_major(self, version_manager):
        """Test compatibility check across major versions."""
        result = version_manager.check_compatibility("2.0.0")
        assert result["compatible"] is False
        assert len(result["issues"]) > 0
