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
→ score-run.py
→ results.jsonl
→ analysis.md
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
└── analysis.md
```

