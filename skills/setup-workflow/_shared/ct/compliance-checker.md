# CT Compliance Checker

The compliance checker runs during REDUCE for `strict` and `experiment` modes.
`lite` mode only applies evidence / uncertainty / drift guard notes in synthesis
and is evaluated by `CT_LITE`; it must not require `ct-stack.yaml`.

## Checks

| Check | Question | Severity |
|------|----------|----------|
| `ct_stack_exists` | Was `ct-stack.yaml` produced before MAP in strict/experiment mode? | blocker |
| `claim_has_evidence` | Does each core claim have evidence or hypothesis status? | high |
| `uncertainty_marked` | Are low-evidence conclusions labeled with uncertainty? | high |
| `no_topic_drift` | Did agents stay within the topic and CT boundaries? | medium |
| `conflict_not_collapsed` | Were contradictions preserved or resolved explicitly? | high |
| `hypothesis_testable` | Can each hypothesis be evaluated with variables and metrics? | medium |
| `output_contract_met` | Does the report include required CT sections? | medium |

## Report Format

```markdown
# CT Compliance Report

## Summary
- compliance_score:
- drift_events:
- unsupported_claims:
- high_ct_violations:
- evidence_coverage:
- hypothesis_testability_score:
- experiment_readiness_score:

## Violations
| Agent | CT Layer | Violation | Severity | Fix |
|---|---|---|---|---|

## Gate Decision
- pass:
- required_revisions:
```

## Scoring

Start from 100 and subtract:

- blocker: 40
- high: 20
- medium: 10
- low: 3

Gate failures are mode-scoped:

- `CT_LITE` fails when evidence / uncertainty markings are missing or obvious
  drift exceeds the lite guard.
- `CT_STRICT` fails when `ct-stack.yaml` or `ct-compliance.md` is missing,
  `high_ct_violations > 0`, or `evidence_coverage < 0.8`.
- `CT_EXPERIMENT` fails when hypotheses or experiment plan are missing,
  `hypothesis_testability_score < 0.7`, or `experiment_readiness_score < 0.7`.
