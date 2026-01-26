#!/usr/bin/env python3
"""
SubagentStop Hook - 在子代理完成時執行 git commit

觸發時機：當 Task 工具完成時
功能：
1. 更新 agent 狀態為 completed
2. 檢查 .claude/memory/ 是否有變更
3. 如果有變更，執行 git commit
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
from update_state import update_state


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

    project_dir = input_data.get("cwd", os.getcwd())
    workflow_id = _get_current_workflow_id(project_dir)

    # 記錄 subagent 完成
    log_action(
        tool="SubagentStop",
        status="success",
        input_data={"session_id": session_id},
        project_dir=project_dir,
        workflow_id=workflow_id,
    )

    # 檢查 .claude/memory/ 是否有變更
    memory_dir = Path(project_dir) / ".claude" / "memory"
    if not memory_dir.exists():
        return

    # 檢查 git status
    result = subprocess.run(
        ["git", "status", "--porcelain", str(memory_dir)],
        capture_output=True,
        text=True,
        cwd=project_dir,
    )

    if not result.stdout.strip():
        return  # 沒有變更

    # 找出變更的 memory 目錄
    changed_files = result.stdout.strip().split("\n")
    memory_paths = set()

    for line in changed_files:
        # 格式: " M path/to/file" 或 "?? path/to/file"
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            file_path = parts[-1]
            # 解析 .claude/memory/{type}/{id}/
            match = re.search(r'\.claude/memory/([^/]+)/([^/]+)', file_path)
            if match:
                memory_type = match.group(1)
                memory_id = match.group(2)
                memory_paths.add((memory_type, memory_id))

    if not memory_paths:
        return

    # 對每個 memory 路徑執行 commit
    for memory_type, memory_id in memory_paths:
        _commit_memory(project_dir, memory_type, memory_id, workflow_id)


def _commit_memory(project_dir: str, memory_type: str, memory_id: str, workflow_id: str):
    """Commit 特定 memory 目錄"""
    memory_dir = f".claude/memory/{memory_type}/{memory_id}"

    # 檢查是否有變更
    result = subprocess.run(
        ["git", "status", "--porcelain", memory_dir],
        capture_output=True,
        text=True,
        cwd=project_dir,
    )

    if not result.stdout.strip():
        return

    # git add
    subprocess.run(
        ["git", "add", memory_dir],
        cwd=project_dir,
        capture_output=True,
    )

    # 決定 commit type
    commit_types = {
        "research": "docs",
        "plans": "feat",
        "tasks": "feat",
        "implement": "feat",
        "review": "docs",
        "verify": "test",
    }
    commit_type = commit_types.get(memory_type, "chore")

    # 取得變更檔案列表
    diff_result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", memory_dir],
        capture_output=True,
        text=True,
        cwd=project_dir,
    )
    changed_files = [f for f in diff_result.stdout.strip().split("\n") if f]

    if not changed_files:
        return

    # 產生摘要
    summary_lines = [f"- Update {Path(f).name}" for f in changed_files[:3]]
    topic = memory_id.replace("-", " ").replace("_", " ")

    commit_message = f"""{commit_type}({memory_type}): complete {topic}

{chr(10).join(summary_lines)}

Memory: {memory_dir}/
Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"""

    # git commit
    result = subprocess.run(
        ["git", "commit", "-m", commit_message],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )

    # 記錄
    if result.returncode == 0:
        log_action(
            tool="Bash",
            status="success",
            input_data={"command": f"git commit ({memory_type}/{memory_id})"},
            output_preview=result.stdout[:200],
            project_dir=project_dir,
            workflow_id=workflow_id,
        )
        print(f"Committed: {memory_dir}", file=sys.stderr)
    else:
        log_action(
            tool="Bash",
            status="failed",
            input_data={"command": f"git commit ({memory_type}/{memory_id})"},
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
