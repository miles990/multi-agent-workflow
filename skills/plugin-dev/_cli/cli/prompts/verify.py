"""
VERIFY 階段 Prompt 模板
"""

from typing import Any, Dict

from ..config.models import PerspectiveConfig
from .base import (
    build_system_context,
    build_perspective_header,
    build_json_output_format,
    build_previous_outputs,
)


VERIFY_OUTPUT_SCHEMA = """
```json
{
  "perspective_id": "string",
  "perspective_name": "string",
  "summary": "string",
  "test_results": [
    {
      "test_id": "string",
      "test_name": "string",
      "status": "passed | failed | skipped | error",
      "details": "string - failure details if any",
      "duration_ms": "number - optional"
    }
  ],
  "coverage": {
    "line_coverage": "number - percentage",
    "branch_coverage": "number - percentage",
    "function_coverage": "number - percentage"
  },
  "verdict": "pass | fail | conditional"
}
```
"""


def get_verify_perspective_prompt(
    perspective: PerspectiveConfig,
    context: Dict[str, Any],
) -> str:
    """生成驗證階段的視角 Prompt"""
    topic = context.get("topic", "")

    parts = []

    parts.append(build_system_context(context))
    parts.append(build_perspective_header(perspective))
    parts.append(build_previous_outputs(context))

    parts.append(f"""
## Task

Verify the implementation for:

**{topic}**

As a **{perspective.name}**, conduct verification from your perspective.

### Verification Guidelines

1. **Run tests** using Bash tool if needed
2. **Check coverage** and quality metrics
3. **Verify acceptance criteria** are met
4. **Test edge cases** relevant to your focus
5. **Provide final verdict**

### Verdict Options

- **pass**: All criteria met, ready for release
- **fail**: Critical issues found, cannot release
- **conditional**: Minor issues, can release with caveats

### Focus On

{chr(10).join(f"- {area}" for area in perspective.focus_areas)}
""")

    parts.append(build_json_output_format(VERIFY_OUTPUT_SCHEMA))

    return "\n".join(parts)


def get_verify_synthesis_prompt(
    perspective_contents: Dict[str, Dict],
    context: Dict[str, Any],
) -> str:
    """生成驗證階段的綜合報告 Prompt"""
    topic = context.get("topic", "")

    parts = []
    parts.append(build_system_context(context))

    parts.append(f"""
# Task: Release Decision

Make final release decision for:

**{topic}**

## Verification Perspectives
""")

    for pid, content in perspective_contents.items():
        name = content.get("perspective_name", pid)
        verdict = content.get("verdict", "unknown")
        tests = content.get("test_results", [])
        passed = sum(1 for t in tests if t.get("status") == "passed")
        total = len(tests)
        parts.append(f"- **{name}**: {verdict} ({passed}/{total} tests)")

    parts.append("""
## Decision Criteria

1. **All Critical Tests Pass**: No failed functional or regression tests
2. **Coverage Thresholds Met**: Line coverage >= 80%
3. **No Unresolved Blockers**: All BLOCKER issues addressed
4. **Acceptance Criteria Verified**: All requirements satisfied
5. **Documentation Complete**: User and developer docs updated

## Release Decision

Based on all verification perspectives, provide:

1. **Overall Verdict**: pass, fail, or conditional
2. **Release Notes**: What's included in this release
3. **Known Issues**: Any remaining issues
4. **Rollback Plan**: If something goes wrong
""")

    parts.append(build_json_output_format("""
```json
{
  "stage_id": "VERIFY",
  "consensus": {
    "score": "number",
    "points": ["string"]
  },
  "key_insights": [...],
  "overall_verdict": "pass | fail | conditional",
  "release_notes": ["string"],
  "known_issues": ["string"],
  "action_items": [...]
}
```
"""))

    return "\n".join(parts)
