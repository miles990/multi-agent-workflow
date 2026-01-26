"""
IMPLEMENT 階段 Prompt 模板
"""

from typing import Any, Dict

from ..config.models import PerspectiveConfig
from .base import (
    build_system_context,
    build_perspective_header,
    build_json_output_format,
    build_previous_outputs,
    PERSPECTIVE_REPORT_SCHEMA_DESC,
)


def get_implement_perspective_prompt(
    perspective: PerspectiveConfig,
    context: Dict[str, Any],
) -> str:
    """生成實作階段的視角 Prompt"""
    topic = context.get("topic", "")

    parts = []

    parts.append(build_system_context(context))
    parts.append(build_perspective_header(perspective))
    parts.append(build_previous_outputs(context))

    parts.append(f"""
## Task

Implement the planned tasks for:

**{topic}**

As a **{perspective.name}**, guide the implementation from your perspective.

### Implementation Guidelines

1. **TDD First**: Write tests before implementation
2. **Small Commits**: Make atomic, focused changes
3. **Quality Focus**: Follow coding standards and best practices
4. **Continuous Review**: Self-review before moving forward
5. **Documentation**: Update docs as you go

### Focus On

{chr(10).join(f"- {area}" for area in perspective.focus_areas)}
""")

    parts.append(build_json_output_format(PERSPECTIVE_REPORT_SCHEMA_DESC))

    return "\n".join(parts)


def get_implement_synthesis_prompt(
    perspective_contents: Dict[str, Dict],
    context: Dict[str, Any],
) -> str:
    """生成實作階段的綜合報告 Prompt"""
    from .base import SYNTHESIS_REPORT_SCHEMA_DESC

    topic = context.get("topic", "")

    parts = []
    parts.append(build_system_context(context))

    parts.append(f"""
# Task: Summarize Implementation Progress

Synthesize implementation feedback for:

**{topic}**

## Implementation Perspectives
""")

    for pid, content in perspective_contents.items():
        name = content.get("perspective_name", pid)
        summary = content.get("summary", "")
        parts.append(f"- **{name}**: {summary}")

    parts.append("""
## Summary Requirements

1. **Task Completion**: Report on completed vs remaining tasks
2. **Test Coverage**: Summarize test results and coverage
3. **Issues Found**: List any issues or blockers
4. **Quality Assessment**: Overall code quality assessment
5. **Next Steps**: What needs to happen next
""")

    parts.append(build_json_output_format(SYNTHESIS_REPORT_SCHEMA_DESC))

    return "\n".join(parts)
