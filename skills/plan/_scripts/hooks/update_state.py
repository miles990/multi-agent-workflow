#!/usr/bin/env python3
"""
State Tracker - 更新 current.json 即時狀態

用法:
  python update-state.py --workflow-id research_user-auth --stage RESEARCH
  python update-state.py --agent-id architecture --agent-status running
  python update-state.py --agent-id architecture --agent-status completed
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path


def update_state(
    project_dir: str = None,
    workflow_id: str = None,
    topic: str = None,
    stage: str = None,
    stage_name: str = None,
    stage_index: int = None,
    stage_total: int = None,
    agent_id: str = None,
    agent_name: str = None,
    agent_status: str = None,
    agent_task: str = None,
):
    """更新 current.json 狀態"""
    project_dir = project_dir or os.getcwd()

    # 決定狀態檔路徑
    if workflow_id:
        state_dir = Path(project_dir) / ".claude" / "workflow" / workflow_id
    else:
        state_dir = Path(project_dir) / ".claude" / "workflow"

    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "current.json"

    # 讀取現有狀態
    state = {}
    if state_file.exists():
        try:
            with open(state_file) as f:
                state = json.load(f)
        except:
            pass

    # 更新時間戳
    state["updated_at"] = datetime.utcnow().isoformat() + "Z"

    # 更新工作流資訊
    if workflow_id or topic:
        if "workflow" not in state:
            state["workflow"] = {}
        if workflow_id:
            state["workflow"]["id"] = workflow_id
            state["workflow_id"] = workflow_id  # 相容舊格式
        if topic:
            state["workflow"]["topic"] = topic

    # 更新階段資訊
    if stage:
        state["stage"] = stage
        if "stage_info" not in state:
            state["stage_info"] = {}
        state["stage_info"]["id"] = stage
        if stage_name:
            state["stage_info"]["name"] = stage_name
        if stage_index:
            state["stage_info"]["index"] = stage_index
        if stage_total:
            state["stage_info"]["total"] = stage_total

    # 更新 Agent 狀態
    if agent_id:
        if "agents" not in state:
            state["agents"] = []

        # 找到或新增 agent
        agent = next((a for a in state["agents"] if a.get("id") == agent_id), None)
        if not agent:
            agent = {"id": agent_id}
            state["agents"].append(agent)

        if agent_name:
            agent["name"] = agent_name
        if agent_status:
            agent["status"] = agent_status
        if agent_task:
            agent["task"] = agent_task

        # 更新進度
        total = len(state["agents"])
        completed = sum(1 for a in state["agents"] if a.get("status") in ["completed", "failed"])
        state["progress"] = {
            "agents_total": total,
            "agents_completed": completed,
        }

    # 寫入
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    return state


def main():
    parser = argparse.ArgumentParser(description="Update current.json state")
    parser.add_argument("--project-dir", help="Project directory")
    parser.add_argument("--workflow-id", help="Workflow ID")
    parser.add_argument("--topic", help="Workflow topic")
    parser.add_argument("--stage", help="Current stage")
    parser.add_argument("--stage-name", help="Stage display name")
    parser.add_argument("--stage-index", type=int, help="Stage index")
    parser.add_argument("--stage-total", type=int, help="Total stages")
    parser.add_argument("--agent-id", help="Agent ID")
    parser.add_argument("--agent-name", help="Agent name")
    parser.add_argument("--agent-status", choices=["pending", "running", "completed", "failed"])
    parser.add_argument("--agent-task", help="Agent task description")

    args = parser.parse_args()

    state = update_state(
        project_dir=args.project_dir,
        workflow_id=args.workflow_id,
        topic=args.topic,
        stage=args.stage,
        stage_name=args.stage_name,
        stage_index=args.stage_index,
        stage_total=args.stage_total,
        agent_id=args.agent_id,
        agent_name=args.agent_name,
        agent_status=args.agent_status,
        agent_task=args.agent_task,
    )

    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
