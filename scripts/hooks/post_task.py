#!/usr/bin/env python3
"""
Post-Task Hook - 在 Agent 完成後更新狀態並自動 commit

由 Claude Code Hook 自動觸發
- 更新 workflow 狀態
- 自動 git commit 程式碼變更（可設定是否包含 memory/logs）
"""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from update_state import update_state
from log_action import log_action

try:
    import yaml
except ImportError:
    yaml = None


def _load_commit_settings(project_dir: str) -> dict:
    """載入 commit 設定"""
    default = {
        "enabled": True,
        "include_memory": False,
        "include_logs": False,
        "exclude_patterns": ["*.pyc", "__pycache__/", ".DS_Store"],
    }

    if yaml is None:
        return default

    config_path = Path(project_dir) / "shared/config/commit-settings.yaml"
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
                return config.get("task_commit", default)
        except Exception:
            pass

    return default


def _commit_task_changes(project_dir: str, description: str, success: bool):
    """Task 完成後 commit 程式碼變更"""
    settings = _load_commit_settings(project_dir)

    if not settings.get("enabled", True):
        return

    if not success:
        return

    # 建立排除路徑規格
    pathspecs = ["."]  # 從當前目錄開始

    # 根據設定排除 memory 和 logs
    if not settings.get("include_memory", False):
        pathspecs.append(":!.claude/memory/")

    if not settings.get("include_logs", False):
        pathspecs.append(":!.claude/workflow/")
        pathspecs.append(":!.claude/logs/")

    # 加入自訂排除模式
    for pattern in settings.get("exclude_patterns", []):
        pathspecs.append(f":!{pattern}")

    # 檢查是否有變更
    cmd = ["git", "status", "--porcelain", "--"] + pathspecs
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_dir)

    if not result.stdout.strip():
        return  # 無變更

    # Stage 變更
    cmd = ["git", "add", "--"] + pathspecs
    subprocess.run(cmd, cwd=project_dir, capture_output=True)

    # 建立 commit message
    task_summary = description[:50] if description else "task completed"

    commit_message = f"""chore(task): {task_summary}

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"""

    # Commit
    subprocess.run(
        ["git", "commit", "-m", commit_message],
        cwd=project_dir,
        capture_output=True,
    )


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

    project_dir = input_data.get("cwd", os.getcwd())
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

    # 自動 commit 程式碼變更
    _commit_task_changes(project_dir, description, success)


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
