#!/usr/bin/env python3
"""
Post-Task Hook - 在 Agent 完成後更新狀態和記錄

由 Claude Code Hook 自動觸發
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from update_state import update_state
from log_action import log_action


def main():
    if len(sys.argv) < 2:
        return

    try:
        tool_input = json.loads(sys.argv[1])
    except (json.JSONDecodeError, IndexError):
        tool_input = {}

    tool_output = sys.argv[2] if len(sys.argv) > 2 else ""

    # 解析
    description = tool_input.get("description", "")
    agent_id = description.lower().replace(" ", "-")[:30]

    # 判斷成功或失敗
    success = "error" not in tool_output.lower() and "failed" not in tool_output.lower()
    status = "completed" if success else "failed"

    project_dir = os.getcwd()
    workflow_id = _get_current_workflow_id(project_dir)

    if not workflow_id:
        return

    # 更新狀態
    update_state(
        project_dir=project_dir,
        workflow_id=workflow_id,
        agent_id=agent_id,
        agent_status=status,
    )

    # 記錄 action
    log_action(
        tool="Task",
        status="success" if success else "failed",
        input_data={"description": description},
        output_preview=tool_output[:200] if tool_output else None,
        project_dir=project_dir,
        workflow_id=workflow_id,
        agent_id=agent_id,
    )


def _get_current_workflow_id(project_dir: str) -> str:
    """從最近的 workflow 目錄取得 ID"""
    workflow_dir = Path(project_dir) / ".claude" / "workflow"
    if workflow_dir.exists():
        for d in sorted(workflow_dir.iterdir(), reverse=True):
            if d.is_dir() and (d / "current.json").exists():
                try:
                    with open(d / "current.json") as f:
                        state = json.load(f)
                        return state.get("workflow_id", d.name)
                except:
                    pass
    return ""


if __name__ == "__main__":
    main()
