# Perspectives System

> Centralized perspective catalog for multi-agent workflows

## Overview

The Perspectives System provides a unified, centralized catalog of analytical perspectives used across all skills in the multi-agent workflow. Each perspective represents a specialized viewpoint or role that contributes unique insights during different phases of work.

**Key Benefits:**
- **Single Source of Truth**: All perspective definitions in `catalog.yaml`
- **Consistent Behavior**: Same perspective behaves identically across skills
- **Easy Maintenance**: Update once, apply everywhere
- **Flexible Composition**: Combine perspectives using presets or custom selections

## Quick Start

### Using Perspectives in a Skill

Reference perspectives from the catalog using their IDs:

```yaml
# In your skill's SKILL.md or configuration
perspectives:
  mode: standard           # quick (2) | standard (4) | deep (6) | custom
  selection: auto          # Let the system choose based on category
  # Or specify explicitly:
  # ids: [architect, risk-analyst, estimator, ux-advocate]
```

### Referencing Shared Perspectives

In any skill document, use the `@shared` reference:

```markdown
## Perspectives

Uses perspectives from @shared/perspectives/catalog.yaml:
- architect
- risk-analyst
- tdd-enforcer
```

## Catalog Structure

The `catalog.yaml` file contains:

### 1. Metadata

Defines severity levels, model tiers, and research methods:

```yaml
metadata:
  severity_levels:
    - id: critical
      description: "Must fix, blocks release"
    - id: high
      description: "Should fix, affects quality"
    # ...

  model_tiers:
    - id: opus      # Complex decisions, conflict resolution
    - id: sonnet    # Standard deep analysis
    - id: haiku     # Quick tasks, formatting

  research_methods:
    - id: deep      # Deep thinking, no external search
    - id: search    # Web/codebase search
    - id: explore   # Codebase exploration
    - id: observe   # Real-time observation and feedback
```

### 2. Categories

Groups perspectives by workflow phase:

| Category | Description | Applicable Skills |
|----------|-------------|-------------------|
| `research` | Information gathering and analysis | research |
| `plan` | Architecture and risk assessment | plan |
| `tasks` | Work decomposition | tasks |
| `implement` | Code quality supervision | implement |
| `review` | Code review | review |
| `verify` | Testing and validation | verify |
| `cross-cutting` | Multi-phase perspectives | all |

### 3. Perspective Definitions

Each perspective includes:

```yaml
- id: architect                    # Unique identifier
  name: System Architect           # Display name
  category: plan                   # Category ID
  focus: "Technical feasibility"   # Brief focus area
  responsibilities:                # What this perspective does
    - Evaluate technical feasibility
    - Design component structure
    - Define interface specifications
  output_format:                   # Expected output structure
    sections:
      - name: Technical Assessment
        description: "Feasibility analysis"
    deliverables:
      - "Architecture diagram"
      - "Component list"
  model_tier: sonnet               # Recommended model
  method: deep                     # Research method
  priority_weight: 0.95            # Conflict resolution weight (0-1)
  tags: [architecture, design]     # Searchable tags
  triggers:                        # Auto-activation keywords
    - "architecture"
    - "system design"
  applicable_skills:               # Override category default
    - plan
    - tasks
```

### 4. Presets

Pre-defined perspective combinations:

| Preset | Count | Use Case |
|--------|-------|----------|
| `quick` | 2 | Simple tasks, initial assessment |
| `standard` | 4 | General work, balanced coverage |
| `deep` | 6 | Complex/high-risk tasks |
| `custom` | N | User-specified selection |

Example preset definition:

```yaml
presets:
  standard:
    description: "Standard depth with 4 perspectives"
    perspective_count: 4
    by_skill:
      plan:
        perspectives: [architect, risk-analyst, estimator, ux-advocate]
        rationale: "Technical + Risk + Estimation + UX"
```

### 5. Composition Rules

Guidelines for combining perspectives:

```yaml
composition_rules:
  recommended_pairs:
    - [architect, risk-analyst]
    - [tdd-enforcer, security-auditor]

  dependencies:
    task-decomposer:
      suggests: [dependency-analyst]
      reason: "Task decomposition needs dependency analysis"
```

### 6. Dynamic Adjustments

Automatic weight boosts based on context:

```yaml
dynamic_adjustments:
  topic_boosts:
    - pattern: "security|auth|password"
      boost:
        security-auditor: 1.5
        compliance-checker: 1.2

  context_adjustments:
    high_risk_project:
      boost:
        risk-analyst: 1.3
        security-auditor: 1.3
```

## Available Perspectives

### Research Phase

| ID | Name | Model | Focus |
|----|------|-------|-------|
| `architecture` | Architecture Analyst | sonnet | System structure, design patterns |
| `cognitive` | Cognitive Researcher | sonnet | Methodology, mental models |
| `workflow` | Workflow Designer | haiku | Execution flow, integration |
| `industry` | Industry Researcher | haiku | Best practices, case studies |

### Plan Phase

| ID | Name | Model | Focus |
|----|------|-------|-------|
| `architect` | System Architect | sonnet | Technical feasibility, components |
| `risk-analyst` | Risk Analyst | sonnet | Risk identification, mitigation |
| `estimator` | Estimation Expert | haiku | Effort estimation, scheduling |
| `ux-advocate` | UX Advocate | haiku | User experience, API design |

### Tasks Phase

| ID | Name | Model | Focus |
|----|------|-------|-------|
| `dependency-analyst` | Dependency Analyst | sonnet | Task dependencies, critical path |
| `task-decomposer` | Task Decomposer | haiku | Work breakdown, granularity |
| `test-planner` | Test Planner | haiku | TDD mapping, coverage targets |
| `risk-preventor` | Risk Preventor | haiku | Risk tasks, prevention measures |

### Implement Phase

| ID | Name | Model | Focus |
|----|------|-------|-------|
| `tdd-enforcer` | TDD Guardian | haiku | Test-first, coverage |
| `performance-optimizer` | Performance Optimizer | sonnet | Time/space complexity |
| `security-auditor` | Security Auditor | sonnet | OWASP, input validation |
| `maintainer` | Maintainability Expert | haiku | Readability, refactoring |

### Review Phase

| ID | Name | Model | Focus |
|----|------|-------|-------|
| `code-quality` | Code Quality Reviewer | haiku | Style, patterns, SOLID |
| `test-coverage` | Test Coverage Reviewer | haiku | Coverage, edge cases |
| `documentation` | Documentation Reviewer | haiku | API docs, comments |
| `integration` | Integration Reviewer | sonnet | Backward compatibility, contracts |

### Verify Phase

| ID | Name | Model | Focus |
|----|------|-------|-------|
| `functional-tester` | Functional Tester | haiku | Happy path, use cases |
| `edge-case-hunter` | Edge Case Hunter | sonnet | Boundary conditions, stress |
| `regression-checker` | Regression Checker | haiku | Existing functionality |
| `acceptance-validator` | Acceptance Validator | sonnet | Requirements, DoD |

### Cross-Cutting

| ID | Name | Model | Focus |
|----|------|-------|-------|
| `data-architect` | Data Architect | sonnet | Database design, migration |
| `ops-engineer` | Ops Engineer | haiku | Deployment, monitoring |
| `accessibility-specialist` | Accessibility Specialist | haiku | WCAG, a11y |
| `compliance-checker` | Compliance Checker | sonnet | Regulations, privacy |

### Deep Mode (Specialized)

| ID | Name | Category | Focus |
|----|------|----------|-------|
| `parallel-optimizer` | Parallel Optimizer | tasks | Parallel execution, efficiency |
| `doc-planner` | Doc Planner | tasks | Documentation planning |
| `i18n-specialist` | i18n Specialist | implement | Internationalization |
| `performance-tester` | Performance Tester | verify | Load/stress testing |
| `security-tester` | Security Tester | verify | Penetration testing |

## Adding New Perspectives

### Step 1: Define in catalog.yaml

Add your perspective to the `perspectives` section:

```yaml
perspectives:
  # ... existing perspectives ...

  - id: my-new-perspective
    name: My New Expert
    category: implement  # or appropriate category
    focus: "Specific area of expertise"
    responsibilities:
      - First responsibility
      - Second responsibility
    output_format:
      sections:
        - name: Section Name
          description: "What this section covers"
      deliverables:
        - "Expected output 1"
        - "Expected output 2"
    model_tier: haiku  # haiku | sonnet | opus
    method: observe    # deep | search | explore | observe
    priority_weight: 0.7
    tags:
      - relevant-tag
    triggers:
      - "keyword1"
      - "keyword2"
```

### Step 2: Add to Presets (Optional)

If your perspective should be part of standard presets:

```yaml
presets:
  deep:
    by_skill:
      implement:
        perspectives: [..., my-new-perspective]
```

### Step 3: Update Composition Rules (Optional)

Add recommended pairs or dependencies:

```yaml
composition_rules:
  recommended_pairs:
    - [my-new-perspective, related-perspective]
```

### Step 4: Add Dynamic Boosts (Optional)

Configure automatic activation:

```yaml
dynamic_adjustments:
  topic_boosts:
    - pattern: "my-keyword|another-keyword"
      boost:
        my-new-perspective: 1.5
```

## Expertise Frameworks

For complex perspectives, use external expertise frameworks:

```yaml
- id: security-auditor
  # ... other fields ...
  expertise_framework: "@shared/perspectives/expertise-frameworks/security.yaml"
```

Available frameworks in `expertise-frameworks/`:
- `security.yaml` - Security audit checklist
- `performance.yaml` - Performance optimization guidelines
- `architecture.yaml` - Architecture evaluation criteria
- `testing.yaml` - Testing strategy framework

## Model Selection Guidelines

| Use Case | Recommended Model | Reason |
|----------|-------------------|--------|
| Complex analysis | `sonnet` | Deep reasoning required |
| Quick formatting | `haiku` | Speed over depth |
| Conflict resolution | `opus` | Highest quality judgment |
| Real-time observation | `haiku` | Fast feedback loop |
| Code exploration | `sonnet` | Understanding context |

## CLI Tool

Use the query tool to explore perspectives:

```bash
# List all perspectives
./scripts/list-perspectives.sh

# Filter by category
./scripts/list-perspectives.sh --category research

# Filter by skill
./scripts/list-perspectives.sh --skill implement

# Show perspective details
./scripts/list-perspectives.sh --show tdd-enforcer

# List preset combinations
./scripts/list-perspectives.sh --preset standard
```

## Output Format

Perspectives should produce reports following this template:

```markdown
# {Perspective Name} Report

**Perspective ID**: {id}
**Execution Time**: {timestamp}
**Topic**: {topic}

## Core Findings

1. Finding 1
2. Finding 2
3. Finding 3

## Detailed Analysis

{analysis by focus areas}

## Recommendations

{actionable recommendations}

## Confidence Level

High / Medium / Low

---
*Produced by {perspective_name}*
```

## Related Resources

- `@shared/perspectives/base-perspective.md` - Perspective definition format
- `@shared/perspectives/expertise-frameworks/` - Specialized knowledge frameworks
- `@shared/config/model-routing.yaml` - Model selection configuration
- `@shared/coordination/map-phase.md` - Parallel execution patterns
