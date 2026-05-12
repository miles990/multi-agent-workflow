#!/usr/bin/env python3
"""Run CT experiment scoring across cases and conditions."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description='Score a CT experiment condition matrix')
    parser.add_argument('--cases', required=True, help='cases.yaml path')
    parser.add_argument('--conditions', required=True, help='Comma-separated condition names')
    parser.add_argument('--runs-root', required=True, help='Root containing {case_id}/{condition}/ artifacts')
    parser.add_argument('--output', required=True, help='results.jsonl output path')
    parser.add_argument('--comparison-output', help='condition-comparison.md output path')
    args = parser.parse_args()

    cases = _load_cases(Path(args.cases))
    conditions = [item.strip() for item in args.conditions.split(',') if item.strip()]
    if not conditions:
        print('ERROR: --conditions must contain at least one condition', file=sys.stderr)
        return 1

    scorer = _load_score_run()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('', encoding='utf-8')

    records = []
    runs_root = Path(args.runs_root)
    for case in cases:
        case_id = str(case['id'])
        required = case.get('required_artifacts') or scorer.DEFAULT_REQUIRED
        for condition in conditions:
            run_dir = runs_root / case_id / condition
            record = _score_run(scorer, run_dir, case_id, condition, required)
            records.append(record)
            with output.open('a', encoding='utf-8') as handle:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n')

    comparison_output = Path(args.comparison_output) if args.comparison_output else output.with_name('condition-comparison.md')
    _write_comparison(records, comparison_output)
    print(f'Wrote {output}')
    print(f'Wrote {comparison_output}')
    return 0 if all(record['pass'] for record in records) else 1


def _load_cases(path: Path) -> list[dict[str, Any]]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise SystemExit('PyYAML is required to read cases.yaml') from exc
    with path.open('r', encoding='utf-8') as handle:
        data = yaml.safe_load(handle) or {}
    cases = data.get('cases')
    if not isinstance(cases, list) or not cases:
        raise SystemExit(f'No cases found in {path}')
    for case in cases:
        if not isinstance(case, dict) or not case.get('id'):
            raise SystemExit(f'Invalid case entry in {path}: {case!r}')
    return cases


def _load_score_run() -> Any:
    path = Path(__file__).with_name('score-run.py')
    spec = importlib.util.spec_from_file_location('score_run', path)
    if spec is None or spec.loader is None:
        raise SystemExit(f'Unable to load scorer: {path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _score_run(
    scorer: Any,
    run_dir: Path,
    case_id: str,
    condition: str,
    required: list[str],
) -> dict[str, Any]:
    present = [name for name in required if (run_dir / name).exists()]
    artifact_completeness = len(present) / len(required) if required else 1.0
    text = scorer._collect_text(run_dir) if run_dir.exists() else ''
    metrics = {
        'drift_event_count': scorer._count_any(text, ['drift_event', 'topic drift', 'role drift']),
        'unsupported_claim_rate': scorer._extract_float(text, 'unsupported_claim_rate', default=1.0),
        'evidence_coverage': scorer._extract_float(text, 'evidence_coverage', default=0.0),
        'hypothesis_testability_score': scorer._extract_float(
            text, 'hypothesis_testability_score', default=0.0
        ),
        'artifact_completeness_score': round(artifact_completeness, 4),
        'repeated_failure_count': scorer._count_any(text, ['repeated_failure', 'repeated failure']),
    }
    return {
        'case_id': case_id,
        'condition': condition,
        'run_dir': str(run_dir),
        'present_artifacts': present,
        'missing_artifacts': [name for name in required if name not in present],
        'metrics': metrics,
        'score': scorer._score(metrics),
        'pass': scorer._passes(metrics),
    }


def _write_comparison(records: list[dict[str, Any]], output: Path) -> None:
    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_condition[record['condition']].append(record)

    lines = ['# CT Condition Comparison', '']
    lines.append('| Condition | Runs | Pass Rate | Avg Score | Avg Drift | Avg Unsupported | Avg Evidence | Avg Testability |')
    lines.append('|---|---:|---:|---:|---:|---:|---:|---:|')
    for condition in sorted(by_condition):
        group = by_condition[condition]
        runs = len(group)
        pass_rate = sum(1 for row in group if row.get('pass')) / runs
        avg_score = sum(row['score'] for row in group) / runs
        avg_drift = sum(row['metrics']['drift_event_count'] for row in group) / runs
        avg_unsupported = sum(row['metrics']['unsupported_claim_rate'] for row in group) / runs
        avg_evidence = sum(row['metrics']['evidence_coverage'] for row in group) / runs
        avg_testability = sum(row['metrics']['hypothesis_testability_score'] for row in group) / runs
        lines.append(
            f'| {condition} | {runs} | {pass_rate:.2f} | {avg_score:.3f} | '
            f'{avg_drift:.2f} | {avg_unsupported:.3f} | {avg_evidence:.3f} | '
            f'{avg_testability:.3f} |'
        )

    lines.extend(['', '## Notes', ''])
    lines.append(
        'Use the same case prompt, model, context budget, and tool policy across '
        'conditions. Treat differences as benchmark evidence until repeated runs '
        'establish stability.'
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('\n'.join(lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    raise SystemExit(main())

