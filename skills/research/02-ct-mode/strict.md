# CT Strict Mode

Use for architecture, risk, product, technical decisions, long-term maintenance,
agent architecture, memory, tool policy, or context engineering.

## Purpose

Make the research output traceable enough to drive later PLAN/TASKS/IMPLEMENT
stages.

## Required Artifacts

Write these files under `.claude/memory/research/{topic-id}/`:

```text
ct-stack.yaml
ct-compliance.md
risk-policy.yaml
```

## Additional Requirements

- Every core claim must be supported by evidence or labeled as hypothesis.
- High-impact recommendations must include risk and mitigation.
- Conflicts must be preserved unless explicitly resolved.
- Low-confidence conclusions cannot become final recommendations.
- Synthesis must include CT compliance summary.
