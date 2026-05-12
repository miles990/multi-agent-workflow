"""
REVIEW 階段 Prompt 模板
"""

from typing import Any, Dict

from ..config.models import PerspectiveConfig
from .base import (
    build_system_context,
    build_perspective_header,
    build_json_output_format,
    build_previous_outputs,
)


REVIEW_OUTPUT_SCHEMA = """
```json
{
  "perspective_id": "string",
  "perspective_name": "string",
  "summary": "string",
  "issues": [
    {
      "id": "string - e.g., ISSUE-001",
      "title": "string",
      "description": "string",
      "severity": "BLOCKER | HIGH | MEDIUM | LOW | INFO",
      "category": "bug | security | performance | style | maintainability | documentation",
      "file": "string - file path if applicable",
      "line": "number - line number if applicable",
      "suggestion": "string - how to fix"
    }
  ],
  "approval": "approved | approved_with_comments | changes_requested"
}
```
"""


def get_review_perspective_prompt(
    perspective: PerspectiveConfig,
    context: Dict[str, Any],
) -> str:
    """生成審查階段的視角 Prompt"""
    topic = context.get("topic", "")

    parts = []

    parts.append(build_system_context(context))
    parts.append(build_perspective_header(perspective))
    parts.append(build_previous_outputs(context))

    parts.append(f"""
## Task

Review the implementation for:

**{topic}**

As a **{perspective.name}**, conduct a thorough review from your perspective.

### Review Guidelines

1. **Use the tools** to read and analyze the code
2. **Focus on your expertise area**
3. **Categorize issues by severity**:
   - BLOCKER: Must fix before merge
   - HIGH: Should fix before merge
   - MEDIUM: Should fix eventually
   - LOW: Nice to fix
   - INFO: Informational comment
4. **Provide actionable suggestions**
5. **Give overall approval status**

### Focus On

{chr(10).join(f"- {area}" for area in perspective.focus_areas)}
""")

    parts.append(build_json_output_format(REVIEW_OUTPUT_SCHEMA))

    return "\n".join(parts)


def get_review_synthesis_prompt(
    perspective_contents: Dict[str, Dict],
    context: Dict[str, Any],
) -> str:
    """生成審查階段的綜合報告 Prompt"""
    topic = context.get("topic", "")

    parts = []
    parts.append(build_system_context(context))

    parts.append(f"""
# Task: Synthesize Code Review

Combine review feedback from all perspectives for:

**{topic}**

## Review Perspectives
""")

    total_issues = 0
    for pid, content in perspective_contents.items():
        name = content.get("perspective_name", pid)
        issues = content.get("issues", [])
        approval = content.get("approval", "unknown")
        total_issues += len(issues)
        parts.append(f"- **{name}**: {len(issues)} issues, {approval}")

    parts.append(f"""
## Total Issues: {total_issues}

## Synthesis Requirements

1. **Deduplicate Issues**: Merge similar issues from different perspectives
2. **Prioritize by Severity**: BLOCKER > HIGH > MEDIUM > LOW > INFO
3. **Categorize**: Group by category for easier handling
4. **Final Verdict**: Overall approval status based on all perspectives
5. **Action Items**: Clear next steps
""")

    parts.append(build_json_output_format("""
```json
{
  "stage_id": "REVIEW",
  "consensus": {
    "score": "number",
    "points": ["string"]
  },
  "key_insights": [...],
  "merged_issues": [
    {
      "id": "string",
      "title": "string",
      "severity": "string",
      "category": "string",
      "description": "string",
      "sources": ["perspective IDs"]
    }
  ],
  "action_items": [...],
  "final_approval": "approved | approved_with_comments | changes_requested"
}
```
"""))

    return "\n".join(parts)
