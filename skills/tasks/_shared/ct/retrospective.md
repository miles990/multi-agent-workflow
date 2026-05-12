# CT Retrospective

CT retrospective closes the loop after output verification. It checks whether
the selected CT mode was appropriate, whether the workflow itself failed in
recoverable ways, and whether future CT rules should change.

## When To Run

Run after the stage output has passed normal verification:

```text
RUN WORKFLOW
↓
VERIFY OUTPUT
↓
CT RETROSPECTIVE
↓
SELF-UPGRADE PROPOSAL
```

For `/multi-research`, run it after synthesis and quality gate. For
`/orchestrate`, run it after VERIFY or after a terminal failure.

## Inputs

- `meta.yaml`, especially `ct_detection`
- `ct-compliance.md`
- `failure-modes.md`
- quality gate logs
- workflow event logs
- generated artifacts for the selected CT mode
- user corrections or manual intervention notes

## Required Questions

1. Was `selected_mode` correct for the user request?
2. Was there over-escalation that added friction without value?
3. Was there under-escalation that allowed drift, weak evidence, or missing
   experiment design?
4. Did required artifacts exist for the selected mode?
5. Which workflow failures happened during execution?
6. Which failures should become regression cases?
7. Which improvements are safe to propose, and which require human approval?

## Output Contract

Write `ct-retrospective.md`:

```markdown
# CT Retrospective

## Mode Review
- selected_mode:
- expected_mode:
- mode_was_correct:
- over_escalation:
- under_escalation:
- confidence:
- rationale:

## Artifact Review
| Artifact | Required | Present | Notes |
|---|---:|---:|---|

## Workflow Failures
| Failure | Layer | Severity | Evidence | Regression Case |
|---|---|---|---|---|

## Lessons
- ...

## Recommended Updates
| Target | Change | Risk | Automation Level |
|---|---|---|---|
```

## Automation Levels

| Level | Meaning | Allowed Action |
|---|---|---|
| L1 | Record only | Write retrospective artifact |
| L2 | Proposal only | Write self-upgrade proposal |
| L3 | Low-risk docs/rules | Patch templates, docs, examples |
| L4a | Runtime rules | Patch escalation rules or non-critical validators only with tests |
| L4b | Quality gate changes | Proposal only; requires human approval |
| L4c | Workflow script changes | Proposal only; requires human approval |
| L5 | Architecture | Require explicit human approval |
