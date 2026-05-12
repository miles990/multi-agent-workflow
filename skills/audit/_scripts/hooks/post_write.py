#!/usr/bin/env python3
"""
Post-Write Hook - 寫入檔案後記錄 action

由 Claude Code Hook 自動觸發
注意：
- 一般檔案的 git commit 由 SubagentStop hook 處理
- 檢查點檔案（如 synthesis.md）會觸發自動 commit
"""

import json
import os
import sys
from fnmatch import fnmatch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # git_lib 目錄
sys.path.insert(0, str(Path(__file__).parent))

from log_action import log_action

# 檢查點檔案模式（寫入這些檔案時觸發 commit）
CHECKPOINT_PATTERNS = [
    "**/synthesis.md",           # RESEARCH 完成
    "**/implementation-plan.md", # PLAN 完成
    "**/tasks.yaml",             # TASKS 完成
    "**/summary.md",             # IMPLEMENT 完成
    "**/review-summary.md",      # REVIEW 完成
    "**/verify-summary.md",      # VERIFY 完成
]


def _is_checkpoint_file(file_path: str) -> bool:
    """檢查是否為檢查點檔案

    Args:
        file_path: 檔案路徑

    Returns:
        True 如果是檢查點檔案
    """
    return any(fnmatch(file_path, pattern) for pattern in CHECKPOINT_PATTERNS)


def _commit_checkpoint(project_dir: str, file_path: str) -> None:
    """檢查點檔案自動 commit

    Args:
        project_dir: 專案目錄
        file_path: 檢查點檔案路徑
    """
    try:
        from git_lib import WorkflowCommitFacade

        facade = WorkflowCommitFacade(Path(project_dir))
        result = facade.auto_commit_checkpoint(file_path)
        if result and result.success:
            print(f"[checkpoint] committed: {result.commit_hash[:8]}")
    except Exception as e:
        # 不中斷主流程，只記錄錯誤
        print(f"[checkpoint] commit failed: {e}", file=sys.stderr)


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

    # 檢查是否為檢查點檔案，如果是則觸發 commit
    if _is_checkpoint_file(file_path):
        _commit_checkpoint(project_dir, file_path)


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
