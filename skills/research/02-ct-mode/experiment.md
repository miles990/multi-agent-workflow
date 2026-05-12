# CT Experiment Mode

Use for papers, experiments, benchmark design, ablation, evaluation, harnesses,
model comparison, reproducible research, and claims that need proof.

## Purpose

Turn multi-agent research into testable hypotheses and evaluation design.

## Required Artifacts

Write these files under `.claude/memory/research/{topic-id}/`:

```text
ct-stack.yaml
ct-compliance.md
risk-policy.yaml
hypotheses.yaml
experiment-plan.md
eval-rubric.yaml
failure-modes.md
```

## Additional Requirements

- Each hypothesis must define independent variable, dependent variable, control,
  metric, and falsification condition.
- Include at least one negative or failure case.
- Define what evidence would confirm, weaken, or falsify the claim.
- Report experiment readiness and missing materials.
