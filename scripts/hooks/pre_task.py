#!/usr/bin/env python3
"""
Pre-Task Hook - 在 Agent 啟動前更新狀態

由 Claude Code Hook 自動觸發
"""

import json
import os
import sys
from pathlib import Path

# 加入 scripts/hooks 到 path
sys.path.insert(0, str(Path(__file__).parent))

from update_state import update_state
from log_action import log_action


def main():
    if len(sys.argv) < 2:
        return

    try:
        tool_input = json.loads(sys.argv[1])
    except (json.JSONDecodeError, IndexError):
        return

    # 解析 Task 輸入
    description = tool_input.get("description", "")
    subagent_type = tool_input.get("subagent_type", "")
    prompt = tool_input.get("prompt", "")[:100]

    # 從 description 推斷 agent_id
    agent_id = description.lower().replace(" ", "-")[:30]

    # 取得當前 workflow_id
    project_dir = os.getcwd()
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
    """從 current.json 取得 workflow_id"""
    # 先檢查是否有活躍的 workflow
    workflow_dir = Path(project_dir) / ".claude" / "workflow"

    # 找最近的 workflow
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
