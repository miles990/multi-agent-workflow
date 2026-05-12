#!/usr/bin/env python3
"""Score CT experiment benchmark runs without external dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_REQUIRED = [
    'synthesis.md',
    'ct-compliance.md',
    'hypotheses.yaml',
    'experiment-plan.md',
    'eval-rubric.yaml',
    'failure-modes.md',
]


def main() -> int:
    parser = argparse.ArgumentParser(description='Score CT experiment artifacts')
    parser.add_argument('--run-dir', required=True, help='Directory containing run artifacts')
    parser.add_argument('--condition', required=True, help='Experiment condition name')
    parser.add_argument('--case-id', required=True, help='Benchmark case id')
    parser.add_argument('--output', required=True, help='results.jsonl path')
    parser.add_argument(
        '--required',
        nargs='*',
        default=DEFAULT_REQUIRED,
        help='Required artifact filenames',
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    required = list(args.required)
    present = [name for name in required if (run_dir / name).exists()]
    artifact_completeness = len(present) / len(required) if required else 1.0

    text = _collect_text(run_dir)
    metrics = {
        'drift_event_count': _count_any(text, ['drift_event', 'topic drift', 'role drift']),
        'unsupported_claim_rate': _extract_float(text, 'unsupported_claim_rate', default=0.0),
        'evidence_coverage': _extract_float(text, 'evidence_coverage', default=0.0),
        'hypothesis_testability_score': _extract_float(
            text, 'hypothesis_testability_score', default=0.0
        ),
        'artifact_completeness_score': round(artifact_completeness, 4),
        'repeated_failure_count': _count_any(text, ['repeated_failure', 'repeated failure']),
    }

    score = _score(metrics)
    record = {
        'case_id': args.case_id,
        'condition': args.condition,
        'run_dir': str(run_dir),
        'present_artifacts': present,
        'missing_artifacts': [name for name in required if name not in present],
        'metrics': metrics,
        'score': score,
        'pass': _passes(metrics),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n')

    print(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if record['pass'] else 1


def _collect_text(run_dir: Path) -> str:
    parts = []
    for path in run_dir.glob('*'):
        if path.is_file() and path.suffix in {'.md', '.yaml', '.yml', '.json'}:
            try:
                parts.append(path.read_text(encoding='utf-8'))
            except UnicodeDecodeError:
                continue
    return '\n'.join(parts)


def _count_any(text: str, needles: list[str]) -> int:
    lowered = text.lower()
    return sum(lowered.count(needle.lower()) for needle in needles)


def _extract_float(text: str, key: str, default: float) -> float:
    found = default
    for raw in text.splitlines():
        line = raw.strip().strip('-').strip()
        if not line.startswith(key):
            continue
        _, _, value = line.partition(':')
        value = value.strip().strip('"').strip("'")
        try:
            found = float(value)
        except ValueError:
            continue
    return found


def _score(metrics: dict[str, Any]) -> float:
    score = 0.0
    score += max(0.0, 1.0 - min(float(metrics['drift_event_count']), 5.0) / 5.0) * 0.25
    score += max(0.0, 1.0 - float(metrics['unsupported_claim_rate'])) * 0.20
    score += min(float(metrics['evidence_coverage']), 1.0) * 0.20
    score += min(float(metrics['hypothesis_testability_score']), 1.0) * 0.15
    score += min(float(metrics['artifact_completeness_score']), 1.0) * 0.10
    score += max(0.0, 1.0 - min(float(metrics['repeated_failure_count']), 5.0) / 5.0) * 0.10
    return round(score, 4)


def _passes(metrics: dict[str, Any]) -> bool:
    return (
        float(metrics['evidence_coverage']) >= 0.8
        and float(metrics['hypothesis_testability_score']) >= 0.7
        and float(metrics['artifact_completeness_score']) >= 0.8
        and float(metrics['unsupported_claim_rate']) <= 0.15
    )


if __name__ == '__main__':
    raise SystemExit(main())
