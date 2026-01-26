"""
Action Log 模組 - 記錄所有操作

所有操作都以 JSONL 格式記錄到 logs/actions.jsonl

Actions:
- workflow_init: 工作流開始
- stage_start: 階段開始
- agent_start: Agent 開始
- agent_complete: Agent 完成
- agent_call_error: Agent 失敗
- file_write: 寫入檔案
- gate_check: 品質閘門
- gate_failed: 閘門失敗
- rollback_triggered: 觸發回退
- workflow_complete: 完成
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from .memory import get_memory


# Action 類型
ActionType = Literal[
    "workflow_init",
    "stage_start",
    "stage_complete",
    "agent_start",
    "agent_complete",
    "agent_call_error",
    "file_write",
    "gate_check",
    "gate_failed",
    "rollback_triggered",
    "workflow_complete",
    "workflow_error",
    "human_intervention",
]


class ActionLogger:
    """Action 日誌記錄器"""

    def __init__(self, workflow_id: str, base_path: Optional[str] = None):
        """
        初始化 Action Logger

        Args:
            workflow_id: 工作流 ID
            base_path: Memory 根目錄
        """
        self.workflow_id = workflow_id
        self.memory = get_memory(base_path)

        workflow_dir = self.memory.get_workflow_dir(workflow_id)
        if workflow_dir:
            self.log_file = workflow_dir / "logs" / "actions.jsonl"
        else:
            # 工作流尚未建立，使用臨時路徑
            self.log_file = self.memory.base_path / "workflows" / workflow_id / "logs" / "actions.jsonl"

        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        action: ActionType,
        details: Optional[Dict[str, Any]] = None,
        level: str = "info",
    ) -> Dict:
        """
        記錄一個 Action

        Args:
            action: Action 類型
            details: 詳細資訊
            level: 日誌等級 (info, warning, error)

        Returns:
            記錄的完整內容
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "workflow_id": self.workflow_id,
            "action": action,
            "level": level,
            "details": details or {},
        }

        self.memory.append_jsonl(self.log_file, record)
        return record

    # ─────────────────────────────────────────────────────────────────────────
    # 便捷方法
    # ─────────────────────────────────────────────────────────────────────────

    def workflow_init(self, topic: str, config: Optional[Dict] = None) -> Dict:
        """記錄工作流初始化"""
        return self.log(
            "workflow_init",
            {"topic": topic, "config": config or {}},
        )

    def stage_start(
        self,
        stage_id: str,
        stage_name: str,
        perspectives: Optional[List[str]] = None,
    ) -> Dict:
        """記錄階段開始"""
        return self.log(
            "stage_start",
            {
                "stage_id": stage_id,
                "stage_name": stage_name,
                "perspectives": perspectives or [],
            },
        )

    def stage_complete(
        self,
        stage_id: str,
        success: bool,
        duration_seconds: Optional[float] = None,
    ) -> Dict:
        """記錄階段完成"""
        return self.log(
            "stage_complete",
            {
                "stage_id": stage_id,
                "success": success,
                "duration_seconds": duration_seconds,
            },
            level="info" if success else "warning",
        )

    def agent_start(
        self,
        agent_id: str,
        agent_name: str,
        model: str,
        task: str,
    ) -> Dict:
        """記錄 Agent 開始"""
        return self.log(
            "agent_start",
            {
                "agent_id": agent_id,
                "agent_name": agent_name,
                "model": model,
                "task": task,
            },
        )

    def agent_complete(
        self,
        agent_id: str,
        success: bool,
        response_tokens: Optional[int] = None,
        duration_seconds: Optional[float] = None,
    ) -> Dict:
        """記錄 Agent 完成"""
        return self.log(
            "agent_complete",
            {
                "agent_id": agent_id,
                "success": success,
                "response_tokens": response_tokens,
                "duration_seconds": duration_seconds,
            },
            level="info" if success else "warning",
        )

    def agent_call_error(
        self,
        agent_id: str,
        reason: str,
        attempt: int,
        retryable: bool,
    ) -> Dict:
        """記錄 Agent 調用錯誤"""
        return self.log(
            "agent_call_error",
            {
                "agent_id": agent_id,
                "reason": reason,
                "attempt": attempt,
                "retryable": retryable,
            },
            level="error",
        )

    def file_write(self, path: str, size_bytes: int) -> Dict:
        """記錄檔案寫入"""
        return self.log(
            "file_write",
            {"path": path, "size_bytes": size_bytes},
        )

    def gate_check(
        self,
        stage: str,
        passed: bool,
        score: float,
        threshold: float,
    ) -> Dict:
        """記錄品質閘門檢查"""
        return self.log(
            "gate_check",
            {
                "stage": stage,
                "passed": passed,
                "score": score,
                "threshold": threshold,
            },
            level="info" if passed else "warning",
        )

    def gate_failed(self, stage: str, failed_criteria: List[str]) -> Dict:
        """記錄閘門失敗"""
        return self.log(
            "gate_failed",
            {"stage": stage, "failed_criteria": failed_criteria},
            level="error",
        )

    def rollback_triggered(
        self,
        from_stage: str,
        to_stage: str,
        iteration: int,
        reason: str,
    ) -> Dict:
        """記錄回退觸發"""
        return self.log(
            "rollback_triggered",
            {
                "from_stage": from_stage,
                "to_stage": to_stage,
                "iteration": iteration,
                "reason": reason,
            },
            level="warning",
        )

    def workflow_complete(
        self,
        duration_seconds: float,
        final_status: str,
        quality_score: Optional[float] = None,
    ) -> Dict:
        """記錄工作流完成"""
        return self.log(
            "workflow_complete",
            {
                "duration_seconds": duration_seconds,
                "final_status": final_status,
                "quality_score": quality_score,
            },
        )

    def workflow_error(self, error: str, stage: Optional[str] = None) -> Dict:
        """記錄工作流錯誤"""
        return self.log(
            "workflow_error",
            {"error": error, "stage": stage},
            level="error",
        )

    def human_intervention(self, reason: str, context: Optional[Dict] = None) -> Dict:
        """記錄需要人工介入"""
        return self.log(
            "human_intervention",
            {"reason": reason, "context": context or {}},
            level="warning",
        )

    # ─────────────────────────────────────────────────────────────────────────
    # 查詢方法
    # ─────────────────────────────────────────────────────────────────────────

    def get_logs(
        self,
        action_filter: Optional[List[ActionType]] = None,
        level_filter: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """
        取得日誌記錄

        Args:
            action_filter: 只包含指定的 action 類型
            level_filter: 只包含指定的 level
            limit: 限制返回數量（最新的）

        Returns:
            日誌記錄列表
        """
        records = self.memory.read_jsonl(self.log_file)

        if action_filter:
            records = [r for r in records if r.get("action") in action_filter]

        if level_filter:
            records = [r for r in records if r.get("level") in level_filter]

        if limit:
            records = records[-limit:]

        return records

    def get_errors(self) -> List[Dict]:
        """取得所有錯誤記錄"""
        return self.get_logs(level_filter=["error"])

    def get_stage_logs(self, stage: str) -> List[Dict]:
        """取得指定階段的日誌"""
        records = self.memory.read_jsonl(self.log_file)
        return [
            r
            for r in records
            if r.get("details", {}).get("stage_id", "").upper() == stage.upper()
            or r.get("details", {}).get("stage", "").upper() == stage.upper()
        ]


# 全域 Logger 實例快取
_loggers: Dict[str, ActionLogger] = {}


def get_logger(workflow_id: str, base_path: Optional[str] = None) -> ActionLogger:
    """取得 Action Logger 實例"""
    if workflow_id not in _loggers:
        _loggers[workflow_id] = ActionLogger(workflow_id, base_path)
    return _loggers[workflow_id]
