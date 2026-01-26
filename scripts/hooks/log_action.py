#!/usr/bin/env python3
"""
Action Logger - 記錄工具調用到 actions.jsonl

用法:
  python log-action.py --tool Read --status success --input '{"file_path": "/path"}' --output-size 1024
  python log-action.py --tool Bash --status failed --error "Command failed" --exit-code 1
"""

import argparse
import json
import os
import random
import string
from datetime import datetime
from pathlib import Path


def generate_id() -> str:
    """生成唯一 ID"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rand = ''.join(random.choices(string.hexdigits[:16], k=6))
    return f"act_{ts}_{rand}"


def get_workflow_state(project_dir: str) -> dict:
    """讀取當前工作流狀態"""
    current_file = Path(project_dir) / ".claude" / "workflow" / "current.json"
    if current_file.exists():
        try:
            with open(current_file) as f:
                return json.load(f)
        except:
            pass
    return {}


def log_action(
    tool: str,
    status: str,
    input_data: dict = None,
    output_preview: str = None,
    output_size: int = None,
    error: str = None,
    stderr: str = None,
    exit_code: int = None,
    duration_ms: int = None,
    project_dir: str = None,
    workflow_id: str = None,
    agent_id: str = None,
    stage: str = None,
):
    """記錄一個 action"""
    project_dir = project_dir or os.getcwd()

    # 取得工作流狀態
    state = get_workflow_state(project_dir)
    workflow_id = workflow_id or state.get("workflow_id", "")
    agent_id = agent_id or state.get("agent_id", "")
    stage = stage or state.get("stage", "")

    # 決定 log 路徑
    if workflow_id:
        log_dir = Path(project_dir) / ".claude" / "workflow" / workflow_id / "logs"
    else:
        log_dir = Path(project_dir) / ".claude" / "workflow" / "logs"

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "actions.jsonl"

    # 構建記錄
    record = {
        "id": generate_id(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "workflow_id": workflow_id,
        "agent_id": agent_id,
        "stage": stage,
        "tool": tool,
        "status": status,
    }

    if input_data:
        record["input"] = input_data
    if output_preview:
        record["output_preview"] = output_preview[:500]
    if output_size:
        record["output_size"] = output_size
    if error:
        record["error"] = error
    if stderr:
        record["stderr"] = stderr[:1000]
    if exit_code is not None:
        record["exit_code"] = exit_code
    if duration_ms:
        record["duration_ms"] = duration_ms

    # 移除空值
    record = {k: v for k, v in record.items() if v not in (None, "", [])}

    # 寫入
    with open(log_file, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


def main():
    parser = argparse.ArgumentParser(description="Log action to actions.jsonl")
    parser.add_argument("--tool", required=True, help="Tool name")
    parser.add_argument("--status", required=True, choices=["success", "failed", "timeout", "skipped"])
    parser.add_argument("--input", help="Input JSON")
    parser.add_argument("--output-preview", help="Output preview")
    parser.add_argument("--output-size", type=int, help="Output size in bytes")
    parser.add_argument("--error", help="Error message")
    parser.add_argument("--stderr", help="Stderr output")
    parser.add_argument("--exit-code", type=int, help="Exit code")
    parser.add_argument("--duration-ms", type=int, help="Duration in ms")
    parser.add_argument("--project-dir", help="Project directory")
    parser.add_argument("--workflow-id", help="Workflow ID")
    parser.add_argument("--agent-id", help="Agent ID")
    parser.add_argument("--stage", help="Stage name")

    args = parser.parse_args()

    input_data = None
    if args.input:
        try:
            input_data = json.loads(args.input)
        except:
            input_data = {"raw": args.input}

    record = log_action(
        tool=args.tool,
        status=args.status,
        input_data=input_data,
        output_preview=args.output_preview,
        output_size=args.output_size,
        error=args.error,
        stderr=args.stderr,
        exit_code=args.exit_code,
        duration_ms=args.duration_ms,
        project_dir=args.project_dir,
        workflow_id=args.workflow_id,
        agent_id=args.agent_id,
        stage=args.stage,
    )

    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
