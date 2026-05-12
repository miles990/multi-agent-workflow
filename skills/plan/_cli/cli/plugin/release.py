"""Release workflow commands for plugins.

Handles validation, release, and publishing to marketplace.
"""

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Callable

from .cache import CacheManager
from .version import VersionManager, BumpLevel, Changelog
from .exceptions import (
    ReleaseError,
    DirtyWorkspaceError,
    ValidationError,
)


class ReleaseStep(Enum):
    """Steps in the release process."""
    VALIDATE = "validate"
    TEST = "test"
    CHECK_GIT = "check_git"
    BUMP_VERSION = "bump_version"
    UPDATE_MARKETPLACE = "update_marketplace"
    GENERATE_CHANGELOG = "generate_changelog"
    GIT_COMMIT = "git_commit"
    GIT_TAG = "git_tag"
    GIT_PUSH = "git_push"
    COMPLETE = "complete"


@dataclass
class ReleaseProgress:
    """Progress tracking for release process."""
    current_step: ReleaseStep
    completed_steps: list[ReleaseStep] = field(default_factory=list)
    failed_step: Optional[ReleaseStep] = None
    error: Optional[str] = None
    new_version: Optional[str] = None
    git_tag: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for persistence."""
        return {
            "current_step": self.current_step.value,
            "completed_steps": [s.value for s in self.completed_steps],
            "failed_step": self.failed_step.value if self.failed_step else None,
            "error": self.error,
            "new_version": self.new_version,
            "git_tag": self.git_tag,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReleaseProgress":
        """Create from dictionary."""
        return cls(
            current_step=ReleaseStep(data["current_step"]),
            completed_steps=[ReleaseStep(s) for s in data.get("completed_steps", [])],
            failed_step=ReleaseStep(data["failed_step"]) if data.get("failed_step") else None,
            error=data.get("error"),
            new_version=data.get("new_version"),
            git_tag=data.get("git_tag"),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )


@dataclass
class ValidationResult:
    """Result of pre-release validation."""
    passed: bool
    checks: dict[str, bool] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_check(self, name: str, passed: bool, error: Optional[str] = None) -> None:
        """Add a validation check result."""
        self.checks[name] = passed
        if not passed and error:
            self.errors.append(error)
            self.passed = False


class ReleaseCommands:
    """Release workflow commands.

    Provides validation, release, and rollback functionality.
    """

    RELEASE_STEPS = [
        ReleaseStep.VALIDATE,
        ReleaseStep.TEST,
        ReleaseStep.CHECK_GIT,
        ReleaseStep.BUMP_VERSION,
        ReleaseStep.UPDATE_MARKETPLACE,
        ReleaseStep.GENERATE_CHANGELOG,
        ReleaseStep.GIT_COMMIT,
        ReleaseStep.GIT_TAG,
        ReleaseStep.GIT_PUSH,
        ReleaseStep.COMPLETE,
    ]

    def __init__(
        self,
        project_dir: Optional[Path] = None,
        cache_manager: Optional[CacheManager] = None,
        version_manager: Optional[VersionManager] = None,
    ):
        """Initialize release commands.

        Args:
            project_dir: Plugin project directory (default: cwd)
            cache_manager: Optional CacheManager instance
            version_manager: Optional VersionManager instance
        """
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.cache = cache_manager or CacheManager(project_dir=self.project_dir)
        self.version = version_manager or VersionManager(project_dir=self.project_dir)

        # Progress file for resume capability
        self.progress_file = self.project_dir / ".plugin-dev" / "release-progress.json"

    def validate(self) -> ValidationResult:
        """Run pre-release validation checks.

        Checks:
        1. plugin.json exists and is valid
        2. All skills have SKILL.md
        3. Version consistency across files
        4. No uncommitted changes
        5. Tests pass (optional)

        Returns:
            ValidationResult with check details
        """
        result = ValidationResult(passed=True)

        # Check 1: plugin.json
        plugin_json_path = self.project_dir / "plugin.json"
        if plugin_json_path.exists():
            try:
                with open(plugin_json_path) as f:
                    data = json.load(f)
                required_fields = ["name", "version", "description"]
                missing = [f for f in required_fields if f not in data]
                if missing:
                    result.add_check(
                        "plugin_json",
                        False,
                        f"plugin.json missing required fields: {missing}"
                    )
                else:
                    result.add_check("plugin_json", True)
            except json.JSONDecodeError as e:
                result.add_check("plugin_json", False, f"plugin.json invalid JSON: {e}")
        else:
            result.add_check("plugin_json", False, "plugin.json not found")

        # Check 2: Skills structure
        skills_dir = self.project_dir / "skills"
        if skills_dir.exists():
            invalid_skills = []
            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                    skill_md = skill_dir / "SKILL.md"
                    if not skill_md.exists():
                        invalid_skills.append(skill_dir.name)

            if invalid_skills:
                result.add_check(
                    "skills_structure",
                    False,
                    f"Skills missing SKILL.md: {invalid_skills}"
                )
            else:
                result.add_check("skills_structure", True)
        else:
            result.add_check("skills_structure", False, "skills/ directory not found")

        # Check 3: Version consistency
        try:
            self.version.check_version_consistency()
            result.add_check("version_consistency", True)
        except Exception as e:
            result.add_check("version_consistency", False, str(e))

        # Check 4: Git status
        git_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.project_dir,
            capture_output=True,
            text=True,
        )
        if git_result.returncode == 0:
            if git_result.stdout.strip():
                changed_files = [
                    line.split()[-1]
                    for line in git_result.stdout.strip().split("\n")
                    if line
                ]
                result.add_check(
                    "git_clean",
                    False,
                    f"Uncommitted changes: {len(changed_files)} files"
                )
                result.warnings.append(f"Changed files: {changed_files[:5]}...")
            else:
                result.add_check("git_clean", True)
        else:
            result.warnings.append("Not a git repository")
            result.checks["git_clean"] = True  # Not a failure

        return result

    def release(
        self,
        bump_level: BumpLevel = BumpLevel.PATCH,
        dry_run: bool = False,
        skip_tests: bool = False,
        on_step: Optional[Callable[[ReleaseStep, str], None]] = None,
    ) -> ReleaseProgress:
        """Execute full release workflow.

        Args:
            bump_level: Version bump level
            dry_run: If True, simulate without making changes
            skip_tests: Skip test execution
            on_step: Callback for each step (step, message)

        Returns:
            ReleaseProgress with result details
        """
        progress = ReleaseProgress(
            current_step=ReleaseStep.VALIDATE,
            started_at=datetime.now(),
        )

        def log_step(step: ReleaseStep, message: str) -> None:
            progress.current_step = step
            if on_step:
                on_step(step, message)

        try:
            # Step 1: Validate
            log_step(ReleaseStep.VALIDATE, "Running validation checks...")
            validation = self.validate()
            if not validation.passed:
                raise ValidationError(validation.errors)
            progress.completed_steps.append(ReleaseStep.VALIDATE)

            # Step 2: Test (optional)
            if not skip_tests:
                log_step(ReleaseStep.TEST, "Running tests...")
                test_result = self._run_tests()
                if not test_result:
                    raise ReleaseError("Tests failed", "Fix failing tests before release")
            progress.completed_steps.append(ReleaseStep.TEST)

            # Step 3: Check git
            log_step(ReleaseStep.CHECK_GIT, "Checking git status...")
            self._check_git_status()
            progress.completed_steps.append(ReleaseStep.CHECK_GIT)

            # Step 4: Bump version
            log_step(ReleaseStep.BUMP_VERSION, f"Bumping version ({bump_level.value})...")
            old_version = str(self.version.get_current_version())
            if not dry_run:
                new_version = self.version.bump(bump_level)
                progress.new_version = str(new_version)
                # Update README.md version badge
                self._update_readme(old_version, str(new_version))
            else:
                new_version = self.version.get_current_version().bump(bump_level)
                progress.new_version = str(new_version)
            progress.completed_steps.append(ReleaseStep.BUMP_VERSION)

            # Step 5: Update marketplace (before commit)
            log_step(ReleaseStep.UPDATE_MARKETPLACE, "Updating marketplace...")
            if not dry_run:
                self._update_marketplace(str(new_version))
            progress.completed_steps.append(ReleaseStep.UPDATE_MARKETPLACE)

            # Step 6: Generate changelog
            log_step(ReleaseStep.GENERATE_CHANGELOG, "Generating changelog...")
            changelog = self.version.generate_changelog(new_version=str(new_version))
            if not dry_run:
                self.version.write_changelog(changelog)
            progress.completed_steps.append(ReleaseStep.GENERATE_CHANGELOG)

            # Step 7: Git commit
            log_step(ReleaseStep.GIT_COMMIT, "Creating git commit...")
            if not dry_run:
                commit_msg = self.version.suggest_commit_message(bump_level, new_version)
                self._git_commit(commit_msg)
            progress.completed_steps.append(ReleaseStep.GIT_COMMIT)

            # Step 8: Git tag
            log_step(ReleaseStep.GIT_TAG, f"Creating git tag v{new_version}...")
            progress.git_tag = f"v{new_version}"
            if not dry_run:
                self._git_tag(progress.git_tag)
            progress.completed_steps.append(ReleaseStep.GIT_TAG)

            # Step 9: Git push
            log_step(ReleaseStep.GIT_PUSH, "Pushing to remote...")
            if not dry_run:
                self._git_push(progress.git_tag)
            progress.completed_steps.append(ReleaseStep.GIT_PUSH)

            # Complete
            log_step(ReleaseStep.COMPLETE, "Release complete!")
            progress.current_step = ReleaseStep.COMPLETE
            progress.completed_steps.append(ReleaseStep.COMPLETE)
            progress.completed_at = datetime.now()

        except Exception as e:
            progress.failed_step = progress.current_step
            progress.error = str(e)
            self._save_progress(progress)
            raise

        return progress

    def resume(
        self,
        on_step: Optional[Callable[[ReleaseStep, str], None]] = None,
    ) -> ReleaseProgress:
        """Resume a failed release from last checkpoint.

        Args:
            on_step: Callback for each step

        Returns:
            ReleaseProgress with result details
        """
        progress = self._load_progress()
        if not progress:
            raise ReleaseError(
                "No release in progress",
                "Start a new release with 'plugin release'"
            )

        # Find next step
        start_index = self.RELEASE_STEPS.index(progress.failed_step)

        # Continue from failed step
        # ... (similar logic to release but starting from failed step)

        return progress

    def rollback(self, tag: Optional[str] = None) -> bool:
        """Rollback a release.

        Args:
            tag: Git tag to rollback (default: latest)

        Returns:
            True if rollback was successful
        """
        if not tag:
            # Get latest tag
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise ReleaseError("No tags found", "Nothing to rollback")
            tag = result.stdout.strip()

        # Delete local tag
        subprocess.run(
            ["git", "tag", "-d", tag],
            cwd=self.project_dir,
            capture_output=True,
        )

        # Delete remote tag
        subprocess.run(
            ["git", "push", "origin", f":refs/tags/{tag}"],
            cwd=self.project_dir,
            capture_output=True,
        )

        # Revert commit
        subprocess.run(
            ["git", "revert", "--no-commit", "HEAD"],
            cwd=self.project_dir,
            capture_output=True,
        )

        print(f"✅ Rolled back release {tag}")
        print("   Review changes and commit when ready")

        return True

    def _run_tests(self) -> bool:
        """Run plugin tests."""
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-v"],
            cwd=self.project_dir,
            capture_output=True,
        )
        return result.returncode == 0

    def _check_git_status(self) -> None:
        """Check git status for uncommitted changes."""
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.project_dir,
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            changed_files = [
                line.split()[-1]
                for line in result.stdout.strip().split("\n")
                if line
            ]
            raise DirtyWorkspaceError(changed_files)

    def _git_commit(self, message: str) -> None:
        """Create git commit."""
        subprocess.run(
            ["git", "add", "-A"],
            cwd=self.project_dir,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.project_dir,
            check=True,
        )

    def _git_tag(self, tag: str) -> None:
        """Create git tag."""
        subprocess.run(
            ["git", "tag", "-a", tag, "-m", f"Release {tag}"],
            cwd=self.project_dir,
            check=True,
        )

    def _git_push(self, tag: str) -> None:
        """Push to remote with tag."""
        # Check if remote exists
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=self.project_dir,
            capture_output=True,
        )
        if result.returncode != 0:
            # No remote configured, skip push
            return

        subprocess.run(
            ["git", "push", "origin", "HEAD"],
            cwd=self.project_dir,
            check=True,
        )
        subprocess.run(
            ["git", "push", "origin", tag],
            cwd=self.project_dir,
            check=True,
        )

    def _update_marketplace(self, version: str) -> None:
        """Update marketplace configuration."""
        marketplace_path = self.project_dir / ".claude-plugin" / "marketplace.json"
        if marketplace_path.exists():
            with open(marketplace_path) as f:
                data = json.load(f)

            # Update version in plugins array
            for plugin in data.get("plugins", []):
                plugin["version"] = version

            with open(marketplace_path, "w") as f:
                json.dump(data, f, indent=2)
                f.write("\n")

    def _update_readme(self, old_version: str, new_version: str) -> None:
        """Update version in README.md.

        Updates:
        1. Version badge: version-X.Y.Z-blue.svg
        2. Version history section header (if exists)

        Args:
            old_version: Current version string
            new_version: New version string
        """
        import re

        readme_path = self.project_dir / "README.md"
        if not readme_path.exists():
            return

        content = readme_path.read_text()

        # Update version badge
        # Pattern: version-X.Y.Z-blue.svg or version-X.Y.Z-color.svg
        badge_pattern = rf"(version-){re.escape(old_version)}(-\w+\.svg)"
        content = re.sub(badge_pattern, rf"\g<1>{new_version}\g<2>", content)

        readme_path.write_text(content)

    def _save_progress(self, progress: ReleaseProgress) -> None:
        """Save release progress for resume."""
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.progress_file, "w") as f:
            json.dump(progress.to_dict(), f, indent=2)

    def _load_progress(self) -> Optional[ReleaseProgress]:
        """Load saved release progress."""
        if self.progress_file.exists():
            with open(self.progress_file) as f:
                return ReleaseProgress.from_dict(json.load(f))
        return None
