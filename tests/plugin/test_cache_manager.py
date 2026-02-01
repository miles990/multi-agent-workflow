"""Tests for CacheManager."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cli"))

from plugin.cache import CacheManager, CacheStatus


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

    return project_dir


@pytest.fixture
def temp_cache(tmp_path):
    """Create a temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def cache_manager(temp_project, temp_cache):
    """Create a CacheManager instance."""
    return CacheManager(
        project_dir=temp_project,
        cache_base=temp_cache,
    )


class TestCacheManager:
    """Tests for CacheManager class."""

    def test_plugin_name(self, cache_manager):
        """Test reading plugin name from plugin.json."""
        assert cache_manager.plugin_name == "test-plugin"

    def test_plugin_version(self, cache_manager):
        """Test reading plugin version from plugin.json."""
        assert cache_manager.plugin_version == "1.0.0"

    def test_get_cache_dir(self, cache_manager, temp_cache):
        """Test cache directory path construction."""
        cache_dir = cache_manager.get_cache_dir()
        expected = temp_cache / "test-plugin" / "test-plugin" / "1.0.0"
        assert cache_dir == expected

    def test_get_cache_dir_custom(self, cache_manager, temp_cache):
        """Test cache directory with custom parameters."""
        cache_dir = cache_manager.get_cache_dir(
            plugin_name="custom",
            version="2.0.0",
            marketplace="my-marketplace"
        )
        expected = temp_cache / "my-marketplace" / "custom" / "2.0.0"
        assert cache_dir == expected

    def test_status_not_exists(self, cache_manager):
        """Test status when cache doesn't exist."""
        status = cache_manager.status()
        assert status.exists is False
        assert status.is_valid is False
        assert status.file_count == 0

    def test_status_exists(self, cache_manager, temp_cache):
        """Test status when cache exists."""
        # Create cache
        cache_dir = cache_manager.get_cache_dir()
        cache_dir.mkdir(parents=True)

        # Add plugin.json
        plugin_json = {"name": "test-plugin", "version": "1.0.0"}
        (cache_dir / "plugin.json").write_text(json.dumps(plugin_json))

        # Add skills
        skills_dir = cache_dir / "skills" / "test-skill"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("# Test")

        status = cache_manager.status()
        assert status.exists is True
        assert status.is_valid is True
        assert status.file_count > 0
        assert "test-skill" in status.skills

    def test_clean(self, cache_manager):
        """Test cleaning cache."""
        # Create cache
        cache_dir = cache_manager.get_cache_dir()
        cache_dir.mkdir(parents=True)
        (cache_dir / "test.txt").write_text("test")

        # Clean
        cleaned = cache_manager.clean()
        assert len(cleaned) == 1
        assert not cache_dir.exists()

    def test_get_all_cached_versions(self, cache_manager, temp_cache):
        """Test getting all cached versions."""
        # Create multiple versions
        for version in ["1.0.0", "1.1.0", "2.0.0"]:
            cache_dir = cache_manager.get_cache_dir(version=version)
            cache_dir.mkdir(parents=True)

        versions = cache_manager.get_all_cached_versions()
        assert versions == ["2.0.0", "1.1.0", "1.0.0"]

    def test_compute_hash(self, cache_manager, temp_project):
        """Test file hash computation."""
        test_file = temp_project / "test.txt"
        test_file.write_text("hello world")

        hash1 = cache_manager.compute_hash(test_file)
        assert len(hash1) == 64  # SHA256 hex length

        # Same content = same hash
        hash2 = cache_manager.compute_hash(test_file)
        assert hash1 == hash2

        # Different content = different hash
        test_file.write_text("different")
        hash3 = cache_manager.compute_hash(test_file)
        assert hash1 != hash3

    def test_get_file_manifest(self, cache_manager, temp_project):
        """Test file manifest generation."""
        # Create test files
        (temp_project / "file1.txt").write_text("content1")
        (temp_project / "file2.txt").write_text("content2")
        (temp_project / "subdir").mkdir()
        (temp_project / "subdir" / "file3.txt").write_text("content3")

        manifest = cache_manager.get_file_manifest(temp_project)

        assert "file1.txt" in manifest
        assert "file2.txt" in manifest
        assert "subdir/file3.txt" in manifest

    def test_compare_manifests(self, cache_manager):
        """Test manifest comparison."""
        source = {
            "file1.txt": "hash1",
            "file2.txt": "hash2",
            "file3.txt": "hash3_new",
        }
        cache = {
            "file1.txt": "hash1",
            "file3.txt": "hash3_old",
            "file4.txt": "hash4",
        }

        added, modified, deleted = cache_manager.compare_manifests(source, cache)

        assert "file2.txt" in added
        assert "file3.txt" in modified
        assert "file4.txt" in deleted


class TestCacheStatus:
    """Tests for CacheStatus class."""

    def test_size_human_bytes(self):
        """Test human-readable size formatting."""
        status = CacheStatus(
            plugin_name="test",
            cache_path=Path("/test"),
            exists=True,
            size_bytes=500,
        )
        assert "B" in status.size_human

    def test_size_human_kb(self):
        """Test KB formatting."""
        status = CacheStatus(
            plugin_name="test",
            cache_path=Path("/test"),
            exists=True,
            size_bytes=2048,
        )
        assert "KB" in status.size_human

    def test_size_human_mb(self):
        """Test MB formatting."""
        status = CacheStatus(
            plugin_name="test",
            cache_path=Path("/test"),
            exists=True,
            size_bytes=2 * 1024 * 1024,
        )
        assert "MB" in status.size_human

    def test_to_dict(self):
        """Test dictionary conversion."""
        status = CacheStatus(
            plugin_name="test",
            cache_path=Path("/test"),
            exists=True,
            version="1.0.0",
        )
        d = status.to_dict()
        assert d["plugin_name"] == "test"
        assert d["version"] == "1.0.0"
        assert d["exists"] is True
