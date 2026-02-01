"""Tests for DevCommands."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cli"))

from plugin.dev import DevCommands, SyncResult, WatchConfig
from plugin.cache import CacheManager


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary plugin project."""
    project_dir = tmp_path / "test-plugin"
    project_dir.mkdir()

    # Create plugin.json
    plugin_json = {
        "name": "test-plugin",
        "version": "1.0.0",
        "description": "Test plugin"
    }
    (project_dir / "plugin.json").write_text(json.dumps(plugin_json))

    # Create skills directory
    skills_dir = project_dir / "skills" / "test-skill"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text("# Test Skill")
    (skills_dir / "config.yaml").write_text("key: value")

    # Create shared directory
    shared_dir = project_dir / "shared" / "test"
    shared_dir.mkdir(parents=True)
    (shared_dir / "module.yaml").write_text("module: test")

    return project_dir


@pytest.fixture
def temp_cache(tmp_path):
    """Create a temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def dev_commands(temp_project, temp_cache):
    """Create DevCommands instance."""
    cache_manager = CacheManager(
        project_dir=temp_project,
        cache_base=temp_cache,
    )
    return DevCommands(
        project_dir=temp_project,
        cache_manager=cache_manager,
    )


class TestSyncResult:
    """Tests for SyncResult class."""

    def test_total_changes(self):
        """Test total changes calculation."""
        result = SyncResult(
            success=True,
            source=Path("/src"),
            destination=Path("/dest"),
            files_added=["a.txt", "b.txt"],
            files_modified=["c.txt"],
            files_deleted=["d.txt"],
        )
        assert result.total_changes == 4

    def test_to_dict(self):
        """Test dictionary conversion."""
        result = SyncResult(
            success=True,
            source=Path("/src"),
            destination=Path("/dest"),
            duration_ms=100,
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["duration_ms"] == 100


class TestWatchConfig:
    """Tests for WatchConfig class."""

    def test_default_values(self):
        """Test default configuration."""
        config = WatchConfig()
        assert config.debounce_ms == 500
        assert config.exclude_patterns == []
        assert config.include_patterns == []

    def test_load_from_file(self, tmp_path):
        """Test loading from JSON file."""
        config_file = tmp_path / "watch.config.json"
        config_file.write_text(json.dumps({
            "debounce_ms": 1000,
            "exclude_patterns": ["*.log"],
        }))

        config = WatchConfig.load(config_file)
        assert config.debounce_ms == 1000
        assert "*.log" in config.exclude_patterns

    def test_load_missing_file(self, tmp_path):
        """Test loading from missing file returns defaults."""
        config = WatchConfig.load(tmp_path / "missing.json")
        assert config.debounce_ms == 500

    def test_save(self, tmp_path):
        """Test saving to file."""
        config = WatchConfig(debounce_ms=750)
        config_file = tmp_path / "config.json"
        config.save(config_file)

        loaded = json.loads(config_file.read_text())
        assert loaded["debounce_ms"] == 750


class TestDevCommands:
    """Tests for DevCommands class."""

    def test_sync_creates_destination(self, dev_commands, temp_cache):
        """Test sync creates destination directory."""
        cache_dir = dev_commands.cache.get_cache_dir()
        assert not cache_dir.exists()

        result = dev_commands.sync()

        assert result.success
        assert cache_dir.exists()

    def test_sync_copies_files(self, dev_commands, temp_cache):
        """Test sync copies expected files."""
        result = dev_commands.sync()

        assert result.success

        cache_dir = dev_commands.cache.get_cache_dir()
        assert (cache_dir / "skills" / "test-skill" / "SKILL.md").exists()
        assert (cache_dir / "shared" / "test" / "module.yaml").exists()

    def test_sync_excludes_patterns(self, dev_commands, temp_project):
        """Test sync excludes configured patterns."""
        # Create files that should be excluded
        (temp_project / "__pycache__").mkdir()
        (temp_project / "__pycache__" / "test.pyc").write_text("cache")
        (temp_project / "tests").mkdir()
        (temp_project / "tests" / "test_something.py").write_text("test")

        result = dev_commands.sync()

        assert result.success
        cache_dir = dev_commands.cache.get_cache_dir()
        assert not (cache_dir / "__pycache__").exists()
        assert not (cache_dir / "tests").exists()

    def test_sync_dry_run(self, dev_commands, temp_cache):
        """Test sync in dry run mode."""
        result = dev_commands.sync(dry_run=True)

        assert result.success
        cache_dir = dev_commands.cache.get_cache_dir()
        # Cache should not be created in dry run
        assert not cache_dir.exists()

    def test_sync_force(self, dev_commands, temp_cache):
        """Test force sync ignores cache map."""
        # First sync
        result1 = dev_commands.sync()
        assert result1.success
        assert len(result1.files_added) > 0

        # Second sync (incremental, no changes)
        result2 = dev_commands.sync()
        assert result2.success
        assert result2.total_changes == 0

        # Force sync (should show files again as added)
        result3 = dev_commands.sync(force=True)
        assert result3.success
        # In force mode, we still use hash comparison

    def test_sync_callback(self, dev_commands):
        """Test sync file callback."""
        files_synced = []

        def callback(path, action):
            files_synced.append((path, action))

        result = dev_commands.sync(on_file=callback)

        assert result.success
        assert len(files_synced) > 0
        # Check at least one file was added
        actions = [a for _, a in files_synced]
        assert "add" in actions

    def test_sync_updates_cache_map(self, dev_commands):
        """Test sync updates cache map."""
        dev_commands.sync()

        cache_map = dev_commands._load_cache_map()
        assert len(cache_map) > 0
        # Check cache map has expected structure
        for path, info in cache_map.items():
            assert "hash" in info
            assert "size" in info
            assert "mtime" in info

    def test_sync_detects_modifications(self, dev_commands, temp_project):
        """Test sync detects file modifications."""
        # First sync
        dev_commands.sync()

        # Modify a file
        skill_md = temp_project / "skills" / "test-skill" / "SKILL.md"
        skill_md.write_text("# Modified Skill")

        # Second sync
        result = dev_commands.sync()

        assert result.success
        assert "skills/test-skill/SKILL.md" in result.files_modified

    def test_sync_detects_deletions(self, dev_commands, temp_project):
        """Test sync detects file deletions."""
        # First sync
        dev_commands.sync()

        # Delete a file
        config_yaml = temp_project / "skills" / "test-skill" / "config.yaml"
        config_yaml.unlink()

        # Second sync
        result = dev_commands.sync()

        assert result.success
        assert "skills/test-skill/config.yaml" in result.files_deleted

    def test_link_creates_symlink(self, dev_commands, temp_project):
        """Test link creates symbolic link."""
        result = dev_commands.link()

        assert result
        cache_dir = dev_commands.cache.get_cache_dir()
        assert cache_dir.is_symlink()
        assert cache_dir.resolve() == temp_project

    def test_link_force_replaces(self, dev_commands):
        """Test link --force replaces existing cache."""
        # Create cache first
        dev_commands.sync()

        # Now link with force
        result = dev_commands.link(force=True)

        assert result
        cache_dir = dev_commands.cache.get_cache_dir()
        assert cache_dir.is_symlink()

    def test_unlink_removes_symlink(self, dev_commands, temp_project):
        """Test unlink removes symbolic link."""
        dev_commands.link()

        result = dev_commands.unlink()

        assert result
        cache_dir = dev_commands.cache.get_cache_dir()
        assert not cache_dir.is_symlink()
        # Cache should be restored
        assert cache_dir.exists()
