from pathlib import Path

from cli.config.artifacts import (
    get_stage_artifact_manifest,
    list_stage_artifact_manifests,
)
from cli.config.stages import get_stage
from cli.config.models import StageID


def test_stage_artifact_paths_are_canonical() -> None:
    stage_dir = Path("/tmp/workflows/demo/stages/research")
    manifest = get_stage_artifact_manifest(StageID.RESEARCH)

    assert manifest.perspective_json_path(stage_dir, "architecture") == (
        stage_dir / "perspectives" / "architecture.json"
    )
    assert manifest.perspective_markdown_path(stage_dir, "architecture") == (
        stage_dir / "perspectives" / "architecture.md"
    )
    assert manifest.synthesis_json_path(stage_dir) == (
        stage_dir / "summaries" / "synthesis.json"
    )
    assert manifest.synthesis_markdown_path(stage_dir) == stage_dir / "synthesis.md"
    assert manifest.primary_output_path(stage_dir) == stage_dir / "synthesis.md"


def test_stage_required_outputs_come_from_artifact_manifests() -> None:
    for manifest in list_stage_artifact_manifests():
        stage = get_stage(manifest.stage_id)
        assert stage.required_outputs == manifest.required_outputs


def test_stage_artifact_primary_outputs_match_workflow_stage_names() -> None:
    expected = {
        StageID.RESEARCH: ("synthesis", "synthesis.md"),
        StageID.PLAN: ("implementation_plan", "implementation-plan.md"),
        StageID.TASKS: ("tasks", "tasks.yaml"),
        StageID.IMPLEMENT: ("implementation", "implementation.md"),
        StageID.REVIEW: ("review_summary", "review-summary.md"),
        StageID.VERIFY: ("verification", "verification.md"),
    }

    for stage_id, (output_key, output_file) in expected.items():
        manifest = get_stage_artifact_manifest(stage_id)
        assert manifest.primary_output_key == output_key
        assert manifest.primary_output == output_file


def test_tasks_manifest_keeps_synthesis_markdown_separate_from_yaml_output() -> None:
    manifest = get_stage_artifact_manifest(StageID.TASKS)

    assert manifest.primary_output == "tasks.yaml"
    assert manifest.synthesis_markdown == "synthesis.md"
