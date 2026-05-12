#!/usr/bin/env python3
"""
Workflow Initialization - CP1 檢查點

用法：
  python init_workflow.py --topic "用戶認證系統" --stage RESEARCH

功能：
1. 生成 workflow_id
2. 建立工作流目錄結構
3. 初始化 current.json 狀態
4. 記錄 workflow_init action
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from update_state import update_state
from log_action import log_action


STAGE_INFO = {
    "RESEARCH": {"name": "研究階段", "index": 1, "total": 6},
    "PLAN": {"name": "規劃階段", "index": 2, "total": 6},
    "TASKS": {"name": "任務分解", "index": 3, "total": 6},
    "IMPLEMENT": {"name": "實作階段", "index": 4, "total": 6},
    "REVIEW": {"name": "審查階段", "index": 5, "total": 6},
    "VERIFY": {"name": "驗證階段", "index": 6, "total": 6},
}


def generate_workflow_id(topic: str) -> str:
    """生成 workflow ID"""
    # 格式: {topic_slug}_{date}_{hash}
    slug = topic.lower()[:20].replace(" ", "-").replace("_", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    date = datetime.now().strftime("%Y%m%d")
    hash_part = hashlib.md5(f"{topic}{datetime.now().isoformat()}".encode()).hexdigest()[:6]
    return f"{slug}_{date}_{hash_part}"


def init_workflow(topic: str, stage: str, project_dir: str = None):
    """初始化工作流 (CP1)"""
    project_dir = project_dir or os.getcwd()

    # 生成 ID
    workflow_id = generate_workflow_id(topic)

    # 建立目錄結構
    workflow_dir = Path(project_dir) / ".claude" / "workflow" / workflow_id
    (workflow_dir / "logs").mkdir(parents=True, exist_ok=True)

    # 取得階段資訊
    stage_info = STAGE_INFO.get(stage.upper(), STAGE_INFO["RESEARCH"])

    # 初始化狀態
    state = update_state(
        project_dir=project_dir,
        workflow_id=workflow_id,
        topic=topic,
        stage=stage.upper(),
        stage_name=stage_info["name"],
        stage_index=stage_info["index"],
        stage_total=stage_info["total"],
    )

    # 記錄 workflow_init action
    log_action(
        tool="Workflow",
        status="success",
        input_data={
            "action": "workflow_init",
            "topic": topic,
            "stage": stage.upper(),
        },
        project_dir=project_dir,
        workflow_id=workflow_id,
    )

    return {
        "workflow_id": workflow_id,
        "workflow_dir": str(workflow_dir),
        "state": state,
    }


def main():
    parser = argparse.ArgumentParser(description="Initialize workflow (CP1)")
    parser.add_argument("--topic", required=True, help="Workflow topic")
    parser.add_argument("--stage", default="RESEARCH", help="Starting stage")
    parser.add_argument("--project-dir", help="Project directory")

    args = parser.parse_args()

    result = init_workflow(
        topic=args.topic,
        stage=args.stage,
        project_dir=args.project_dir,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
