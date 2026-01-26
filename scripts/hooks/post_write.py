#!/usr/bin/env python3
"""
Post-Write Hook - 寫入檔案後自動處理

功能：
1. 記錄 Write action 到日誌
2. 如果寫入 .claude/memory/ 目錄，自動 git commit (CP4)

由 Claude Code Hook 自動觸發
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from log_action import log_action


def main():
    if len(sys.argv) < 2:
        return

    try:
        tool_input = json.loads(sys.argv[1])
    except (json.JSONDecodeError, IndexError):
        return

    file_path = tool_input.get("file_path", "")
    if not file_path:
        return

    project_dir = os.getcwd()
    workflow_id = _get_current_workflow_id(project_dir)

    # 記錄 Write action
    log_action(
        tool="Write",
        status="success",
        input_data={"file_path": file_path},
        project_dir=project_dir,
        workflow_id=workflow_id,
    )

    # 檢查是否為 memory 目錄
    if ".claude/memory/" in file_path:
        _auto_commit_memory(project_dir, file_path, workflow_id)


def _auto_commit_memory(project_dir: str, file_path: str, workflow_id: str):
    """自動 commit memory 檔案 (CP4)"""
    # 解析 memory 路徑: .claude/memory/{type}/{id}/...
    match = re.search(r'\.claude/memory/([^/]+)/([^/]+)', file_path)
    if not match:
        return

    memory_type = match.group(1)  # research, plan, tasks, etc.
    memory_id = match.group(2)
    memory_dir = f".claude/memory/{memory_type}/{memory_id}"

    # 檢查是否有變更
    result = subprocess.run(
        ["git", "status", "--porcelain", memory_dir],
        capture_output=True,
        text=True,
        cwd=project_dir,
    )

    if not result.stdout.strip():
        return  # 沒有變更

    # 執行 git add
    subprocess.run(
        ["git", "add", memory_dir],
        cwd=project_dir,
        capture_output=True,
    )

    # 產生 commit message
    # 從檔案路徑推斷 topic
    topic = memory_id.replace("-", " ").replace("_", " ")

    # 根據 memory_type 決定 commit type
    commit_types = {
        "research": "docs",
        "plan": "feat",
        "tasks": "feat",
        "implement": "feat",
        "review": "docs",
        "verify": "test",
    }
    commit_type = commit_types.get(memory_type, "chore")

    # 取得變更的檔案列表
    diff_result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", memory_dir],
        capture_output=True,
        text=True,
        cwd=project_dir,
    )
    changed_files = diff_result.stdout.strip().split("\n")
    summary_lines = [f"- Update {Path(f).name}" for f in changed_files[:3] if f]

    commit_message = f"""{commit_type}({memory_type}): complete {topic}

{chr(10).join(summary_lines)}

Memory: {memory_dir}/
Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"""

    # 執行 git commit
    result = subprocess.run(
        ["git", "commit", "-m", commit_message],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )

    # 記錄 commit action
    if result.returncode == 0:
        log_action(
            tool="Bash",
            status="success",
            input_data={"command": "git commit (auto CP4)"},
            output_preview=result.stdout[:200],
            project_dir=project_dir,
            workflow_id=workflow_id,
        )
    else:
        log_action(
            tool="Bash",
            status="failed",
            input_data={"command": "git commit (auto CP4)"},
            error=result.stderr[:200],
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
