# CT Autonomous Upgrade

Autonomous upgrade is the controlled execution step after CT retrospective and
self-upgrade proposal. It lets the workflow improve itself only when the change
is bounded, evidenced, and verifiable.

## Position In The Loop

```text
VERIFY OUTPUT
↓
CT RETROSPECTIVE
↓
SELF-UPGRADE PROPOSAL
↓
AUTONOMOUS UPGRADE DECISION
↓
PATCH + VERIFY, or STOP FOR HUMAN APPROVAL
```

## Decision Rules

| Level | Default Action |
|---|---|
| L1 | Record only. Do not patch. |
| L2 | Proposal only. Do not patch. |
| L3 | May patch docs, templates, examples, and non-runtime CT guidance. |
| L4 | May patch router, gates, scripts, or validators only with a focused smoke test. |
| L5 | Must stop for human approval. |

## Required Preconditions

Before applying any autonomous patch:

1. `self-upgrade-proposal.md` exists.
2. The proposal includes evidence and target files.
3. Risk level is not `high` unless the user explicitly requested autonomous
   repair.
4. The change has a verification plan.
5. The working tree is inspected so unrelated user changes are not reverted.

## Required Output

Write `upgrade-decision.yaml`:

```yaml
upgrade_decision:
  proposal:
  automation_level:
  decision: applied | skipped | requires_human_approval
  reason:
  target_files:
  verification:
    commands:
    result:
  rollback_plan:
```

If patching, also write `upgrade-report.md`:

```markdown
# Upgrade Report

## Applied Changes

## Evidence

## Verification

## Residual Risk

## Rollback Plan
```

## Hard Stops

Stop and request approval when:

- The proposal changes phase boundaries, memory model, install model, or agent
  authority.
- Verification cannot be run.
- The patch would weaken a quality gate without adding a replacement check.
- The target files contain unrelated user edits that make the patch ambiguous.

