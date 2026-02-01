#!/usr/bin/env python3
"""Post-Task Hook - 在 Agent 完成後更新狀態並自動 commit

由 Claude Code Hook 自動觸發
- 更新 workflow 狀態
- 自動 git commit 程式碼變更（可設定是否包含 memory/logs）

重構版本：使用 git_lib 統一模組
"""

import json
import os
import sys
from pathlib import Path

# 加入 git_lib 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from git_lib import WorkflowCommitFacade
from log_action import log_action
from update_state import update_state


def main():
    # 從 stdin 讀取 JSON 輸入
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    tool_input = input_data.get("tool_input", {})
    tool_response = input_data.get("tool_response", {})

    description = tool_input.get("description", "")
    agent_id = description.lower().replace(" ", "-")[:30]

    # 判斷成功或失敗
    tool_output = str(tool_response)
    success = "error" not in tool_output.lower() and "failed" not in tool_output.lower()
    status = "completed" if success else "failed"

    project_dir = Path(input_data.get("cwd", os.getcwd()))

    # 使用統一 Facade
    facade = WorkflowCommitFacade(project_dir)
    workflow_id = facade.get_workflow_id()

    if not workflow_id:
        return

    # 更新狀態
    update_state(
        project_dir=str(project_dir),
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
        project_dir=str(project_dir),
        workflow_id=workflow_id,
        agent_id=agent_id,
    )

    # 自動 commit（使用 Facade 簡化 API）
    result = facade.auto_commit_after_task(description, success)

    if result and result.success:
        print(f"✅ Auto-committed: {result.commit_hash[:8]}", file=sys.stderr)


if __name__ == "__main__":
    main()
