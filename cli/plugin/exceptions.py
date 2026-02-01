"""Plugin management exceptions."""

from pathlib import Path
from typing import Optional


class PluginError(Exception):
    """Base exception for plugin operations."""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)

    def __str__(self) -> str:
        if self.suggestion:
            return f"{self.message}\n  💡 Suggestion: {self.suggestion}"
        return self.message


class CacheError(PluginError):
    """Cache-related errors."""
    pass


class CacheNotFoundError(CacheError):
    """Cache directory not found."""

    def __init__(self, cache_path: Path):
        super().__init__(
            f"Cache directory not found: {cache_path}",
            "Run 'plugin dev sync' to create the cache, or install the plugin first."
        )
        self.cache_path = cache_path


class CacheCorruptedError(CacheError):
    """Cache is corrupted or invalid."""

    def __init__(self, cache_path: Path, reason: str):
        super().__init__(
            f"Cache corrupted at {cache_path}: {reason}",
            "Run 'plugin cache clean' and then 'plugin dev sync' to rebuild."
        )
        self.cache_path = cache_path
        self.reason = reason


class SyncError(PluginError):
    """Synchronization errors."""
    pass


class SyncFailedError(SyncError):
    """Sync operation failed."""

    def __init__(self, source: Path, dest: Path, reason: str):
        super().__init__(
            f"Sync failed from {source} to {dest}: {reason}",
            "Check file permissions and disk space."
        )
        self.source = source
        self.dest = dest
        self.reason = reason


class VersionError(PluginError):
    """Version-related errors."""
    pass


class InvalidVersionError(VersionError):
    """Invalid version format."""

    def __init__(self, version: str):
        super().__init__(
            f"Invalid version format: {version}",
            "Use semantic versioning format: MAJOR.MINOR.PATCH (e.g., 1.2.3)"
        )
        self.version = version


class VersionConflictError(VersionError):
    """Version conflict detected."""

    def __init__(self, files: list[str], versions: list[str]):
        super().__init__(
            f"Version mismatch across files: {dict(zip(files, versions))}",
            "Run 'plugin version sync' to align versions."
        )
        self.files = files
        self.versions = versions


class ReleaseError(PluginError):
    """Release-related errors."""
    pass


class DirtyWorkspaceError(ReleaseError):
    """Workspace has uncommitted changes."""

    def __init__(self, changed_files: list[str]):
        super().__init__(
            f"Cannot release with uncommitted changes: {len(changed_files)} files modified",
            "Commit or stash your changes first."
        )
        self.changed_files = changed_files


class ValidationError(ReleaseError):
    """Pre-release validation failed."""

    def __init__(self, failures: list[str]):
        super().__init__(
            f"Validation failed: {', '.join(failures)}",
            "Fix the issues and try again."
        )
        self.failures = failures
