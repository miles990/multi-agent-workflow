#!/usr/bin/env python3
"""Summarize CT experiment benchmark results."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description='Analyze CT experiment results.jsonl')
    parser.add_argument('--results', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    rows = []
    with Path(args.results).open('r', encoding='utf-8') as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    by_condition = defaultdict(list)
    for row in rows:
        by_condition[row['condition']].append(row)

    lines = ['# CT Experiment Analysis', '']
    lines.append('| Condition | Runs | Pass Rate | Avg Score | Avg Drift | Avg Unsupported |')
    lines.append('|---|---:|---:|---:|---:|---:|')
    for condition in sorted(by_condition):
        group = by_condition[condition]
        runs = len(group)
        pass_rate = sum(1 for row in group if row.get('pass')) / runs
        avg_score = sum(row['score'] for row in group) / runs
        avg_drift = sum(row['metrics']['drift_event_count'] for row in group) / runs
        avg_unsupported = (
            sum(row['metrics']['unsupported_claim_rate'] for row in group) / runs
        )
        lines.append(
            f'| {condition} | {runs} | {pass_rate:.2f} | {avg_score:.3f} | '
            f'{avg_drift:.2f} | {avg_unsupported:.3f} |'
        )

    lines.extend(['', '## Interpretation', ''])
    lines.append(
        'Treat these scores as benchmark evidence, not proof. Causal claims require '
        'multiple cases, repeated runs, and comparison against the control condition.'
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Wrote {output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
