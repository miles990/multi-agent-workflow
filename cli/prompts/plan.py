"""
PLAN 階段 Prompt 模板
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


def get_plan_perspective_prompt(
    perspective: PerspectiveConfig,
    context: Dict[str, Any],
) -> str:
    """生成規劃階段的視角 Prompt"""
    topic = context.get("topic", "")

    parts = []

    parts.append(build_system_context(context))
    parts.append(build_perspective_header(perspective))

    # 前階段輸出
    parts.append(build_previous_outputs(context))

    parts.append(f"""
## Task

Based on the research findings, design an implementation plan for:

**{topic}**

As a **{perspective.name}**, provide your perspective on the design.

### Design Guidelines

1. **Review research findings** from the previous phase
2. **Design components** relevant to your expertise
3. **Define interfaces** and interactions
4. **Identify risks** and mitigation strategies
5. **Propose milestones** and success criteria

### Focus Your Design On

{chr(10).join(f"- {area}" for area in perspective.focus_areas)}
""")

    parts.append(build_json_output_format(PERSPECTIVE_REPORT_SCHEMA_DESC))

    return "\n".join(parts)


def get_plan_synthesis_prompt(
    perspective_contents: Dict[str, Dict],
    context: Dict[str, Any],
) -> str:
    """生成規劃階段的綜合報告 Prompt"""
    from .base import SYNTHESIS_REPORT_SCHEMA_DESC

    topic = context.get("topic", "")

    parts = []
    parts.append(build_system_context(context))

    parts.append(f"""
# Task: Create Implementation Plan

Synthesize design perspectives into a cohesive implementation plan for:

**{topic}**

## Design Perspectives
""")

    for pid, content in perspective_contents.items():
        name = content.get("perspective_name", pid)
        summary = content.get("summary", "")
        parts.append(f"- **{name}**: {summary}")

    parts.append("""
## Plan Requirements

1. **Component Design**: Define major components and their responsibilities
2. **Interface Definitions**: Specify how components interact
3. **Risk Assessment**: Identify and mitigate risks
4. **Milestones**: Define clear milestones with success criteria
5. **Dependencies**: Map out external and internal dependencies
""")

    parts.append(build_json_output_format(SYNTHESIS_REPORT_SCHEMA_DESC))

    return "\n".join(parts)
