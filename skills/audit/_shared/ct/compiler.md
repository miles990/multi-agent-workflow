# CT Compiler

CT Compile turns a research request into an explicit constraint stack before any
multi-agent work begins.

## Inputs

- Research topic and objective
- Scope boundaries and non-goals
- Evidence requirements
- Risk boundaries
- Output format expectations
- Verification and evaluation criteria

## Outputs

Write the compiled stack to:

```text
.claude/memory/research/{topic-id}/
|-- ct-stack.yaml
|-- eval-rubric.yaml
|-- risk-policy.yaml
`-- output-contract.md
```

## Compile Steps

1. Normalize the topic into `topic-id`.
2. Select CT layers from [taxonomy.yaml](taxonomy.yaml).
3. Convert user constraints into explicit rules with severity.
4. Add evidence and uncertainty policies.
5. Generate an output contract for all perspective agents.
6. Generate an eval rubric with measurable thresholds.

## Minimum CT Stack

Every CT research run must include:

- `base`: task boundary, honesty, and traceability rules.
- `evidence`: source and claim support rules.
- `risk`: conflict, confidence, and recommendation limits.
- `experiment`: hypothesis and variable requirements.
- `output`: report contract.
- `eval`: scoring dimensions and thresholds.
