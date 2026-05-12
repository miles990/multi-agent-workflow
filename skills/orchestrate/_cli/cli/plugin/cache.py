"""Cache management for plugins.

Handles plugin cache discovery, status, cleaning, and validation.
"""

import hashlib
import json
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .exceptions import CacheError, CacheNotFoundError, CacheCorruptedError


@dataclass
class CacheStatus:
    """Status information about a plugin cache."""

    plugin_name: str
    cache_path: Path
    exists: bool
    version: Optional[str] = None
    size_bytes: int = 0
    file_count: int = 0
    last_sync: Optional[datetime] = None
    is_valid: bool = False
    skills: list[str] = field(default_factory=list)

    @property
    def size_human(self) -> str:
        """Human-readable size."""
        size = self.size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "plugin_name": self.plugin_name,
            "cache_path": str(self.cache_path),
            "exists": self.exists,
            "version": self.version,
            "size_bytes": self.size_bytes,
            "size_human": self.size_human,
            "file_count": self.file_count,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "is_valid": self.is_valid,
            "skills": self.skills,
        }


class CacheManager:
    """Manages plugin cache operations.

    Claude Code caches plugins at:
    ~/.claude/plugins/cache/{marketplace}/{plugin_name}/{version}/

    Example:
    ~/.claude/plugins/cache/multi-agent-workflow/multi-agent-workflow/2.3.1/
    """

    DEFAULT_CACHE_BASE = Path.home() / ".claude" / "plugins" / "cache"

    # Files and directories to exclude from sync
    DEFAULT_EXCLUDES = [
        "__pycache__",
        "*.pyc",
        "*.pyo",
        ".git",
        ".gitignore",
        ".pytest_cache",
        ".coverage",
        "*.egg-info",
        "tests",
        ".plugin-dev",
        ".claude",
        "*.md",  # Keep SKILL.md but exclude others during sync
        "!SKILL.md",  # Except SKILL.md
        "!CLAUDE.md",  # Except CLAUDE.md
    ]

    def __init__(
        self,
        project_dir: Optional[Path] = None,
        cache_base: Optional[Path] = None,
    ):
        """Initialize cache manager.

        Args:
            project_dir: Plugin project directory (default: cwd)
            cache_base: Custom cache base directory (default: ~/.claude/plugins/cache)
        """
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.cache_base = Path(cache_base) if cache_base else self.DEFAULT_CACHE_BASE
        self._plugin_json: Optional[dict] = None

    @property
    def plugin_json(self) -> dict:
        """Load and cache plugin.json."""
        if self._plugin_json is None:
            plugin_json_path = self.project_dir / "plugin.json"
            if not plugin_json_path.exists():
                raise CacheError(
                    f"plugin.json not found at {plugin_json_path}",
                    "Ensure you're in a plugin project directory."
                )
            with open(plugin_json_path) as f:
                self._plugin_json = json.load(f)
        return self._plugin_json

    @property
    def plugin_name(self) -> str:
        """Get plugin name from plugin.json."""
        return self.plugin_json.get("name", "unknown")

    @property
    def plugin_version(self) -> str:
        """Get plugin version from plugin.json."""
        return self.plugin_json.get("version", "0.0.0")

    def get_cache_dir(
        self,
        plugin_name: Optional[str] = None,
        version: Optional[str] = None,
        marketplace: Optional[str] = None,
    ) -> Path:
        """Get the cache directory for a plugin.

        Args:
            plugin_name: Plugin name (default: from plugin.json)
            version: Plugin version (default: from plugin.json)
            marketplace: Marketplace name (default: same as plugin_name)

        Returns:
            Path to cache directory
        """
        name = plugin_name or self.plugin_name
        ver = version or self.plugin_version
        mkt = marketplace or name
        return self.cache_base / mkt / name / ver

    def get_all_cached_versions(
        self,
        plugin_name: Optional[str] = None,
        marketplace: Optional[str] = None,
    ) -> list[str]:
        """Get all cached versions of a plugin.

        Returns:
            List of version strings, sorted newest first
        """
        name = plugin_name or self.plugin_name
        mkt = marketplace or name
        plugin_cache = self.cache_base / mkt / name

        if not plugin_cache.exists():
            return []

        versions = [
            d.name for d in plugin_cache.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]

        # Sort by semantic version (descending)
        def version_key(v: str) -> tuple:
            try:
                parts = v.split(".")
                return tuple(int(p) for p in parts)
            except ValueError:
                return (0, 0, 0)

        return sorted(versions, key=version_key, reverse=True)

    def status(
        self,
        plugin_name: Optional[str] = None,
        version: Optional[str] = None,
    ) -> CacheStatus:
        """Get cache status for a plugin.

        Args:
            plugin_name: Plugin name (default: from plugin.json)
            version: Plugin version (default: from plugin.json)

        Returns:
            CacheStatus object with cache information
        """
        name = plugin_name or self.plugin_name
        ver = version or self.plugin_version
        cache_dir = self.get_cache_dir(name, ver)

        status = CacheStatus(
            plugin_name=name,
            cache_path=cache_dir,
            exists=cache_dir.exists(),
        )

        if not status.exists:
            return status

        # Gather statistics
        status.version = ver
        status.file_count = sum(1 for _ in cache_dir.rglob("*") if _.is_file())
        status.size_bytes = sum(
            f.stat().st_size for f in cache_dir.rglob("*") if f.is_file()
        )

        # Get last modification time
        try:
            mtime = cache_dir.stat().st_mtime
            status.last_sync = datetime.fromtimestamp(mtime)
        except OSError:
            pass

        # List skills
        skills_dir = cache_dir / "skills"
        if skills_dir.exists():
            status.skills = [
                d.name for d in skills_dir.iterdir()
                if d.is_dir() and (d / "SKILL.md").exists()
            ]

        # Validate cache
        status.is_valid = self._validate_cache(cache_dir)

        return status

    def _validate_cache(self, cache_dir: Path) -> bool:
        """Validate cache integrity.

        Checks:
        1. plugin.json exists
        2. skills directory exists
        3. At least one skill has SKILL.md
        """
        plugin_json = cache_dir / "plugin.json"
        if not plugin_json.exists():
            return False

        skills_dir = cache_dir / "skills"
        if not skills_dir.exists():
            return False

        # Check at least one valid skill
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                return True

        return False

    def clean(
        self,
        plugin_name: Optional[str] = None,
        version: Optional[str] = None,
        keep_versions: int = 0,
    ) -> list[Path]:
        """Clean cache for a plugin.

        Args:
            plugin_name: Plugin name (default: from plugin.json)
            version: Specific version to clean (default: current version)
            keep_versions: Number of recent versions to keep (0 = clean all)

        Returns:
            List of cleaned directories
        """
        name = plugin_name or self.plugin_name
        cleaned = []

        if version:
            # Clean specific version
            cache_dir = self.get_cache_dir(name, version)
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                cleaned.append(cache_dir)
        elif keep_versions > 0:
            # Keep N recent versions
            versions = self.get_all_cached_versions(name)
            to_remove = versions[keep_versions:]
            for ver in to_remove:
                cache_dir = self.get_cache_dir(name, ver)
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                    cleaned.append(cache_dir)
        else:
            # Clean current version
            cache_dir = self.get_cache_dir(name)
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                cleaned.append(cache_dir)

        return cleaned

    def repair(
        self,
        plugin_name: Optional[str] = None,
        version: Optional[str] = None,
    ) -> bool:
        """Repair a corrupted cache by rebuilding.

        Args:
            plugin_name: Plugin name (default: from plugin.json)
            version: Plugin version (default: from plugin.json)

        Returns:
            True if repair was successful
        """
        # Clean and resync
        self.clean(plugin_name, version)
        # Sync will be handled by DevCommands
        return True

    def compute_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of a file.

        Args:
            file_path: Path to file

        Returns:
            Hex digest of SHA256 hash
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def get_file_manifest(self, directory: Path) -> dict[str, str]:
        """Get manifest of files with their hashes.

        Args:
            directory: Directory to scan

        Returns:
            Dict mapping relative paths to hashes
        """
        manifest = {}
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(directory)
                # Skip excluded patterns
                if self._should_exclude(rel_path):
                    continue
                manifest[str(rel_path)] = self.compute_hash(file_path)
        return manifest

    def _should_exclude(self, rel_path: Path) -> bool:
        """Check if a path should be excluded from sync."""
        path_str = str(rel_path)
        path_parts = rel_path.parts

        for pattern in self.DEFAULT_EXCLUDES:
            if pattern.startswith("!"):
                # Negation pattern - include this file
                continue
            if pattern.startswith("*"):
                # Extension match
                if path_str.endswith(pattern[1:]):
                    return True
            elif pattern in path_parts:
                # Directory match
                return True

        return False

    def compare_manifests(
        self,
        source_manifest: dict[str, str],
        cache_manifest: dict[str, str],
    ) -> tuple[list[str], list[str], list[str]]:
        """Compare two manifests to find differences.

        Args:
            source_manifest: Source directory manifest
            cache_manifest: Cache directory manifest

        Returns:
            Tuple of (added, modified, deleted) file lists
        """
        source_files = set(source_manifest.keys())
        cache_files = set(cache_manifest.keys())

        added = list(source_files - cache_files)
        deleted = list(cache_files - source_files)

        modified = [
            f for f in source_files & cache_files
            if source_manifest[f] != cache_manifest[f]
        ]

        return added, modified, deleted
