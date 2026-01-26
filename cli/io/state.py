"""
即時狀態追蹤模組 - 管理 current.json

支援並行 Agent 的即時狀態追蹤：
- 工作流資訊
- 當前階段
- 多個 Agent 的狀態
- 進度統計
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from .memory import get_memory


AgentStatus = Literal["pending", "running", "completed", "failed"]
StageStatus = Literal["pending", "running", "completed", "failed", "skipped"]


class StateTracker:
    """即時狀態追蹤器"""

    def __init__(self, workflow_id: str, base_path: Optional[str] = None):
        """
        初始化狀態追蹤器

        Args:
            workflow_id: 工作流 ID
            base_path: Memory 根目錄
        """
        self.workflow_id = workflow_id
        self.memory = get_memory(base_path)

        workflow_dir = self.memory.get_workflow_dir(workflow_id)
        if workflow_dir:
            self.state_file = workflow_dir / "current.json"
        else:
            self.state_file = (
                self.memory.base_path / "workflows" / workflow_id / "current.json"
            )

        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # 初始化狀態
        if not self.state_file.exists():
            self._init_state()

    def _init_state(self) -> None:
        """初始化狀態檔案"""
        state = {
            "updated_at": datetime.now().isoformat(),
            "workflow": {
                "id": self.workflow_id,
                "topic": None,
            },
            "stage": None,
            "agents": [],
            "progress": {
                "agents_completed": 0,
                "agents_total": 0,
            },
        }
        self._save_state(state)

    def _load_state(self) -> Dict:
        """載入當前狀態"""
        return self.memory.read_json(self.state_file) or self._get_default_state()

    def _save_state(self, state: Dict) -> bool:
        """儲存狀態"""
        state["updated_at"] = datetime.now().isoformat()
        return self.memory.write_json(self.state_file, state)

    def _get_default_state(self) -> Dict:
        """取得預設狀態"""
        return {
            "updated_at": datetime.now().isoformat(),
            "workflow": {"id": self.workflow_id, "topic": None},
            "stage": None,
            "agents": [],
            "progress": {"agents_completed": 0, "agents_total": 0},
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 工作流狀態
    # ─────────────────────────────────────────────────────────────────────────

    def set_workflow(self, topic: str) -> None:
        """設定工作流資訊"""
        state = self._load_state()
        state["workflow"]["topic"] = topic
        self._save_state(state)

    # ─────────────────────────────────────────────────────────────────────────
    # 階段狀態
    # ─────────────────────────────────────────────────────────────────────────

    def set_stage(
        self,
        stage_id: str,
        stage_name: str,
        description: str,
        index: int,
        total: int,
    ) -> None:
        """
        設定當前階段

        Args:
            stage_id: 階段 ID (如 RESEARCH, PLAN)
            stage_name: 階段名稱 (如 研究階段)
            description: 階段描述
            index: 當前階段索引 (1-based)
            total: 總階段數
        """
        state = self._load_state()
        state["stage"] = {
            "id": stage_id,
            "name": stage_name,
            "description": description,
            "index": index,
            "total": total,
        }
        # 重置 agents
        state["agents"] = []
        state["progress"] = {"agents_completed": 0, "agents_total": 0}
        self._save_state(state)

    def clear_stage(self) -> None:
        """清除階段狀態"""
        state = self._load_state()
        state["stage"] = None
        state["agents"] = []
        state["progress"] = {"agents_completed": 0, "agents_total": 0}
        self._save_state(state)

    # ─────────────────────────────────────────────────────────────────────────
    # Agent 狀態
    # ─────────────────────────────────────────────────────────────────────────

    def add_agent(
        self,
        agent_id: str,
        agent_name: str,
        description: Optional[str] = None,
        model: str = "sonnet",
        task: Optional[str] = None,
    ) -> None:
        """
        新增 Agent

        Args:
            agent_id: Agent ID
            agent_name: Agent 名稱
            description: Agent 描述
            model: 使用的模型
            task: 分配的任務
        """
        state = self._load_state()

        # 檢查是否已存在
        existing = next(
            (a for a in state["agents"] if a["id"] == agent_id),
            None,
        )
        if existing:
            return

        agent = {
            "id": agent_id,
            "name": agent_name,
            "description": description,
            "model": model,
            "status": "pending",
            "task": task,
        }
        state["agents"].append(agent)
        state["progress"]["agents_total"] = len(state["agents"])
        self._save_state(state)

    def update_agent_status(
        self,
        agent_id: str,
        status: AgentStatus,
        task: Optional[str] = None,
    ) -> None:
        """
        更新 Agent 狀態

        Args:
            agent_id: Agent ID
            status: 新狀態
            task: 更新任務描述（可選）
        """
        state = self._load_state()

        for agent in state["agents"]:
            if agent["id"] == agent_id:
                agent["status"] = status
                if task:
                    agent["task"] = task
                break

        # 更新進度
        completed = sum(
            1 for a in state["agents"] if a["status"] in ["completed", "failed"]
        )
        state["progress"]["agents_completed"] = completed

        self._save_state(state)

    def set_agents(self, agents: List[Dict]) -> None:
        """
        批次設定 Agents

        Args:
            agents: Agent 列表，每個包含 id, name, description, model, status, task
        """
        state = self._load_state()
        state["agents"] = agents
        state["progress"]["agents_total"] = len(agents)
        state["progress"]["agents_completed"] = sum(
            1 for a in agents if a.get("status") in ["completed", "failed"]
        )
        self._save_state(state)

    # ─────────────────────────────────────────────────────────────────────────
    # 查詢方法
    # ─────────────────────────────────────────────────────────────────────────

    def get_state(self) -> Dict:
        """取得完整狀態"""
        return self._load_state()

    def get_stage(self) -> Optional[Dict]:
        """取得當前階段"""
        state = self._load_state()
        return state.get("stage")

    def get_agents(self) -> List[Dict]:
        """取得所有 Agents"""
        state = self._load_state()
        return state.get("agents", [])

    def get_progress(self) -> Dict:
        """取得進度統計"""
        state = self._load_state()
        return state.get("progress", {"agents_completed": 0, "agents_total": 0})

    def is_all_agents_done(self) -> bool:
        """檢查是否所有 Agents 都完成"""
        progress = self.get_progress()
        return (
            progress["agents_total"] > 0
            and progress["agents_completed"] >= progress["agents_total"]
        )


# 全域狀態追蹤器快取
_trackers: Dict[str, StateTracker] = {}


def get_tracker(workflow_id: str, base_path: Optional[str] = None) -> StateTracker:
    """取得狀態追蹤器實例"""
    if workflow_id not in _trackers:
        _trackers[workflow_id] = StateTracker(workflow_id, base_path)
    return _trackers[workflow_id]


def read_current_state(workflow_id: str, base_path: Optional[str] = None) -> Dict:
    """快速讀取當前狀態"""
    tracker = get_tracker(workflow_id, base_path)
    return tracker.get_state()
