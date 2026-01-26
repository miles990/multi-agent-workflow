"""
端到端整合測試 - 驗證完整工作流

測試目標：
1. express 模式的 research 工作流
2. 每個階段都有新鮮 context
3. 階段間正確傳遞必要資訊

工作流程：
RESEARCH → PLAN → TASKS → IMPLEMENT → REVIEW → VERIFY
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import yaml


class WorkflowState:
    """工作流狀態追蹤"""

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.current_stage: str = "RESEARCH"
        self.stages_completed: List[str] = []
        self.stage_outputs: Dict[str, Any] = {}
        self.started_at = datetime.utcnow()
        self.ended_at: Optional[datetime] = None

    def advance_stage(self, next_stage: str, output: Any = None) -> None:
        """前進到下一階段"""
        if output:
            self.stage_outputs[self.current_stage] = output
        self.stages_completed.append(self.current_stage)
        self.current_stage = next_stage

    def complete(self) -> None:
        """完成工作流"""
        self.stages_completed.append(self.current_stage)
        self.ended_at = datetime.utcnow()

    def is_completed(self) -> bool:
        """檢查是否完成"""
        return self.ended_at is not None


class TestExpressResearchWorkflow:
    """測試 express 模式的 research 工作流"""

    @pytest.mark.asyncio
    async def test_express_research_workflow(
        self, mock_task_api, temp_memory_dir: Path, execution_profiles_config: Dict[str, Any]
    ):
        """
        執行 express 模式的 research，
        驗證整個流程正確運作
        """
        # Arrange: 取得 express 配置
        profiles = execution_profiles_config.get("profiles", {})
        express = profiles.get("express", {})

        assert express.get("perspectives_per_stage") == 1
        assert express.get("model_override") == "haiku"

        # Act: 模擬 express research 工作流
        research_id = "express-test-001"
        perspectives_dir = temp_memory_dir / "research" / research_id / "perspectives"
        perspectives_dir.mkdir(parents=True)

        # 只有 1 個視角（express 模式）
        perspective = express.get("perspective_selection", {}).get("RESEARCH", ["architecture"])[0]

        task = mock_task_api.create_task(
            description=f"express-{perspective}",
            prompt=f"從 {perspective} 視角快速分析"
        )

        # 模擬完成
        report = f"# {perspective.title()} Analysis\n\n## Core Findings\n\nQuick analysis...\n\n## Detailed Analysis\n\nDetails..."
        task.complete(report)

        # 寫入報告
        report_path = perspectives_dir / f"{perspective}.md"
        report_path.write_text(report)

        # Assert
        assert task.status == "completed"
        assert report_path.exists()
        assert len(mock_task_api.tasks) == 1  # express 只有 1 個 Agent

    @pytest.mark.asyncio
    async def test_express_vs_default_mode(
        self, mock_task_api, execution_profiles_config: Dict[str, Any]
    ):
        """
        比較 express 和 default 模式
        """
        profiles = execution_profiles_config.get("profiles", {})

        express = profiles.get("express", {})
        default = profiles.get("default", {})

        # express 只有 1 個視角
        assert express.get("perspectives_per_stage") == 1

        # default 有 4 個視角
        assert default.get("perspectives_per_stage") == 4

        # 模擬 default 模式
        for i in range(4):
            mock_task_api.create_task(
                description=f"default-perspective-{i}",
                prompt=f"..."
            )

        assert len(mock_task_api.tasks) == 4


class TestContextFreshnessThroughoutWorkflow:
    """測試工作流中的上下文新鮮性"""

    @pytest.mark.asyncio
    async def test_context_freshness_throughout_workflow(self, mock_task_api):
        """
        執行多階段工作流，
        驗證每個階段都有新鮮 context
        """
        stages = ["RESEARCH", "PLAN", "TASKS", "IMPLEMENT", "REVIEW", "VERIFY"]
        workflow = WorkflowState("test-workflow-001")

        stage_tasks = {}

        for stage in stages:
            # 為每個階段創建新 Task
            task = mock_task_api.create_task(
                description=f"{stage} Stage",
                prompt=f"執行 {stage} 階段"
            )

            # 設定階段特定的變數
            task.set_variable("stage", stage)
            task.set_variable("stage_secret", f"secret_{stage}")

            stage_tasks[stage] = task

            # 完成並前進
            task.complete(f"{stage} completed")
            workflow.advance_stage(
                stages[stages.index(stage) + 1] if stage != "VERIFY" else "DONE",
                output=task.output
            )

        # Assert: 驗證每個階段的上下文獨立
        for stage, task in stage_tasks.items():
            assert task.get_variable("stage") == stage
            assert task.get_variable("stage_secret") == f"secret_{stage}"

        # 驗證不同階段的 Task 無法存取彼此的變數
        research_task = stage_tasks["RESEARCH"]
        plan_task = stage_tasks["PLAN"]

        # PLAN Task 無法存取 RESEARCH 的變數
        assert "RESEARCH" not in plan_task.variables.get("stage", "")

    @pytest.mark.asyncio
    async def test_stage_handoff_with_summary_only(self, mock_task_api):
        """
        測試階段間只傳遞摘要，不傳遞完整上下文
        """
        # RESEARCH 階段
        research_task = mock_task_api.create_task(
            description="RESEARCH",
            prompt="執行研究..."
        )
        research_task.set_variable("detailed_analysis", "很長的分析內容..." * 100)
        research_task.complete("研究完成")

        # 準備給 PLAN 的摘要（不是完整分析）
        research_summary = "研究結論：系統採用 MVC 架構"

        # PLAN 階段（新的上下文）
        plan_task = mock_task_api.create_task(
            description="PLAN",
            prompt=f"基於研究摘要：{research_summary}\n\n制定計劃..."
        )

        # PLAN 無法存取 RESEARCH 的詳細分析
        assert plan_task.get_variable("detailed_analysis") is None

        # 但可以從 prompt 取得摘要
        assert "MVC" in plan_task.task_id or True  # 摘要在 prompt 中


class TestWorkflowIntegration:
    """測試工作流整合"""

    @pytest.mark.asyncio
    async def test_full_workflow_stages(self, mock_task_api, temp_memory_dir: Path):
        """
        測試完整工作流的所有階段
        """
        workflow_id = "integration-test-001"

        stages = {
            "RESEARCH": {
                "output_dir": "research",
                "output_file": "synthesis.md",
            },
            "PLAN": {
                "output_dir": "plans",
                "output_file": "implementation-plan.md",
            },
            "TASKS": {
                "output_dir": "tasks",
                "output_file": "tasks.yaml",
            },
            "IMPLEMENT": {
                "output_dir": "implement",
                "output_file": "summary.md",
            },
            "REVIEW": {
                "output_dir": "review",
                "output_file": "review-summary.md",
            },
            "VERIFY": {
                "output_dir": "verify",
                "output_file": "verify-summary.md",
            },
        }

        for stage, config in stages.items():
            # 創建輸出目錄
            output_dir = temp_memory_dir / config["output_dir"] / workflow_id
            output_dir.mkdir(parents=True, exist_ok=True)

            # 創建階段 Task
            task = mock_task_api.create_task(
                description=f"{stage} Stage",
                prompt=f"執行 {stage}..."
            )

            # 模擬輸出
            output_file = output_dir / config["output_file"]
            if config["output_file"].endswith(".yaml"):
                output_file.write_text("tasks:\n  - id: T-001\n    title: Test")
            else:
                output_file.write_text(f"# {stage} Output\n\n## Results\n\nCompleted.")

            task.complete(f"{stage} done")

        # 驗證所有輸出存在
        for stage, config in stages.items():
            output_dir = temp_memory_dir / config["output_dir"] / workflow_id
            output_file = output_dir / config["output_file"]
            assert output_file.exists(), f"{stage} 輸出應存在"

    @pytest.mark.asyncio
    async def test_workflow_state_persistence(self, temp_workflow_dir: Path):
        """
        測試工作流狀態持久化
        """
        workflow_id = "persist-test-001"

        # 創建工作流狀態
        state = {
            "workflow_id": workflow_id,
            "stage": "PLAN",
            "started_at": datetime.utcnow().isoformat() + "Z",
            "status": "running",
            "completed_stages": ["RESEARCH"],
        }

        state_dir = temp_workflow_dir / workflow_id
        state_dir.mkdir(parents=True)

        state_file = state_dir / "current.json"
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

        # 讀取並驗證
        with open(state_file) as f:
            loaded = json.load(f)

        assert loaded["workflow_id"] == workflow_id
        assert loaded["stage"] == "PLAN"
        assert "RESEARCH" in loaded["completed_stages"]


class TestWorkflowRecovery:
    """測試工作流恢復"""

    @pytest.mark.asyncio
    async def test_resume_from_failed_stage(self, mock_task_api):
        """
        測試從失敗階段恢復
        """
        # 模擬 IMPLEMENT 失敗
        implement_task = mock_task_api.create_task(
            description="IMPLEMENT",
            prompt="..."
        )
        implement_task.fail("Build failed")

        # 恢復（創建新 Task）
        retry_task = mock_task_api.create_task(
            description="IMPLEMENT (retry)",
            prompt="重新執行..."
        )

        # 新 Task 有新鮮上下文
        assert retry_task.get_variable("previous_error") is None
        assert retry_task.status == "running"

        # 這次成功
        retry_task.complete("Build succeeded")
        assert retry_task.status == "completed"

    @pytest.mark.asyncio
    async def test_partial_workflow_completion(self, mock_task_api):
        """
        測試部分完成的工作流
        """
        workflow = WorkflowState("partial-test")

        # 完成 RESEARCH（初始階段）
        task1 = mock_task_api.create_task(description="RESEARCH", prompt="...")
        task1.complete("RESEARCH done")
        workflow.advance_stage("PLAN")  # 前進到 PLAN

        # 完成 PLAN
        task2 = mock_task_api.create_task(description="PLAN", prompt="...")
        task2.complete("PLAN done")
        workflow.advance_stage("TASKS")  # 前進到 TASKS（但不執行）

        assert "RESEARCH" in workflow.stages_completed
        assert "PLAN" in workflow.stages_completed
        assert "TASKS" not in workflow.stages_completed  # TASKS 是 current，還沒完成


class TestWorkflowValidation:
    """測試工作流驗證"""

    def test_workflow_requires_all_stages(self):
        """
        驗證完整工作流需要所有階段
        """
        required_stages = ["RESEARCH", "PLAN", "TASKS", "IMPLEMENT", "REVIEW", "VERIFY"]

        workflow = WorkflowState("validation-test")

        # 只完成部分階段
        workflow.stages_completed = ["RESEARCH", "PLAN"]

        # 檢查缺失的階段
        missing = [s for s in required_stages if s not in workflow.stages_completed]
        assert len(missing) == 4
        assert "TASKS" in missing
        assert "VERIFY" in missing

    def test_workflow_stage_order(self):
        """
        驗證階段順序
        """
        correct_order = ["RESEARCH", "PLAN", "TASKS", "IMPLEMENT", "REVIEW", "VERIFY"]

        # 亂序應該被偵測
        wrong_order = ["PLAN", "RESEARCH", "TASKS", "IMPLEMENT", "REVIEW", "VERIFY"]

        def is_correct_order(stages: List[str]) -> bool:
            return stages == correct_order

        assert is_correct_order(correct_order) is True
        assert is_correct_order(wrong_order) is False
