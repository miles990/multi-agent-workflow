#!/usr/bin/env python3
"""SubagentStop Hook - 在子代理完成時執行 git commit

觸發時機：當 Task 工具完成時
功能：
1. 更新 agent 狀態為 completed
2. 檢查 .claude/memory/ 是否有變更
3. 如果有變更，執行 git commit

重構版本：使用 git_lib 統一模組
"""

import json
import os
import re
import sys
from pathlib import Path

# 加入 git_lib 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from git_lib import GitOps, WorkflowCommitFacade
from log_action import log_action


def main():
    # 讀取 stdin 的 JSON 輸入
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    session_id = input_data.get("session_id", "")
    stop_hook_active = input_data.get("stop_hook_active", False)

    # 防止無限循環
    if stop_hook_active:
        return

    project_dir = Path(input_data.get("cwd", os.getcwd()))

    # 使用統一 Facade
    facade = WorkflowCommitFacade(project_dir)
    workflow_id = facade.get_workflow_id() or ""

    # 記錄 subagent 完成
    log_action(
        tool="SubagentStop",
        status="success",
        input_data={"session_id": session_id},
        project_dir=str(project_dir),
        workflow_id=workflow_id,
    )

    # 檢查 .claude/memory/ 是否有變更
    memory_dir = project_dir / ".claude" / "memory"
    if not memory_dir.exists():
        return

    # 使用 GitOps 取得變更
    git = GitOps(project_dir)
    status_output = git.get_status([str(memory_dir)])

    if not status_output:
        return

    # 解析變更的 memory 路徑
    memory_paths = set()
    for line in status_output.split("\n"):
        if not line:
            continue
        # 格式: " M path/to/file" 或 "?? path/to/file"
        parts = line.split()
        if len(parts) >= 2:
            file_path = parts[-1]
            match = re.search(r"\.claude/memory/([^/]+)/([^/]+)", file_path)
            if match:
                memory_paths.add((match.group(1), match.group(2)))

    if not memory_paths:
        return

    # 對每個 memory 路徑執行 commit
    for memory_type, memory_id in memory_paths:
        result = facade.auto_commit_memory(memory_type, memory_id)

        if result and result.success:
            # 記錄成功
            log_action(
                tool="Bash",
                status="success",
                input_data={"command": f"git commit ({memory_type}/{memory_id})"},
                output_preview=f"Committed: {result.commit_hash[:8] if result.commit_hash else 'unknown'}",
                project_dir=str(project_dir),
                workflow_id=workflow_id,
            )
            print(
                f"Committed: .claude/memory/{memory_type}/{memory_id}",
                file=sys.stderr,
            )
        elif result and not result.success:
            # 記錄失敗
            log_action(
                tool="Bash",
                status="failed",
                input_data={"command": f"git commit ({memory_type}/{memory_id})"},
                error=result.error[:200] if result.error else "Unknown error",
                project_dir=str(project_dir),
                workflow_id=workflow_id,
            )


if __name__ == "__main__":
    main()
