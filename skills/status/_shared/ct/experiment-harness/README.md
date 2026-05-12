# CT Experiment Harness

Use this harness when CT-experiment mode produces a testable hypothesis. It
turns research claims into repeatable benchmark cases and scores the generated
artifacts.

## Flow

```text
hypotheses.yaml
→ experiment-plan.md
→ experiments/{topic-id}/cases.yaml
→ experiments/{topic-id}/run-config.yaml
→ experiments/{topic-id}/rubric.yaml
→ score-run.py or run-matrix.py
→ results.jsonl
→ analysis.md / condition-comparison.md
```

## Conditions

Recommended treatment groups:

- `no_ct`
- `ct_lite`
- `ct_strict`
- `ct_experiment`
- `ct_experiment_closed_loop`

Each case should be run under each condition with the same prompt and expected
artifact contract.

## Required Files

```text
experiments/{topic-id}/
├── cases.yaml
├── run-config.yaml
├── rubric.yaml
├── results.jsonl
├── condition-comparison.md
└── analysis.md
```

## Batch Condition Comparison

Use `run-matrix.py` when the same case has artifacts for multiple CT
conditions:

```bash
python shared/ct/experiment-harness/run-matrix.py \
  --cases experiments/{topic-id}/cases.yaml \
  --conditions no_ct,ct_lite,ct_strict,ct_experiment \
  --runs-root experiments/{topic-id}/runs \
  --output experiments/{topic-id}/results.jsonl
```

Expected run layout:

```text
experiments/{topic-id}/runs/
└── CTD-001/
    ├── no_ct/
    ├── ct_lite/
    ├── ct_strict/
    └── ct_experiment/
```

The runner scores each `{case_id}/{condition}` directory and writes both
`results.jsonl` and `condition-comparison.md`.
