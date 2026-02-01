"""Development workflow commands for plugins.

Handles hot-reload development, file synchronization, and cache management.
"""

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from .cache import CacheManager, CacheStatus
from .exceptions import SyncError, SyncFailedError


@dataclass
class SyncResult:
    """Result of a sync operation."""
    success: bool
    source: Path
    destination: Path
    files_added: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    files_deleted: list[str] = field(default_factory=list)
    duration_ms: int = 0
    error: Optional[str] = None

    @property
    def total_changes(self) -> int:
        """Total number of file changes."""
        return len(self.files_added) + len(self.files_modified) + len(self.files_deleted)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "source": str(self.source),
            "destination": str(self.destination),
            "files_added": self.files_added,
            "files_modified": self.files_modified,
            "files_deleted": self.files_deleted,
            "total_changes": self.total_changes,
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


@dataclass
class WatchConfig:
    """Configuration for file watching."""
    debounce_ms: int = 500
    exclude_patterns: list[str] = field(default_factory=list)
    include_patterns: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, config_path: Path) -> "WatchConfig":
        """Load config from JSON file."""
        if config_path.exists():
            with open(config_path) as f:
                data = json.load(f)
            return cls(
                debounce_ms=data.get("debounce_ms", 500),
                exclude_patterns=data.get("exclude_patterns", []),
                include_patterns=data.get("include_patterns", []),
            )
        return cls()

    def save(self, config_path: Path) -> None:
        """Save config to JSON file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump({
                "debounce_ms": self.debounce_ms,
                "exclude_patterns": self.exclude_patterns,
                "include_patterns": self.include_patterns,
            }, f, indent=2)


@dataclass
class CacheMapEntry:
    """Entry in the cache map for tracking file states."""
    hash: str
    size: int
    mtime: float


class DevCommands:
    """Development workflow commands.

    Provides sync, watch, and link functionality for plugin development.
    """

    # Default patterns to sync (include)
    DEFAULT_INCLUDE = [
        "skills/**/*",
        "shared/**/*",
        "templates/**/*",
        "plugin.json",
        ".claude-plugin/**/*",
    ]

    # Default patterns to exclude from sync
    DEFAULT_EXCLUDE = [
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
        ".claude/workflow",
        ".claude/memory",
        "cli",
        "scripts",
        "docs",
        "agents",
    ]

    def __init__(
        self,
        project_dir: Optional[Path] = None,
        cache_manager: Optional[CacheManager] = None,
    ):
        """Initialize development commands.

        Args:
            project_dir: Plugin project directory (default: cwd)
            cache_manager: Optional CacheManager instance
        """
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.cache = cache_manager or CacheManager(project_dir=self.project_dir)

        # Config paths
        self.dev_config_dir = self.project_dir / ".plugin-dev"
        self.watch_config_path = self.dev_config_dir / "watch.config.json"
        self.cache_map_path = self.dev_config_dir / "cache-map.json"

    def sync(
        self,
        force: bool = False,
        dry_run: bool = False,
        on_file: Optional[Callable[[str, str], None]] = None,
    ) -> SyncResult:
        """Synchronize plugin to cache directory.

        Args:
            force: Force full sync (ignore incremental)
            dry_run: Don't actually copy files
            on_file: Callback for each file (path, action)

        Returns:
            SyncResult with sync details
        """
        start_time = time.time()
        source = self.project_dir
        dest = self.cache.get_cache_dir()

        try:
            # Ensure destination exists
            if not dry_run:
                dest.mkdir(parents=True, exist_ok=True)

            # Load cache map for incremental sync
            cache_map = self._load_cache_map() if not force else {}

            # Get files to sync
            files_to_sync = self._get_sync_files(source)

            added = []
            modified = []
            deleted = []

            # Determine changes
            for rel_path in files_to_sync:
                src_file = source / rel_path
                dest_file = dest / rel_path

                file_hash = self.cache.compute_hash(src_file)
                cached_entry = cache_map.get(str(rel_path))

                if not cached_entry:
                    added.append(str(rel_path))
                    action = "add"
                elif cached_entry.get("hash") != file_hash:
                    modified.append(str(rel_path))
                    action = "modify"
                else:
                    continue  # No change

                if on_file:
                    on_file(str(rel_path), action)

                if not dry_run:
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dest_file)

                    # Update cache map
                    stat = src_file.stat()
                    cache_map[str(rel_path)] = {
                        "hash": file_hash,
                        "size": stat.st_size,
                        "mtime": stat.st_mtime,
                    }

            # Find deleted files
            for cached_path in list(cache_map.keys()):
                if cached_path not in [str(p) for p in files_to_sync]:
                    deleted.append(cached_path)
                    if on_file:
                        on_file(cached_path, "delete")
                    if not dry_run:
                        dest_file = dest / cached_path
                        if dest_file.exists():
                            dest_file.unlink()
                        del cache_map[cached_path]

            # Save cache map
            if not dry_run:
                self._save_cache_map(cache_map)

            duration_ms = int((time.time() - start_time) * 1000)

            return SyncResult(
                success=True,
                source=source,
                destination=dest,
                files_added=added,
                files_modified=modified,
                files_deleted=deleted,
                duration_ms=duration_ms,
            )

        except Exception as e:
            return SyncResult(
                success=False,
                source=source,
                destination=dest,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

    def _get_sync_files(self, source: Path) -> list[Path]:
        """Get list of files to sync based on include/exclude patterns.

        Args:
            source: Source directory

        Returns:
            List of relative paths to sync
        """
        files = []

        for pattern in self.DEFAULT_INCLUDE:
            if "**" in pattern:
                # Recursive glob
                base_pattern = pattern.replace("/**/*", "").replace("**/*", "")
                base_dir = source / base_pattern if base_pattern else source
                if base_dir.exists() and base_dir.is_dir():
                    for file_path in base_dir.rglob("*"):
                        if file_path.is_file():
                            rel_path = file_path.relative_to(source)
                            if not self._should_exclude(rel_path):
                                files.append(rel_path)
            else:
                file_path = source / pattern
                if file_path.exists() and file_path.is_file():
                    rel_path = file_path.relative_to(source)
                    if not self._should_exclude(rel_path):
                        files.append(rel_path)

        return files

    def _should_exclude(self, rel_path: Path) -> bool:
        """Check if a path should be excluded from sync."""
        path_str = str(rel_path)
        path_parts = rel_path.parts

        for pattern in self.DEFAULT_EXCLUDE:
            if pattern.startswith("*"):
                # Extension match
                if path_str.endswith(pattern[1:]):
                    return True
            elif pattern in path_parts:
                # Directory match
                return True
            elif pattern in path_str:
                # Substring match
                return True

        return False

    def _load_cache_map(self) -> dict:
        """Load cache map from file."""
        if self.cache_map_path.exists():
            with open(self.cache_map_path) as f:
                return json.load(f)
        return {}

    def _save_cache_map(self, cache_map: dict) -> None:
        """Save cache map to file."""
        self.cache_map_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_map_path, "w") as f:
            json.dump(cache_map, f, indent=2)

    def watch(
        self,
        on_sync: Optional[Callable[[SyncResult], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> None:
        """Start watching for file changes and auto-sync.

        Args:
            on_sync: Callback after each sync
            on_error: Callback on errors

        Note:
            This method blocks until interrupted.
        """
        config = WatchConfig.load(self.watch_config_path)

        print(f"👀 Watching {self.project_dir} for changes...")
        print(f"   Syncing to: {self.cache.get_cache_dir()}")
        print(f"   Debounce: {config.debounce_ms}ms")
        print("   Press Ctrl+C to stop")

        # Initial sync
        result = self.sync()
        if on_sync:
            on_sync(result)

        # Determine which watch tool to use
        watch_cmd = self._get_watch_command(config)

        if not watch_cmd:
            print("⚠️  No file watcher available. Falling back to polling mode.")
            self._poll_watch(config, on_sync, on_error)
            return

        try:
            process = subprocess.Popen(
                watch_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.project_dir,
                text=True,
            )

            last_sync = time.time()

            while True:
                line = process.stdout.readline()
                if line:
                    # Debounce
                    now = time.time()
                    if (now - last_sync) * 1000 >= config.debounce_ms:
                        try:
                            result = self.sync()
                            if result.total_changes > 0 and on_sync:
                                on_sync(result)
                            last_sync = now
                        except Exception as e:
                            if on_error:
                                on_error(e)

        except KeyboardInterrupt:
            print("\n👋 Stopping watch...")
        finally:
            if 'process' in locals():
                process.terminate()

    def _get_watch_command(self, config: WatchConfig) -> Optional[list[str]]:
        """Get the appropriate file watch command for the platform."""
        # Try fswatch (macOS)
        if shutil.which("fswatch"):
            cmd = [
                "fswatch",
                "-r",  # Recursive
                "-1",  # Exit after first event (we'll restart)
                "--latency", str(config.debounce_ms / 1000),
            ]
            # Add exclude patterns
            for pattern in self.DEFAULT_EXCLUDE:
                cmd.extend(["--exclude", pattern])
            cmd.append(str(self.project_dir / "skills"))
            cmd.append(str(self.project_dir / "shared"))
            return cmd

        # Try inotifywait (Linux)
        if shutil.which("inotifywait"):
            return [
                "inotifywait",
                "-r",  # Recursive
                "-m",  # Monitor continuously
                "-e", "modify,create,delete",
                str(self.project_dir),
            ]

        return None

    def _poll_watch(
        self,
        config: WatchConfig,
        on_sync: Optional[Callable[[SyncResult], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> None:
        """Fallback polling-based watch."""
        print("   Polling interval: 2s")

        last_cache_map = self._load_cache_map()

        try:
            while True:
                time.sleep(2)

                try:
                    result = self.sync()
                    if result.total_changes > 0:
                        print(f"   📦 Synced {result.total_changes} files")
                        if on_sync:
                            on_sync(result)
                except Exception as e:
                    if on_error:
                        on_error(e)

        except KeyboardInterrupt:
            print("\n👋 Stopping watch...")

    def link(self, force: bool = False) -> bool:
        """Create symbolic link from cache to project directory.

        This is an advanced option that provides zero-delay sync but may
        not work on all platforms or with Claude Code.

        Args:
            force: Remove existing cache and create link

        Returns:
            True if link was created successfully
        """
        cache_dir = self.cache.get_cache_dir()
        parent_dir = cache_dir.parent

        # Ensure parent exists
        parent_dir.mkdir(parents=True, exist_ok=True)

        # Check if cache already exists
        if cache_dir.exists():
            if force:
                if cache_dir.is_symlink():
                    cache_dir.unlink()
                else:
                    shutil.rmtree(cache_dir)
            else:
                print(f"⚠️  Cache already exists: {cache_dir}")
                print("   Use --force to replace with symlink")
                return False

        # Create symlink
        try:
            cache_dir.symlink_to(self.project_dir)
            print(f"✅ Created symlink: {cache_dir} → {self.project_dir}")
            return True
        except OSError as e:
            print(f"❌ Failed to create symlink: {e}")
            print("   This may require administrator privileges on Windows")
            return False

    def unlink(self) -> bool:
        """Remove symbolic link and restore normal cache.

        Returns:
            True if unlink was successful
        """
        cache_dir = self.cache.get_cache_dir()

        if not cache_dir.exists():
            print("ℹ️  No cache exists")
            return True

        if not cache_dir.is_symlink():
            print("ℹ️  Cache is not a symlink")
            return True

        cache_dir.unlink()
        print(f"✅ Removed symlink: {cache_dir}")

        # Sync to restore cache
        print("   Restoring cache...")
        self.sync(force=True)

        return True
