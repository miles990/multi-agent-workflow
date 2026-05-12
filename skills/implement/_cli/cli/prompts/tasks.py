"""
TASKS 階段 Prompt 模板
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


TASKS_OUTPUT_SCHEMA = """
```json
{
  "perspective_id": "string",
  "perspective_name": "string",
  "summary": "string",
  "findings": [...],
  "recommendations": [...],
  "task_suggestions": [
    {
      "id": "string - e.g., T-F-01, TEST-01",
      "title": "string",
      "description": "string",
      "type": "feature | test | setup | config | docs",
      "wave": "number - execution wave",
      "depends_on": ["string - task IDs"],
      "acceptance_criteria": ["string"],
      "test_id": "string - corresponding test ID for TDD"
    }
  ]
}
```
"""


def get_tasks_perspective_prompt(
    perspective: PerspectiveConfig,
    context: Dict[str, Any],
) -> str:
    """生成任務分解階段的視角 Prompt"""
    topic = context.get("topic", "")

    parts = []

    parts.append(build_system_context(context))
    parts.append(build_perspective_header(perspective))
    parts.append(build_previous_outputs(context))

    parts.append(f"""
## Task

Decompose the implementation plan into executable tasks for:

**{topic}**

As a **{perspective.name}**, analyze and decompose tasks from your perspective.

### Task Decomposition Guidelines

1. **Atomic Tasks**: Each task should be small and independently testable
2. **Clear Acceptance Criteria**: Define what "done" means
3. **TDD Mapping**: Feature tasks (T-F-*) should have corresponding tests (TEST-*)
4. **Wave Planning**: Group tasks by execution order
5. **Dependencies**: Identify task dependencies to form a valid DAG

### Task ID Conventions

- `T-F-XX`: Feature implementation tasks
- `TEST-XX`: Test tasks
- `SETUP-XX`: Setup/configuration tasks
- `T-D-XX`: Documentation tasks

### Focus On

{chr(10).join(f"- {area}" for area in perspective.focus_areas)}
""")

    parts.append(build_json_output_format(TASKS_OUTPUT_SCHEMA))

    return "\n".join(parts)


def get_tasks_synthesis_prompt(
    perspective_contents: Dict[str, Dict],
    context: Dict[str, Any],
) -> str:
    """生成任務分解階段的綜合報告 Prompt"""
    topic = context.get("topic", "")

    parts = []
    parts.append(build_system_context(context))

    parts.append(f"""
# Task: Create Task DAG

Synthesize task suggestions into a valid task DAG for:

**{topic}**

## Perspective Suggestions
""")

    for pid, content in perspective_contents.items():
        name = content.get("perspective_name", pid)
        tasks = content.get("task_suggestions", [])
        parts.append(f"- **{name}**: {len(tasks)} tasks suggested")

    parts.append("""
## DAG Requirements

1. **No Cycles**: The task graph must be acyclic
2. **TDD Compliance**: Each T-F-* must have a corresponding TEST-*
3. **Wave Assignment**: Group independent tasks into parallel waves
4. **Complete Coverage**: All features from the plan must be covered
5. **Clear Dependencies**: Every dependency must point to an existing task

## Output Format

Return a unified task list in YAML format:

```yaml
metadata:
  total_tasks: number
  total_waves: number

tasks:
  - id: "T-F-01"
    title: "Task title"
    type: "feature"
    wave: 1
    depends_on: []
    acceptance_criteria:
      - "Criterion 1"
    test_id: "TEST-01"
```
""")

    return "\n".join(parts)
