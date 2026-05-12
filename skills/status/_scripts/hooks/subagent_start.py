#!/usr/bin/env python3
"""
SubagentStart Hook - 在子代理開始時記錄

觸發時機：當 Task 工具開始執行子代理時
功能：
1. 初始化 agent 狀態
2. 記錄 agent_start action
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from log_action import log_action
from update_state import update_state


def main():
    # 從 stdin 讀取 JSON 輸入
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    # SubagentStart 輸入格式（根據文檔）
    # 包含 session_id, cwd, permission_mode 等
    session_id = input_data.get("session_id", "")

    project_dir = input_data.get("cwd", os.getcwd())
    workflow_id = _get_current_workflow_id(project_dir)

    if not workflow_id:
        return

    # 從 session_id 推斷 agent_id
    agent_id = f"subagent_{session_id[:8]}" if session_id else "unknown"

    # 記錄 subagent 開始
    log_action(
        tool="SubagentStart",
        status="success",
        input_data={
            "session_id": session_id,
            "event": "subagent_start",
        },
        project_dir=project_dir,
        workflow_id=workflow_id,
        agent_id=agent_id,
    )

    # 更新狀態
    update_state(
        project_dir=project_dir,
        workflow_id=workflow_id,
        agent_id=agent_id,
        agent_name=f"Subagent {session_id[:8]}",
        agent_status="running",
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
