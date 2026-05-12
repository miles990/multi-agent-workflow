# CT Drift Detector

Drift detection identifies when an agent, phase, or synthesis step leaves the
compiled CT boundary.

## Drift Types

- `topic_drift`: output answers a different question.
- `role_drift`: perspective ignores its assigned focus.
- `evidence_drift`: conclusion strength exceeds evidence strength.
- `phase_drift`: phase produces artifacts intended for a later phase.
- `constraint_drift`: output violates a CT rule while still seeming useful.

## Detection Heuristics

1. Compare each section against the research question and objective.
2. Check whether claims map to the CT output contract.
3. Flag recommendations that lack evidence, uncertainty, or next action.
4. Flag perspective reports that omit their perspective-specific CT.
5. Flag reduce outputs that merge contradictory findings without rationale.

## Output

Record drift events in `ct-compliance.md` and aggregate counts in `metrics.yaml`.
