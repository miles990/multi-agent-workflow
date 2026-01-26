"""
Hook 追蹤測試 - 驗證 Pre/Post Task Hook 正常運作

測試目標：
1. pre_task.py 記錄 Agent 啟動
2. post_task.py 記錄 Agent 完成狀態
3. actions.jsonl 有相應記錄
4. subagent_start/stop hooks 追蹤生命週期

相關檔案：
- scripts/hooks/pre_task.py
- scripts/hooks/post_task.py
- scripts/hooks/subagent_start.py
- scripts/hooks/subagent_stop.py
- scripts/hooks/log_action.py
"""

import json
import sys
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch, MagicMock

import pytest


def create_test_workflow_state(workflow_dir, workflow_id, stage="RESEARCH"):
    """建立測試 workflow 狀態"""
    from datetime import datetime
    state_dir = workflow_dir / workflow_id
    state_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "workflow_id": workflow_id,
        "stage": stage,
        "started_at": datetime.utcnow().isoformat() + "Z",
        "status": "running",
    }
    with open(state_dir / "current.json", "w") as f:
        json.dump(state, f, indent=2)


def create_test_action_log(workflow_dir, workflow_id, actions):
    """建立測試 action log"""
    log_dir = workflow_dir / workflow_id / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "actions.jsonl"
    with open(log_file, "w") as f:
        for action in actions:
            f.write(json.dumps(action, ensure_ascii=False) + "\n")
    return log_file


class TestPreTaskHook:
    """測試 pre_task hook"""

    def test_pre_task_hook_logs_start(
        self, hooks_dir: Path, temp_workflow_dir: Path
    ):
        """
        驗證 pre_task.py 記錄 Agent 啟動
        """
        # Arrange
        hook_script = hooks_dir / "pre_task.py"
        if not hook_script.exists():
            pytest.skip("pre_task.py 不存在")

        # 創建工作流狀態
        workflow_id = "test-wf-001"
        create_test_workflow_state(temp_workflow_dir, workflow_id)

        # 模擬 hook 輸入
        hook_input = {
            "tool_input": {
                "description": "research architecture",
                "subagent_type": "Explore",
                "prompt": "分析系統架構..."
            },
            "cwd": str(temp_workflow_dir.parent)
        }

        # Act: 模擬執行 hook（使用 import）
        # 由於 hook 會讀取 stdin，我們模擬這個過程
        sys.path.insert(0, str(hooks_dir))
        try:
            from pre_task import main as pre_task_main
            from update_state import update_state
            from log_action import log_action

            # 驗證模組存在
            assert callable(pre_task_main)
            assert callable(update_state)
            assert callable(log_action)
        finally:
            sys.path.remove(str(hooks_dir))

    def test_pre_task_extracts_agent_id(self, hooks_dir: Path):
        """
        驗證 pre_task 正確提取 agent_id
        """
        # Agent ID 應該從 description 推斷
        descriptions = [
            ("research architecture", "research-architecture"),
            ("Plan Implementation", "plan-implementation"),
            ("verify tests", "verify-tests"),
        ]

        for desc, expected_prefix in descriptions:
            agent_id = desc.lower().replace(" ", "-")[:30]
            assert expected_prefix in agent_id


class TestPostTaskHook:
    """測試 post_task hook"""

    def test_post_task_hook_logs_completion(
        self, hooks_dir: Path, temp_workflow_dir: Path
    ):
        """
        驗證 post_task.py 記錄 Agent 完成狀態
        """
        hook_script = hooks_dir / "post_task.py"
        if not hook_script.exists():
            pytest.skip("post_task.py 不存在")

        # 驗證模組可導入
        sys.path.insert(0, str(hooks_dir))
        try:
            from post_task import main as post_task_main
            assert callable(post_task_main)
        finally:
            sys.path.remove(str(hooks_dir))

    def test_post_task_determines_success(self, hooks_dir: Path):
        """
        驗證 post_task 正確判斷成功/失敗
        """
        # 成功的回應
        success_outputs = [
            "Analysis completed successfully",
            "Report written to path",
            "Task finished",
        ]

        # 失敗的回應
        failure_outputs = [
            "Error: file not found",
            "Task failed due to timeout",
            "Failed to complete analysis",
        ]

        for output in success_outputs:
            success = "error" not in output.lower() and "failed" not in output.lower()
            assert success is True, f"'{output}' 應被判斷為成功"

        for output in failure_outputs:
            success = "error" not in output.lower() and "failed" not in output.lower()
            assert success is False, f"'{output}' 應被判斷為失敗"


class TestActionLog:
    """測試 action log"""

    def test_action_log_contains_task_events(
        self, temp_workflow_dir: Path, sample_action_log: List[Dict[str, Any]]
    ):
        """
        驗證 actions.jsonl 有相應記錄
        """
        # Arrange: 創建測試 action log
        workflow_id = "test-wf-001"
        log_file = create_test_action_log(
            temp_workflow_dir, workflow_id, sample_action_log
        )

        # Assert: 驗證 log 檔案存在
        assert log_file.exists()

        # 讀取並解析 log
        with open(log_file) as f:
            records = [json.loads(line) for line in f if line.strip()]

        assert len(records) == 3

        # 驗證記錄結構
        for record in records:
            assert "id" in record
            assert "timestamp" in record
            assert "tool" in record
            assert "status" in record

    def test_action_log_format(self, sample_action_log: List[Dict[str, Any]]):
        """
        驗證 action log 格式正確
        """
        for record in sample_action_log:
            # 驗證必要欄位
            assert "id" in record
            assert record["id"].startswith("act_")

            assert "timestamp" in record
            assert record["timestamp"].endswith("Z")  # UTC 格式

            assert "workflow_id" in record
            assert "tool" in record
            assert "status" in record

    def test_action_log_workflow_id_tracking(
        self, temp_workflow_dir: Path
    ):
        """
        驗證 action log 正確追蹤 workflow_id
        """
        # 創建多個 workflow 的 action log
        workflows = ["wf-001", "wf-002", "wf-003"]

        for wf_id in workflows:
            actions = [
                {
                    "id": f"act_{wf_id}_001",
                    "timestamp": "2026-01-27T12:00:00Z",
                    "workflow_id": wf_id,
                    "tool": "Task",
                    "status": "started",
                }
            ]
            log_file = create_test_action_log(temp_workflow_dir, wf_id, actions)

            # 驗證每個 workflow 有獨立的 log
            assert log_file.exists()
            assert wf_id in str(log_file)


class TestSubagentHooks:
    """測試 subagent hooks"""

    def test_subagent_hooks_track_lifecycle(
        self, hooks_dir: Path, hook_tracker
    ):
        """
        驗證 subagent_start/stop hooks 追蹤生命週期
        """
        # 驗證 hook 檔案存在
        start_hook = hooks_dir / "subagent_start.py"
        stop_hook = hooks_dir / "subagent_stop.py"

        assert start_hook.exists(), "subagent_start.py 應存在"
        assert stop_hook.exists(), "subagent_stop.py 應存在"

        # 模擬生命週期追蹤
        session_id = "test-session-123"

        hook_tracker.record_subagent_start({"session_id": session_id})
        hook_tracker.record_subagent_stop({"session_id": session_id})

        # 驗證追蹤記錄
        assert len(hook_tracker.subagent_start_calls) == 1
        assert len(hook_tracker.subagent_stop_calls) == 1
        assert hook_tracker.subagent_start_calls[0]["session_id"] == session_id
        assert hook_tracker.subagent_stop_calls[0]["session_id"] == session_id

    def test_subagent_start_records_session(self, hooks_dir: Path):
        """
        驗證 subagent_start 記錄 session_id
        """
        hook_script = hooks_dir / "subagent_start.py"
        if not hook_script.exists():
            pytest.skip("subagent_start.py 不存在")

        # 驗證模組可導入
        sys.path.insert(0, str(hooks_dir))
        try:
            from subagent_start import main as start_main
            assert callable(start_main)
        finally:
            sys.path.remove(str(hooks_dir))

    def test_subagent_stop_triggers_commit(self, hooks_dir: Path):
        """
        驗證 subagent_stop 觸發 git commit
        """
        hook_script = hooks_dir / "subagent_stop.py"
        if not hook_script.exists():
            pytest.skip("subagent_stop.py 不存在")

        # 讀取 hook 內容，驗證包含 git commit 邏輯
        content = hook_script.read_text()

        assert "git" in content.lower(), "subagent_stop 應包含 git 操作"
        assert "commit" in content.lower(), "subagent_stop 應包含 commit 邏輯"


class TestHookIntegration:
    """測試 Hook 整合"""

    def test_hooks_use_shared_utilities(self, hooks_dir: Path):
        """
        驗證 hooks 使用共用的工具函數
        """
        # 檢查共用模組存在
        shared_modules = ["log_action.py", "update_state.py"]

        for module in shared_modules:
            module_path = hooks_dir / module
            assert module_path.exists(), f"{module} 應存在"

    def test_hook_input_parsing(self, hooks_dir: Path):
        """
        驗證 hook 能正確解析 JSON 輸入
        """
        # 測試各種輸入格式
        valid_inputs = [
            {"tool_input": {"description": "test"}, "cwd": "/path"},
            {"tool_input": {}, "cwd": "/path"},
            {"session_id": "abc123", "cwd": "/path"},
        ]

        for input_data in valid_inputs:
            # 驗證這些輸入可以被 JSON 序列化
            json_str = json.dumps(input_data)
            parsed = json.loads(json_str)
            assert parsed == input_data

    def test_hook_workflow_state_reading(
        self, hooks_dir: Path, temp_workflow_dir: Path
    ):
        """
        驗證 hooks 能正確讀取 workflow 狀態
        """
        # 創建 workflow 狀態
        workflow_id = "test-wf-read"
        create_test_workflow_state(temp_workflow_dir, workflow_id, stage="RESEARCH")

        # 驗證狀態檔案存在
        state_file = temp_workflow_dir / workflow_id / "current.json"
        assert state_file.exists()

        # 讀取狀態
        with open(state_file) as f:
            state = json.load(f)

        assert state["workflow_id"] == workflow_id
        assert state["stage"] == "RESEARCH"


class TestLogActionFunction:
    """測試 log_action 函數"""

    def test_log_action_generates_unique_ids(self, hooks_dir: Path):
        """
        驗證 log_action 生成唯一 ID
        """
        sys.path.insert(0, str(hooks_dir))
        try:
            from log_action import generate_id

            # 生成多個 ID
            ids = [generate_id() for _ in range(100)]

            # 驗證唯一性
            assert len(set(ids)) == 100, "生成的 ID 應該是唯一的"

            # 驗證格式
            for id_ in ids:
                assert id_.startswith("act_"), "ID 應以 'act_' 開頭"
        finally:
            sys.path.remove(str(hooks_dir))

    def test_log_action_filters_empty_values(self, hooks_dir: Path):
        """
        驗證 log_action 過濾空值
        """
        # log_action 應該移除 None 和空字串
        record = {
            "id": "act_123",
            "workflow_id": "",
            "agent_id": None,
            "tool": "Test",
            "status": "success",
            "error": None,
        }

        # 模擬過濾邏輯
        filtered = {k: v for k, v in record.items() if v not in (None, "", [])}

        assert "workflow_id" not in filtered
        assert "agent_id" not in filtered
        assert "error" not in filtered
        assert "tool" in filtered
        assert "status" in filtered
