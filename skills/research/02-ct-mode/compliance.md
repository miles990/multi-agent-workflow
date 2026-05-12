# CT Compliance for Research

CT compliance runs after cross validation and before final synthesis.

## Checks By Mode

| Check | lite | strict | experiment |
|-------|------|--------|------------|
| Evidence marker | required | required | required |
| Uncertainty marker | required | required | required |
| Drift guard | required | required | required |
| CT stack | optional | required | required |
| Risk policy | optional | required | required |
| Hypothesis variables | optional | optional | required |
| Experiment plan | optional | optional | required |
| Failure mining | optional | recommended | required |

## Violation Handling

- `blocker`: stop synthesis until fixed.
- `high`: request CT revision before final recommendation.
- `medium`: include warning and fix in `ct-compliance.md`.
- `low`: record for future failure mining.

## Summary Shape

```markdown
## CT Compliance

- selected_mode:
- compliance_score:
- unsupported_claims:
- drift_events:
- unresolved_conflicts:
- required_revisions:
```
