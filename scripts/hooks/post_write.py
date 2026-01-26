#!/usr/bin/env python3
"""
Post-Write Hook - 寫入檔案後記錄 action

由 Claude Code Hook 自動觸發
注意：git commit 由 SubagentStop hook 處理
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from log_action import log_action


def main():
    # 從 stdin 讀取 JSON 輸入
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        return

    project_dir = input_data.get("cwd", os.getcwd())
    workflow_id = _get_current_workflow_id(project_dir)

    # 記錄 Write action
    log_action(
        tool="Write",
        status="success",
        input_data={"file_path": file_path},
        project_dir=project_dir,
        workflow_id=workflow_id,
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
