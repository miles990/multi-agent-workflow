#!/usr/bin/env python3
"""
Workflow Hooks - 統一的 hook 處理入口
支援多種觸發類型：post_task, subagent_stop

使用方式：
    python3 workflow_hooks.py post_task      # Task 完成後
    python3 workflow_hooks.py subagent_stop  # Subagent 結束後

環境變數：
    CLAUDE_PROJECT_DIR - 專案目錄（由 Claude Code 自動設置）
"""
import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Tuple


def get_project_dir() -> str:
    """取得專案目錄"""
    return os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())


def auto_commit(project_dir: str, message: str) -> bool:
    """自動 commit 變更

    Args:
        project_dir: 專案目錄
        message: commit message

    Returns:
        是否成功 commit
    """
    # 檢查是否有變更
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=project_dir
    )
    if not result.stdout.strip():
        return False

    # Stage 所有變更（排除常見忽略項）
    # 使用 pathspec 排除不需要的檔案
    subprocess.run(
        ["git", "add", "-A"],
        cwd=project_dir, capture_output=True
    )

    # 移除不需要的檔案
    for pattern in ["node_modules/", "dist/", "*.log", ".env*"]:
        subprocess.run(
            ["git", "reset", "HEAD", "--", pattern],
            cwd=project_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    # Commit
    full_msg = f"{message}\n\nCo-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
    result = subprocess.run(
        ["git", "commit", "-m", full_msg],
        cwd=project_dir, capture_output=True
    )
    return result.returncode == 0


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
                capture_output=True, text=True, cwd=project_dir, timeout=300
            )
        elif pyproject.exists():
            # Python 專案 - 使用 pytest
            result = subprocess.run(
                ["pytest", "-x", "--tb=short", "-q"],
                capture_output=True, text=True, cwd=project_dir, timeout=300
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

    流程：
    1. 自動 commit 變更（保存進度）
    2. 運行測試驗證
    3. 如果測試失敗，提示修復
    """
    project_dir = input_data.get("cwd", get_project_dir())
    tool_input = input_data.get("tool_input", {})
    description = tool_input.get("description", "task completed")[:50]

    # 1. 先 commit 保存進度
    committed = auto_commit(project_dir, f"chore(task): {description}")

    if committed:
        # 2. 運行驗證
        passed, output = run_verification(project_dir)

        if not passed:
            # 輸出警告到 stderr（會顯示給用戶）
            print(f"\n⚠️ 測試失敗，請修復後再 commit：\n{output[:500]}", file=sys.stderr)
        else:
            print(f"\n✅ 自動 commit 完成，測試通過", file=sys.stderr)


def handle_subagent_stop(input_data: dict) -> None:
    """Subagent 結束處理

    檢測 .claude/memory/ 是否有變更，提示用戶執行 /memory-commit
    """
    project_dir = input_data.get("cwd", get_project_dir())

    # 檢查 memory 變更
    memory_dir = Path(project_dir) / ".claude" / "memory"
    if not memory_dir.exists():
        return

    result = subprocess.run(
        ["git", "status", "--porcelain", str(memory_dir)],
        capture_output=True, text=True, cwd=project_dir
    )
    if result.stdout.strip():
        # 統計變更數量
        changes = len(result.stdout.strip().split('\n'))
        print(f"\n📝 偵測到 {changes} 個 memory 變更，建議執行 /memory-commit", file=sys.stderr)


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
