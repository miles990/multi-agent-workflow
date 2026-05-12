"""
RESEARCH 階段 Prompt 模板
"""

from typing import Any, Dict

from ..config.models import PerspectiveConfig
from .base import (
    build_system_context,
    build_perspective_header,
    build_json_output_format,
    PERSPECTIVE_REPORT_SCHEMA_DESC,
)


def get_research_perspective_prompt(
    perspective: PerspectiveConfig,
    context: Dict[str, Any],
) -> str:
    """
    生成研究階段的視角 Prompt

    Args:
        perspective: 視角配置
        context: 執行上下文

    Returns:
        完整 Prompt
    """
    topic = context.get("topic", "")

    parts = []

    # 系統上下文
    parts.append(build_system_context(context))

    # 視角標頭
    parts.append(build_perspective_header(perspective))

    # 任務描述
    parts.append(f"""
## Task

You are conducting research for the following topic:

**{topic}**

As a **{perspective.name}**, analyze this topic from your specialized perspective.

### Research Guidelines

1. **Explore the codebase** if relevant using Read, Glob, Grep tools
2. **Search for best practices** using WebSearch if needed
3. **Identify key findings** related to your focus areas
4. **Provide actionable recommendations**
5. **Highlight concerns or risks**

### Focus Your Analysis On

{chr(10).join(f"- {area}" for area in perspective.focus_areas)}
""")

    # 輸出格式
    parts.append(build_json_output_format(PERSPECTIVE_REPORT_SCHEMA_DESC))

    return "\n".join(parts)


def get_research_synthesis_prompt(
    perspective_contents: Dict[str, Dict],
    context: Dict[str, Any],
) -> str:
    """
    生成研究階段的綜合報告 Prompt

    Args:
        perspective_contents: 各視角的報告內容
        context: 執行上下文

    Returns:
        完整 Prompt
    """
    from .base import SYNTHESIS_REPORT_SCHEMA_DESC

    topic = context.get("topic", "")

    parts = []

    # 系統上下文
    parts.append(build_system_context(context))

    # 任務描述
    parts.append(f"""
# Task: Synthesize Research Findings

You are synthesizing research findings from multiple perspectives for:

**{topic}**

## Perspective Reports
""")

    # 各視角報告摘要
    for pid, content in perspective_contents.items():
        name = content.get("perspective_name", pid)
        summary = content.get("summary", "")
        findings_count = len(content.get("findings", []))
        recs_count = len(content.get("recommendations", []))

        parts.append(f"""
### {name}
- Summary: {summary}
- Findings: {findings_count}
- Recommendations: {recs_count}
""")

    # 綜合指引
    parts.append("""
## Synthesis Guidelines

1. **Identify Consensus**: Find points where multiple perspectives agree
2. **Extract Key Insights**: Combine findings into actionable insights
3. **Resolve Conflicts**: When perspectives disagree, propose resolutions
4. **Prioritize Actions**: Create a prioritized action list
""")

    # 輸出格式
    parts.append(build_json_output_format(SYNTHESIS_REPORT_SCHEMA_DESC))

    return "\n".join(parts)
