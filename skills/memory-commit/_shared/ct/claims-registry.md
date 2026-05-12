# CT Claims Registry

CT claims registry is the structured claim layer for CT research artifacts. It
keeps evidence, uncertainty, risk, and CT layer metadata out of free-form
Markdown so compliance and metrics can be verified mechanically.

## Location

```text
.claude/memory/research/{topic-id}/claims/
├── architecture.claims.yaml
├── cognitive.claims.yaml
├── workflow.claims.yaml
└── industry.claims.yaml
```

Each perspective may still write `perspectives/{id}.md` and
`summaries/{id}.yaml`; claims registry is the machine-checkable companion.

## Format

```yaml
claims:
  - id: C001
    statement: "Layered CT reduces unsupported recommendations in agent research."
    evidence_type: hypothesis
    confidence: medium
    risk: medium
    ct_layer: experiment
    source_ref: "hypotheses.yaml#H001"
    uncertainty: "Needs condition comparison across no_ct/lite/strict/experiment."
```

Valid values are defined in [claims-schema.yaml](claims-schema.yaml).

## Metrics Enabled

- `unsupported_claim_rate`
- `evidence_coverage`
- `contradiction_resolution_rate`
- `claim_confidence_distribution`
- `high_risk_claim_count`

## Validation

```bash
python shared/ct/validate-claims.py \
  --claims-dir .claude/memory/research/{topic-id}/claims
```

Validation fails when required fields are missing, enum values are invalid, IDs
are duplicated, or source-backed claims omit `source_ref`.

