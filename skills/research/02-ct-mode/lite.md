# CT Lite Mode

Default mode for `/multi-research`.

## Purpose

Add lightweight research discipline without adding heavy artifacts.

## Apply To Every Perspective

- Mark evidence strength for core claims.
- Separate observation, inference, and hypothesis.
- Mark uncertainty when evidence is weak or missing.
- Stay inside the research question and perspective role.
- Include next action for important unresolved questions.

## Output Impact

No extra CT files are required. Include a compact CT section in `meta.yaml` and
the synthesis report:

```yaml
ct_detection:
  selected_mode: lite
  confidence:
  reasons:
  user_override:
  downgrade_applied:
```
