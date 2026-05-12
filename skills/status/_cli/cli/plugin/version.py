"""Version management for plugins.

Handles semantic versioning, version bumping, compatibility checking,
and changelog generation.
"""

import json
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from .exceptions import InvalidVersionError, VersionConflictError, VersionError


class BumpLevel(Enum):
    """Version bump levels following semantic versioning."""
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


@dataclass
class SemanticVersion:
    """Semantic version representation."""
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None

    @classmethod
    def parse(cls, version_str: str) -> "SemanticVersion":
        """Parse a version string into SemanticVersion.

        Args:
            version_str: Version string (e.g., "1.2.3", "1.2.3-beta.1", "1.2.3+build.123")

        Returns:
            SemanticVersion object

        Raises:
            InvalidVersionError: If version format is invalid
        """
        # Pattern: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
        pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?(?:\+([a-zA-Z0-9.-]+))?$"
        match = re.match(pattern, version_str.strip())

        if not match:
            raise InvalidVersionError(version_str)

        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            prerelease=match.group(4),
            build=match.group(5),
        )

    def bump(self, level: BumpLevel) -> "SemanticVersion":
        """Create a new version with bumped level.

        Args:
            level: Which component to bump

        Returns:
            New SemanticVersion with bumped version
        """
        if level == BumpLevel.MAJOR:
            return SemanticVersion(self.major + 1, 0, 0)
        elif level == BumpLevel.MINOR:
            return SemanticVersion(self.major, self.minor + 1, 0)
        else:  # PATCH
            return SemanticVersion(self.major, self.minor, self.patch + 1)

    def __str__(self) -> str:
        """Convert to string."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version

    def __lt__(self, other: "SemanticVersion") -> bool:
        """Compare versions."""
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, SemanticVersion):
            return False
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)


@dataclass
class ChangelogEntry:
    """A single changelog entry."""
    type: str  # feat, fix, docs, refactor, test, chore, breaking
    scope: Optional[str]
    description: str
    commit_hash: str
    author: Optional[str] = None
    breaking: bool = False

    @classmethod
    def from_commit(cls, commit_line: str) -> Optional["ChangelogEntry"]:
        """Parse a git commit line into a ChangelogEntry.

        Expected format: HASH|TYPE(SCOPE): DESCRIPTION|AUTHOR

        Returns:
            ChangelogEntry or None if format doesn't match
        """
        # Pattern for conventional commits
        pattern = r"^([a-f0-9]+)\|(\w+)(?:\(([^)]+)\))?:\s*(.+)\|(.*)$"
        match = re.match(pattern, commit_line.strip())

        if not match:
            return None

        commit_hash, commit_type, scope, description, author = match.groups()

        # Check for breaking change indicators
        breaking = "BREAKING CHANGE" in description or commit_type == "breaking"
        if breaking:
            description = description.replace("BREAKING CHANGE:", "").strip()

        return cls(
            type=commit_type.lower(),
            scope=scope,
            description=description,
            commit_hash=commit_hash[:7],
            author=author or None,
            breaking=breaking,
        )


@dataclass
class Changelog:
    """Changelog for a version."""
    version: str
    date: datetime
    entries: list[ChangelogEntry] = field(default_factory=list)

    @property
    def has_breaking_changes(self) -> bool:
        """Check if changelog contains breaking changes."""
        return any(e.breaking or e.type == "breaking" for e in self.entries)

    @property
    def grouped_entries(self) -> dict[str, list[ChangelogEntry]]:
        """Group entries by type."""
        groups: dict[str, list[ChangelogEntry]] = {}
        for entry in self.entries:
            key = entry.type
            if entry.breaking:
                key = "breaking"
            groups.setdefault(key, []).append(entry)
        return groups

    def to_markdown(self) -> str:
        """Convert to markdown format."""
        lines = [
            f"## [{self.version}] - {self.date.strftime('%Y-%m-%d')}",
            "",
        ]

        type_labels = {
            "breaking": "⚠️ BREAKING CHANGES",
            "feat": "✨ Features",
            "fix": "🐛 Bug Fixes",
            "docs": "📚 Documentation",
            "refactor": "♻️ Refactoring",
            "test": "🧪 Tests",
            "perf": "⚡ Performance",
            "chore": "🔧 Chores",
        }

        for type_key, entries in self.grouped_entries.items():
            label = type_labels.get(type_key, type_key.title())
            lines.append(f"### {label}")
            lines.append("")
            for entry in entries:
                scope = f"**{entry.scope}**: " if entry.scope else ""
                lines.append(f"- {scope}{entry.description} ({entry.commit_hash})")
            lines.append("")

        return "\n".join(lines)


class VersionManager:
    """Manages plugin version operations.

    Handles version bumping, changelog generation, and compatibility checking.
    """

    # Files that contain version information
    VERSION_FILES = [
        "plugin.json",
        ".claude-plugin/marketplace.json",
    ]

    def __init__(self, project_dir: Optional[Path] = None):
        """Initialize version manager.

        Args:
            project_dir: Plugin project directory (default: cwd)
        """
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()

    def get_current_version(self) -> SemanticVersion:
        """Get current version from plugin.json.

        Returns:
            Current version as SemanticVersion
        """
        plugin_json_path = self.project_dir / "plugin.json"
        with open(plugin_json_path) as f:
            data = json.load(f)
        return SemanticVersion.parse(data["version"])

    def get_all_versions(self) -> dict[str, str]:
        """Get versions from all version files.

        Returns:
            Dict mapping file path to version string
        """
        versions = {}
        for rel_path in self.VERSION_FILES:
            file_path = self.project_dir / rel_path
            if file_path.exists():
                with open(file_path) as f:
                    data = json.load(f)
                # Handle nested version in marketplace.json
                if "plugins" in data and data["plugins"]:
                    versions[rel_path] = data["plugins"][0].get("version", "unknown")
                else:
                    versions[rel_path] = data.get("version", "unknown")
        return versions

    def check_version_consistency(self) -> bool:
        """Check if all version files have the same version.

        Returns:
            True if versions are consistent

        Raises:
            VersionConflictError: If versions are inconsistent
        """
        versions = self.get_all_versions()
        unique_versions = set(versions.values())

        if len(unique_versions) > 1:
            raise VersionConflictError(
                list(versions.keys()),
                list(versions.values()),
            )

        return True

    def bump(
        self,
        level: BumpLevel,
        dry_run: bool = False,
    ) -> SemanticVersion:
        """Bump version across all version files.

        Args:
            level: Which component to bump (major, minor, patch)
            dry_run: If True, don't actually modify files

        Returns:
            New version
        """
        current = self.get_current_version()
        new_version = current.bump(level)

        if not dry_run:
            self._update_version_files(str(new_version))

        return new_version

    def _update_version_files(self, new_version: str) -> None:
        """Update version in all version files.

        Args:
            new_version: New version string
        """
        for rel_path in self.VERSION_FILES:
            file_path = self.project_dir / rel_path
            if file_path.exists():
                with open(file_path) as f:
                    data = json.load(f)
                data["version"] = new_version
                with open(file_path, "w") as f:
                    json.dump(data, f, indent=2)
                    f.write("\n")

        # Also update CLAUDE.md version declaration if present
        claude_md = self.project_dir / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text()
            # Pattern: > 多視角並行工作流生態系 v2.3.2
            pattern = r"(> .+) v\d+\.\d+\.\d+"
            replacement = rf"\1 v{new_version}"
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                claude_md.write_text(new_content)

    def generate_changelog(
        self,
        since_tag: Optional[str] = None,
        new_version: Optional[str] = None,
    ) -> Changelog:
        """Generate changelog from git commits.

        Args:
            since_tag: Starting tag (default: latest tag)
            new_version: Version string for the changelog

        Returns:
            Changelog object
        """
        if not since_tag:
            # Get latest tag
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
            )
            since_tag = result.stdout.strip() if result.returncode == 0 else None

        # Get commits since tag
        range_spec = f"{since_tag}..HEAD" if since_tag else "HEAD"
        result = subprocess.run(
            [
                "git", "log", range_spec,
                "--pretty=format:%h|%s|%an",
            ],
            cwd=self.project_dir,
            capture_output=True,
            text=True,
        )

        entries = []
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if line:
                    entry = ChangelogEntry.from_commit(line)
                    if entry:
                        entries.append(entry)

        version = new_version or str(self.get_current_version())
        return Changelog(
            version=version,
            date=datetime.now(),
            entries=entries,
        )

    def check_compatibility(
        self,
        target_version: str,
    ) -> dict[str, list[str]]:
        """Check compatibility between current and target version.

        Args:
            target_version: Version to check against

        Returns:
            Dict with 'compatible' (bool) and 'issues' (list of strings)
        """
        current = self.get_current_version()
        target = SemanticVersion.parse(target_version)

        issues = []

        # Major version change = breaking
        if target.major != current.major:
            issues.append(
                f"Major version change ({current.major} → {target.major}): "
                "May contain breaking API changes"
            )

        # Check for recent breaking changes in git log
        changelog = self.generate_changelog()
        if changelog.has_breaking_changes:
            for entry in changelog.entries:
                if entry.breaking:
                    issues.append(f"Breaking change: {entry.description}")

        return {
            "compatible": len(issues) == 0,
            "current_version": str(current),
            "target_version": target_version,
            "issues": issues,
        }

    def suggest_commit_message(
        self,
        level: BumpLevel,
        new_version: SemanticVersion,
    ) -> str:
        """Suggest a git commit message for version bump.

        Args:
            level: Bump level used
            new_version: New version

        Returns:
            Suggested commit message
        """
        type_map = {
            BumpLevel.MAJOR: "release",
            BumpLevel.MINOR: "feat",
            BumpLevel.PATCH: "fix",
        }
        commit_type = type_map[level]

        return f"{commit_type}(version): bump to v{new_version}"

    def write_changelog(
        self,
        changelog: Changelog,
        prepend: bool = True,
    ) -> None:
        """Write changelog to CHANGELOG.md.

        Args:
            changelog: Changelog to write
            prepend: If True, prepend to existing file
        """
        changelog_path = self.project_dir / "CHANGELOG.md"
        new_content = changelog.to_markdown()

        if prepend and changelog_path.exists():
            existing = changelog_path.read_text()
            # Find first version header and insert before it
            pattern = r"^## \["
            match = re.search(pattern, existing, re.MULTILINE)
            if match:
                content = existing[:match.start()] + new_content + "\n" + existing[match.start():]
            else:
                content = new_content + "\n" + existing
        else:
            header = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"
            content = header + new_content

        changelog_path.write_text(content)
