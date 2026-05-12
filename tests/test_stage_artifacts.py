from pathlib import Path

import yaml

from cli.config.artifacts import (
    detect_stage_from_checkpoint,
    get_checkpoint_patterns,
    get_checkpoint_stage_map,
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


def test_checkpoint_patterns_are_derived_from_primary_outputs() -> None:
    assert get_checkpoint_patterns() == [
        f"**/{manifest.primary_output}"
        for manifest in list_stage_artifact_manifests()
    ]


def test_checkpoint_stage_detection_uses_manifest_outputs() -> None:
    assert get_checkpoint_stage_map() == {
        manifest.primary_output: manifest.stage_id
        for manifest in list_stage_artifact_manifests()
    }

    for manifest in list_stage_artifact_manifests():
        path = f".claude/memory/workflows/demo/stages/{manifest.stage_id.value.lower()}/{manifest.primary_output}"
        assert detect_stage_from_checkpoint(path) == manifest.stage_id

    assert detect_stage_from_checkpoint("unknown.md") is None


def test_post_write_hook_uses_manifest_checkpoint_patterns() -> None:
    from scripts.hooks import post_write

    assert post_write.CHECKPOINT_PATTERNS == get_checkpoint_patterns()

    for pattern in get_checkpoint_patterns():
        filename = pattern.removeprefix("**/")
        assert post_write._is_checkpoint_file(f".claude/memory/demo/{filename}")


def test_workflow_commit_facade_detects_manifest_checkpoints() -> None:
    from scripts.git_lib.facade import WorkflowCommitFacade

    facade = WorkflowCommitFacade(Path.cwd())

    for manifest in list_stage_artifact_manifests():
        assert (
            facade._detect_stage_from_checkpoint(manifest.primary_output)
            == manifest.stage_id.value.lower()
        )


def test_commit_settings_checkpoint_patterns_match_manifest() -> None:
    config_path = Path("shared/config/commit-settings.yaml")
    config = yaml.safe_load(config_path.read_text())

    assert config["checkpoint_commit"]["patterns"] == get_checkpoint_patterns()
