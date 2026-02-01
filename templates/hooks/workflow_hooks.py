#!/usr/bin/env python3
"""Workflow Hooks - 統一的 hook 處理入口

使用委派模式，將請求轉發到 scripts/hooks/ 的完整實作。
這確保了 templates/ 和 scripts/hooks/ 使用相同的邏輯。

使用方式：
    python3 workflow_hooks.py post_task      # Task 完成後
    python3 workflow_hooks.py subagent_stop  # Subagent 結束後

環境變數：
    CLAUDE_PROJECT_DIR - 專案目錄（由 Claude Code 自動設置）

重構版本：使用 git_lib 統一模組
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Tuple

# 加入 git_lib 路徑
PLUGIN_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from git_lib import GitOps, WorkflowCommitFacade


def get_project_dir() -> str:
    """取得專案目錄"""
    return os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())


def auto_commit(project_dir: str, message: str) -> bool:
    """自動 commit 變更

    使用 git_lib 統一模組實作。

    Args:
        project_dir: 專案目錄
        message: commit message

    Returns:
        是否成功 commit
    """
    git = GitOps(Path(project_dir))

    # 檢查是否有變更
    if not git.has_changes():
        return False

    # Stage 變更（排除常見忽略項）
    pathspecs = [
        ".",
        ":!node_modules/",
        ":!dist/",
        ":!*.log",
        ":!.env*",
    ]

    try:
        git.stage(pathspecs)
    except Exception:
        # 如果 pathspec 格式有問題，使用簡單的 git add -A
        git.executor.run(["add", "-A"])

    # Commit
    from git_lib import ConfigManager

    config = ConfigManager(Path(project_dir))
    full_msg = f"{message}\n\n{config.get_co_author()}"
    result = git.commit(full_msg)

    return result.success


def run_verification(project_dir: str) -> Tuple[bool, str]:
    """運行驗證（測試）

    Args:
        project_dir: 專案目錄

    Returns:
        (是否通過, 輸出訊息)
    """
    package_json = Path(project_dir) / "package.json"
    pyproject = Path(project_dir) / "pyproject.toml"

    try:
        if package_json.exists():
            # Node.js 專案 - 使用 pnpm test
            result = subprocess.run(
                ["pnpm", "test", "--passWithNoTests"],
                capture_output=True,
                text=True,
                cwd=project_dir,
                timeout=300,
            )
        elif pyproject.exists():
            # Python 專案 - 使用 pytest
            result = subprocess.run(
                ["pytest", "-x", "--tb=short", "-q"],
                capture_output=True,
                text=True,
                cwd=project_dir,
                timeout=300,
            )
        else:
            return True, "No test framework detected"

        if result.returncode == 0:
            return True, "All tests passed"
        else:
            return False, result.stdout + result.stderr

    except subprocess.TimeoutExpired:
        return False, "Test timeout (>5min)"
    except FileNotFoundError as e:
        return True, f"Test runner not found: {e}"


def handle_post_task(input_data: dict) -> None:
    """Task 完成後處理

    使用 WorkflowCommitFacade 統一處理。

    流程：
    1. 自動 commit 變更（保存進度）
    2. 運行測試驗證
    3. 如果測試失敗，提示修復
    """
    project_dir = Path(input_data.get("cwd", get_project_dir()))
    tool_input = input_data.get("tool_input", {})
    description = tool_input.get("description", "task completed")

    # 判斷成功或失敗
    tool_response = input_data.get("tool_response", {})
    tool_output = str(tool_response)
    success = "error" not in tool_output.lower() and "failed" not in tool_output.lower()

    # 使用統一 Facade
    facade = WorkflowCommitFacade(project_dir)
    result = facade.auto_commit_after_task(description, success)

    if result and result.success:
        # 運行驗證
        passed, output = run_verification(str(project_dir))

        if not passed:
            print(
                f"\n⚠️ 測試失敗，請修復後再 commit：\n{output[:500]}", file=sys.stderr
            )
        else:
            print(
                f"\n✅ 自動 commit 完成: {result.commit_hash[:8] if result.commit_hash else 'done'}",
                file=sys.stderr,
            )


def handle_subagent_stop(input_data: dict) -> None:
    """Subagent 結束處理

    使用 git_lib 檢測 .claude/memory/ 是否有變更。
    """
    project_dir = Path(input_data.get("cwd", get_project_dir()))

    # 檢查 memory 變更
    memory_dir = project_dir / ".claude" / "memory"
    if not memory_dir.exists():
        return

    git = GitOps(project_dir)
    status = git.get_status([str(memory_dir)])

    if status:
        # 統計變更數量
        changes = len([line for line in status.split("\n") if line.strip()])
        print(
            f"\n📝 偵測到 {changes} 個 memory 變更，建議執行 /memory-commit",
            file=sys.stderr,
        )


def main():
    if len(sys.argv) < 2:
        print("Usage: workflow_hooks.py <hook_type>", file=sys.stderr)
        print("  hook_type: post_task | subagent_stop", file=sys.stderr)
        sys.exit(1)

    hook_type = sys.argv[1]

    # 從 stdin 讀取輸入（Claude Code 會傳入 JSON）
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        input_data = {}

    handlers = {
        "post_task": handle_post_task,
        "subagent_stop": handle_subagent_stop,
    }

    handler = handlers.get(hook_type)
    if handler:
        handler(input_data)
    else:
        print(f"Unknown hook type: {hook_type}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
