# CT Failure Miner

Failure mining converts CT violations and weak conclusions into reusable research
material.

## Inputs

- Perspective reports
- Cross validation output
- CT compliance report
- Quality gate results
- Experiment plan
- CT retrospective
- Workflow logs and tool failures

## Failure Mode Format

```yaml
failure_mode:
  id: FM001
  category: evidence | drift | conflict | experiment | output
  description: string
  trigger: string
  observed_in: string
  severity: low | medium | high | blocker
  prevention: string
  regression_case: string
```

## Required Output

Write `failure-modes.md` with:

- Recurrent CT violations
- Root causes
- Regression prompts or evaluation cases
- Prevention rules to add to future CT stacks
- Workflow failures that should become regression cases

## Closed-Loop Use

After verification, feed `ct-retrospective.md` back into failure mining. Any
workflow failure that affected quality, observability, or reproducibility should
be recorded as a regression case before proposing changes.
