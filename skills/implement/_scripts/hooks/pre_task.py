#!/usr/bin/env python3
"""
Pre-Task Hook - 在 Agent 啟動前更新狀態

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
    # 從 stdin 讀取 JSON 輸入
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    tool_input = input_data.get("tool_input", {})
    description = tool_input.get("description", "")
    subagent_type = tool_input.get("subagent_type", "")
    prompt = tool_input.get("prompt", "")[:100]

    # 從 description 推斷 agent_id
    agent_id = description.lower().replace(" ", "-")[:30]

    project_dir = input_data.get("cwd", os.getcwd())
    workflow_id = _get_current_workflow_id(project_dir)

    if not workflow_id:
        return

    # 更新狀態：Agent 開始
    update_state(
        project_dir=project_dir,
        workflow_id=workflow_id,
        agent_id=agent_id,
        agent_name=description,
        agent_status="running",
        agent_task=prompt,
    )

    # 記錄 action
    log_action(
        tool="Task",
        status="started",
        input_data={
            "description": description,
            "subagent_type": subagent_type,
        },
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
