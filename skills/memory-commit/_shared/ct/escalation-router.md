# CT Escalation Router

The CT Escalation Router runs before `/multi-research` starts MAP. It selects a
research constraint mode without forcing the user to choose one manually.

## Modes

| Mode | Use |
|------|-----|
| `off` | Explicit user override, quick drafts, or non-research notes |
| `lite` | Default research mode: evidence, uncertainty, drift guard |
| `strict` | Architecture, risk, product, technical decisions |
| `experiment` | Hypotheses, evaluation, benchmark, reproducible research |

Default mode is `lite`.

## Decision Order

1. Check user override first:
   - `--no-ct` or `--ct off` -> `off`
   - `--ct lite` -> `lite`
   - `--ct strict` -> `strict`
   - `--ct experiment` -> `experiment`
2. Apply command flags:
   - `--quick` prefers `lite`
   - `--deep` raises the floor to `strict`
3. Score the request with [escalation-rules.yaml](escalation-rules.yaml).
4. Apply downgrade guards such as "快速", "先粗略", or "不用太詳細".
5. Let the model add reasons or detect missing intent, but do not let it ignore
   explicit override or downgrade guards.
6. Select `ct_mode` and write the detection result to `meta.yaml`.

## Required Output

```yaml
ct_detection:
  selected_mode: lite | strict | experiment | off
  confidence: 0.0
  reasons:
    - "reason"
  user_override: false
  downgrade_applied: false
  score:
    lite: 0.0
    strict: 0.0
    experiment: 0.0
```

## Mode Effects

| Mode | Artifacts |
|------|-----------|
| `off` | No CT artifacts |
| `lite` | Evidence / uncertainty / drift guard in prompts and synthesis |
| `strict` | `ct-stack.yaml`, `ct-compliance.md`, `risk-policy.yaml` |
| `experiment` | strict artifacts plus `hypotheses.yaml`, `experiment-plan.md`, `eval-rubric.yaml`, `failure-modes.md` |

## Guardrails

- Do not over-escalate when the user explicitly asks for a quick rough pass.
- Do not downgrade explicit experiment requests.
- Do not classify a single architecture keyword as `experiment` without evidence,
  benchmark, hypothesis, or validation intent.
- Record reasons even when the mode is `lite`; future stages inherit the result.
