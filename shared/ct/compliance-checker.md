# CT Compliance Checker

The compliance checker runs during REDUCE and before the quality gate. It does
not replace cross validation; it extends it with constraint validation.

## Checks

| Check | Question | Severity |
|------|----------|----------|
| `ct_stack_exists` | Was `ct-stack.yaml` produced before MAP? | blocker |
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

The CT gate fails when `high_ct_violations > 0`, `evidence_coverage < 0.8`, or
`hypothesis_testability_score < 0.7`.
