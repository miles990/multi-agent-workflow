"""Stage artifact manifests.

This module centralizes the canonical artifact paths produced by each workflow
stage. It intentionally starts as a path/name manifest so stage behavior can
move behind this interface incrementally.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from .models import StageID


@dataclass(frozen=True)
class StageArtifactManifest:
    """Canonical artifact names and paths for one workflow stage."""

    stage_id: StageID
    primary_output: str
    primary_output_key: str
    perspective_dir: str = "perspectives"
    summary_dir: str = "summaries"
    perspective_json_pattern: str = "{perspective_id}.json"
    perspective_markdown_pattern: str = "{perspective_id}.md"
    synthesis_json: str = "synthesis.json"
    synthesis_markdown: str = "synthesis.md"

    @property
    def required_outputs(self) -> list[str]:
        """Output files callers should expect this stage to produce."""
        return [self.primary_output]

    def perspective_dir_path(self, stage_dir: Path) -> Path:
        """Return the perspective artifact directory for a stage directory."""
        return stage_dir / self.perspective_dir

    def summary_dir_path(self, stage_dir: Path) -> Path:
        """Return the summary artifact directory for a stage directory."""
        return stage_dir / self.summary_dir

    def perspective_json_path(self, stage_dir: Path, perspective_id: str) -> Path:
        """Return the JSON artifact path for one perspective."""
        filename = self.perspective_json_pattern.format(perspective_id=perspective_id)
        return self.perspective_dir_path(stage_dir) / filename

    def perspective_markdown_path(self, stage_dir: Path, perspective_id: str) -> Path:
        """Return the Markdown artifact path for one perspective."""
        filename = self.perspective_markdown_pattern.format(perspective_id=perspective_id)
        return self.perspective_dir_path(stage_dir) / filename

    def synthesis_json_path(self, stage_dir: Path) -> Path:
        """Return the structured synthesis artifact path."""
        return self.summary_dir_path(stage_dir) / self.synthesis_json

    def synthesis_markdown_path(self, stage_dir: Path) -> Path:
        """Return the Markdown synthesis artifact path."""
        return stage_dir / self.synthesis_markdown

    def primary_output_path(self, stage_dir: Path) -> Path:
        """Return the primary artifact path for this stage."""
        return stage_dir / self.primary_output

    def ensure_directories(self, stage_dir: Path) -> None:
        """Create artifact directories below a stage directory."""
        self.perspective_dir_path(stage_dir).mkdir(parents=True, exist_ok=True)
        self.summary_dir_path(stage_dir).mkdir(parents=True, exist_ok=True)


_STAGE_ARTIFACTS: Dict[StageID, StageArtifactManifest] = {
    StageID.RESEARCH: StageArtifactManifest(
        stage_id=StageID.RESEARCH,
        primary_output="synthesis.md",
        primary_output_key="synthesis",
    ),
    StageID.PLAN: StageArtifactManifest(
        stage_id=StageID.PLAN,
        primary_output="implementation-plan.md",
        primary_output_key="implementation_plan",
    ),
    StageID.TASKS: StageArtifactManifest(
        stage_id=StageID.TASKS,
        primary_output="tasks.yaml",
        primary_output_key="tasks",
    ),
    StageID.IMPLEMENT: StageArtifactManifest(
        stage_id=StageID.IMPLEMENT,
        primary_output="implementation.md",
        primary_output_key="implementation",
    ),
    StageID.REVIEW: StageArtifactManifest(
        stage_id=StageID.REVIEW,
        primary_output="review-summary.md",
        primary_output_key="review_summary",
    ),
    StageID.VERIFY: StageArtifactManifest(
        stage_id=StageID.VERIFY,
        primary_output="verification.md",
        primary_output_key="verification",
    ),
}


def get_stage_artifact_manifest(stage_id: StageID) -> StageArtifactManifest:
    """Return the artifact manifest for a workflow stage."""
    return _STAGE_ARTIFACTS[stage_id]


def list_stage_artifact_manifests() -> list[StageArtifactManifest]:
    """Return all stage artifact manifests in declaration order."""
    return list(_STAGE_ARTIFACTS.values())


def get_checkpoint_patterns() -> list[str]:
    """Return file patterns that mark a workflow stage checkpoint."""
    return [
        f"**/{manifest.primary_output}"
        for manifest in list_stage_artifact_manifests()
    ]


def get_checkpoint_stage_map() -> dict[str, StageID]:
    """Return checkpoint filename to stage mapping."""
    return {
        manifest.primary_output: manifest.stage_id
        for manifest in list_stage_artifact_manifests()
    }


def detect_stage_from_checkpoint(checkpoint_file: str | Path) -> Optional[StageID]:
    """Infer the workflow stage from a checkpoint artifact path."""
    file_name = Path(checkpoint_file).name.lower()
    return get_checkpoint_stage_map().get(file_name)
