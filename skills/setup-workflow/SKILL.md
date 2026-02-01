---
name: setup-workflow
version: 1.0.0
description: 一鍵配置 multi-agent-workflow 規範執行機制
triggers: [setup-workflow, setup-wf]
allowed-tools: [Bash, Read, Write, Edit, Glob]
---

# Setup Workflow

為當前專案配置 multi-agent-workflow 的規範執行機制。

## 使用方式

```bash
/setup-workflow              # 完整設置
/setup-workflow --check      # 僅檢查配置狀態
/setup-workflow --minimal    # 最小設置（僅權限）
```

## 配置內容

### 1. Hook 腳本
自動 commit、驗證檢查的 Python 腳本。

### 2. 權限預設
常用命令預先允許（git, pnpm, npm, pytest 等）。

### 3. Memory 結構
研究/計劃/實作記錄目錄（可選）。

## 執行步驟

### Step 1: 檢查現有配置

```bash
# 檢查 settings.local.json 是否存在
cat .claude/settings.local.json 2>/dev/null || echo "{}"
```

檢查項目：
- [ ] `hooks.PostToolUse` 是否包含 Task matcher
- [ ] `hooks.SubagentStop` 是否存在
- [ ] `permissions.allow` 是否包含常用命令

### Step 2: 創建 Hook 腳本

創建 `scripts/hooks/workflow_hooks.py`：

```python
#!/usr/bin/env python3
"""
Workflow Hooks - 統一的 hook 處理入口
支援多種觸發類型：post_task, subagent_stop, pre_commit
"""
import json
import subprocess
import sys
import os
from pathlib import Path

def get_project_dir():
    return os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

def auto_commit(project_dir: str, message: str):
    """自動 commit 變更"""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=project_dir
    )
    if not result.stdout.strip():
        return False

    subprocess.run(
        ["git", "add", "-A", ":!node_modules/", ":!dist/", ":!*.log", ":!.env*"],
        cwd=project_dir, capture_output=True
    )

    full_msg = f"{message}\n\nCo-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
    result = subprocess.run(
        ["git", "commit", "-m", full_msg],
        cwd=project_dir, capture_output=True
    )
    return result.returncode == 0

def run_verification(project_dir: str) -> tuple[bool, str]:
    """運行驗證（測試）"""
    package_json = Path(project_dir) / "package.json"
    pyproject = Path(project_dir) / "pyproject.toml"

    if package_json.exists():
        result = subprocess.run(
            ["pnpm", "test", "--passWithNoTests"],
            capture_output=True, text=True, cwd=project_dir, timeout=300
        )
    elif pyproject.exists():
        result = subprocess.run(
            ["pytest", "-x", "--tb=short"],
            capture_output=True, text=True, cwd=project_dir, timeout=300
        )
    else:
        return True, "No test framework detected"

    if result.returncode == 0:
        return True, "All tests passed"
    else:
        return False, result.stdout + result.stderr

def handle_post_task(input_data: dict):
    """Task 完成後處理"""
    project_dir = input_data.get("cwd", get_project_dir())
    tool_input = input_data.get("tool_input", {})
    description = tool_input.get("description", "task completed")[:50]

    committed = auto_commit(project_dir, f"chore(task): {description}")

    if committed:
        passed, output = run_verification(project_dir)
        if not passed:
            print(f"\n⚠️ 測試失敗，請修復後再 commit：\n{output[:500]}", file=sys.stderr)

def handle_subagent_stop(input_data: dict):
    """Subagent 結束處理"""
    project_dir = input_data.get("cwd", get_project_dir())
    memory_dir = Path(project_dir) / ".claude" / "memory"

    if not memory_dir.exists():
        return

    result = subprocess.run(
        ["git", "status", "--porcelain", str(memory_dir)],
        capture_output=True, text=True, cwd=project_dir
    )
    if result.stdout.strip():
        print(f"\n📝 偵測到 memory 變更，建議執行 /memory-commit", file=sys.stderr)

def main():
    if len(sys.argv) < 2:
        print("Usage: workflow_hooks.py <hook_type>", file=sys.stderr)
        return

    hook_type = sys.argv[1]

    try:
        input_data = json.load(sys.stdin)
    except:
        input_data = {}

    handlers = {
        "post_task": handle_post_task,
        "subagent_stop": handle_subagent_stop,
    }

    handler = handlers.get(hook_type)
    if handler:
        handler(input_data)

if __name__ == "__main__":
    main()
```

### Step 3: 更新 settings.local.json

合併以下配置到現有 settings：

```json
{
  "permissions": {
    "allow": [
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git push:*)",
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(pnpm:*)",
      "Bash(npm:*)",
      "Bash(npx:*)",
      "Bash(python3:*)",
      "Bash(pytest:*)",
      "Bash(vitest:*)"
    ]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/scripts/hooks/workflow_hooks.py\" post_task"
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/scripts/hooks/workflow_hooks.py\" subagent_stop"
          }
        ]
      }
    ]
  }
}
```

### Step 4: 創建 Memory 結構（可選）

```bash
mkdir -p .claude/memory/{tasks,research,plans,implement,review,workflows}
```

### Step 5: 顯示配置摘要

```
✅ Workflow 設置完成！

配置項目：
  ✓ Hook 腳本：scripts/hooks/workflow_hooks.py
  ✓ 權限：12 個常用命令已允許
  ✓ Hooks：PostToolUse(Task), SubagentStop

功能說明：
  • Task 完成後自動 commit 並運行測試
  • Subagent 結束時檢測 memory 變更
  • 測試失敗會提示修復

相關命令：
  • /memory-commit - 手動 commit memory 變更
  • /orchestrate - 端到端工作流（會自動使用這些 hooks）
```

## 注意事項

- 會保留現有的 settings.local.json 配置
- Hook 腳本需要 Python 3.8+
- 如果專案沒有測試框架，驗證步驟會跳過
- 可以用 `--minimal` 只設置權限，不啟用 hooks
