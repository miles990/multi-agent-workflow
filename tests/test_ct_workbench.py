import json
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_ct_contract_validator_passes_repository_contracts() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "shared/ct/validate-contracts.py"),
            "--root",
            str(REPO_ROOT),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "CT contracts OK" in result.stdout


def test_claims_registry_validator_accepts_valid_claims(tmp_path: Path) -> None:
    claims_dir = tmp_path / "claims"
    claims_dir.mkdir()
    (claims_dir / "architecture.claims.yaml").write_text(
        yaml.safe_dump(
            {
                "claims": [
                    {
                        "id": "C001",
                        "statement": "Layered CT reduces unsupported claims.",
                        "evidence_type": "hypothesis",
                        "confidence": "medium",
                        "risk": "medium",
                        "ct_layer": "experiment",
                    },
                    {
                        "id": "C002",
                        "statement": "The run produced an experiment plan.",
                        "evidence_type": "source",
                        "confidence": "high",
                        "risk": "low",
                        "ct_layer": "evidence",
                        "source_ref": "experiment-plan.md",
                    },
                ]
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "shared/ct/validate-claims.py"),
            "--claims-dir",
            str(claims_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Claims registry OK" in result.stdout


def test_claims_registry_validator_rejects_invalid_claims(tmp_path: Path) -> None:
    claims_dir = tmp_path / "claims"
    claims_dir.mkdir()
    (claims_dir / "workflow.claims.yaml").write_text(
        yaml.safe_dump(
            {
                "claims": [
                    {
                        "id": "C001",
                        "statement": "A source claim without source_ref.",
                        "evidence_type": "source",
                        "confidence": "certain",
                        "risk": "low",
                        "ct_layer": "evidence",
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "shared/ct/validate-claims.py"),
            "--claims-dir",
            str(claims_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "invalid confidence" in result.stderr
    assert "requires source_ref" in result.stderr


def test_experiment_matrix_runner_scores_conditions(tmp_path: Path) -> None:
    cases_path = tmp_path / "cases.yaml"
    cases_path.write_text(
        yaml.safe_dump(
            {
                "cases": [
                    {
                        "id": "CTD-001",
                        "prompt": "Evaluate CT condition comparison.",
                        "required_artifacts": [
                            "synthesis.md",
                            "ct-compliance.md",
                            "hypotheses.yaml",
                            "experiment-plan.md",
                        ],
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    runs_root = tmp_path / "runs"
    for condition, evidence_coverage, unsupported in [
        ("no_ct", 0.45, 0.40),
        ("ct_lite", 0.82, 0.10),
    ]:
        run_dir = runs_root / "CTD-001" / condition
        run_dir.mkdir(parents=True)
        for name in [
            "synthesis.md",
            "ct-compliance.md",
            "hypotheses.yaml",
            "experiment-plan.md",
        ]:
            (run_dir / name).write_text(
                "\n".join(
                    [
                        f"evidence_coverage: {evidence_coverage}",
                        "hypothesis_testability_score: 0.75",
                        f"unsupported_claim_rate: {unsupported}",
                    ]
                ),
                encoding="utf-8",
            )

    results_path = tmp_path / "results.jsonl"
    comparison_path = tmp_path / "condition-comparison.md"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "shared/ct/experiment-harness/run-matrix.py"),
            "--cases",
            str(cases_path),
            "--conditions",
            "no_ct,ct_lite",
            "--runs-root",
            str(runs_root),
            "--output",
            str(results_path),
            "--comparison-output",
            str(comparison_path),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    rows = [
        json.loads(line)
        for line in results_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert [row["condition"] for row in rows] == ["no_ct", "ct_lite"]
    assert rows[0]["pass"] is False
    assert rows[1]["pass"] is True

    comparison = comparison_path.read_text(encoding="utf-8")
    assert "| no_ct |" in comparison
    assert "| ct_lite |" in comparison

