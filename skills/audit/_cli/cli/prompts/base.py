"""
Prompt 基礎模組 - 通用 Prompt 組件
"""

from typing import Any, Dict, List, Optional

from ..config.models import PerspectiveConfig, StageID
from ..config.perspectives import get_perspective


def build_system_context(context: Dict[str, Any]) -> str:
    """構建系統上下文"""
    parts = []

    parts.append("# System Context")
    parts.append("")

    if topic := context.get("topic"):
        parts.append(f"**Topic**: {topic}")

    if workflow_id := context.get("workflow_id"):
        parts.append(f"**Workflow ID**: {workflow_id}")

    if stage_id := context.get("stage_id"):
        parts.append(f"**Current Stage**: {stage_id}")

    if iteration := context.get("iteration"):
        parts.append(f"**Iteration**: {iteration}")

    parts.append("")

    return "\n".join(parts)


def build_perspective_header(perspective: PerspectiveConfig) -> str:
    """構建視角標頭"""
    parts = []

    parts.append(f"# Role: {perspective.name}")
    parts.append("")
    parts.append(f"**Description**: {perspective.description}")
    parts.append("")

    if perspective.focus_areas:
        parts.append("**Focus Areas**:")
        for area in perspective.focus_areas:
            parts.append(f"- {area}")
        parts.append("")

    return "\n".join(parts)


def build_json_output_format(schema_description: str) -> str:
    """構建 JSON 輸出格式說明"""
    return f"""
## Output Format

You MUST return your analysis as valid JSON.

{schema_description}

**Important**:
- Start your final answer with ```json
- End with ```
- Ensure the JSON is valid and parseable
- Include all required fields
"""


def build_previous_outputs(context: Dict[str, Any]) -> str:
    """構建前階段輸出摘要"""
    parts = []
    has_outputs = False

    # 研究階段輸出
    if research_outputs := context.get("research_outputs"):
        has_outputs = True
        parts.append("## Research Phase Outputs")
        parts.append(f"- Files: {', '.join(research_outputs.keys())}")
        parts.append("")

    # 規劃階段輸出
    if plan_outputs := context.get("plan_outputs"):
        has_outputs = True
        parts.append("## Plan Phase Outputs")
        parts.append(f"- Files: {', '.join(plan_outputs.keys())}")
        parts.append("")

    # 任務階段輸出
    if tasks_outputs := context.get("tasks_outputs"):
        has_outputs = True
        parts.append("## Tasks Phase Outputs")
        parts.append(f"- Files: {', '.join(tasks_outputs.keys())}")
        parts.append("")

    if not has_outputs:
        return ""

    return "\n".join(parts)


PERSPECTIVE_REPORT_SCHEMA_DESC = """
```json
{
  "perspective_id": "string - your perspective ID",
  "perspective_name": "string - your perspective name",
  "summary": "string - 1-2 sentence summary",
  "findings": [
    {
      "title": "string - finding title",
      "description": "string - detailed description",
      "importance": "high | medium | low"
    }
  ],
  "recommendations": [
    {
      "title": "string - recommendation title",
      "description": "string - detailed description",
      "priority": "must | should | could"
    }
  ],
  "concerns": [
    {
      "title": "string - concern title",
      "description": "string - detailed description",
      "severity": "critical | high | medium | low"
    }
  ]
}
```
"""


SYNTHESIS_REPORT_SCHEMA_DESC = """
```json
{
  "stage_id": "string - stage ID",
  "consensus": {
    "score": "number - consensus score 0-1",
    "points": ["string - consensus point"]
  },
  "key_insights": [
    {
      "insight": "string - key insight",
      "source_perspectives": ["string - perspective IDs"],
      "confidence": "high | medium | low"
    }
  ],
  "conflicts": [
    {
      "topic": "string - conflict topic",
      "perspectives": [
        {
          "perspective_id": "string",
          "position": "string - perspective's position"
        }
      ],
      "resolution": "string - resolution if any"
    }
  ],
  "action_items": [
    {
      "action": "string - action item",
      "priority": "critical | high | medium | low",
      "owner": "string - optional owner"
    }
  ]
}
```
"""
