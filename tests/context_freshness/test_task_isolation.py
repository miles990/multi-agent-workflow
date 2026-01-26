"""
Task 獨立性測試 - 驗證 Task = Fresh Context 原則

測試目標：
1. 並行 Tasks 擁有隔離的上下文
2. 子 Task 不繼承父 Task 的上下文變數
3. 連續 Tasks 各自從空上下文開始

核心原理：
- 每個 Claude Code Task 都是獨立的 context window
- Task 之間不共享狀態
- Task 完成 = 上下文足夠的驗證
"""

import asyncio
from typing import Any, Dict, List

import pytest


class TestParallelTaskIsolation:
    """測試並行 Task 的上下文隔離"""

    @pytest.mark.asyncio
    async def test_parallel_tasks_have_isolated_context(self, mock_task_api):
        """
        啟動 2 個並行 Task，各自設定不同的「記憶」變數，
        驗證它們不會互相看到對方的變數
        """
        # Arrange: 建立兩個並行 Task
        task1 = mock_task_api.create_task(
            description="Task 1 - Architecture Analysis",
            prompt="分析架構..."
        )
        task2 = mock_task_api.create_task(
            description="Task 2 - Workflow Analysis",
            prompt="分析工作流..."
        )

        # Act: 各自設定不同的變數
        task1.set_variable("analysis_type", "architecture")
        task1.set_variable("secret_key", "task1_secret")

        task2.set_variable("analysis_type", "workflow")
        task2.set_variable("secret_key", "task2_secret")

        # Assert: 驗證隔離
        # Task 1 不應該看到 Task 2 的變數
        assert task1.get_variable("analysis_type") == "architecture"
        assert task1.get_variable("secret_key") == "task1_secret"

        # Task 2 不應該看到 Task 1 的變數
        assert task2.get_variable("analysis_type") == "workflow"
        assert task2.get_variable("secret_key") == "task2_secret"

        # 驗證各自的變數空間獨立
        assert task1.variables != task2.variables
        assert id(task1.variables) != id(task2.variables)

    @pytest.mark.asyncio
    async def test_parallel_tasks_outputs_independent(self, mock_task_api):
        """
        驗證並行 Task 的輸出互不干擾
        """
        # Arrange: 建立四個並行 Task（模擬 4 視角）
        perspectives = ["architecture", "cognitive", "workflow", "industry"]
        tasks = []

        for perspective in perspectives:
            task = mock_task_api.create_task(
                description=f"{perspective} perspective",
                prompt=f"從 {perspective} 視角分析..."
            )
            tasks.append(task)

        # Act: 各自完成並輸出不同結果
        for i, task in enumerate(tasks):
            task.complete(f"Report from {perspectives[i]} perspective")

        # Assert: 驗證輸出獨立
        for i, task in enumerate(tasks):
            assert task.output == f"Report from {perspectives[i]} perspective"
            assert task.status == "completed"

        # 確認沒有輸出被覆蓋
        outputs = [t.output for t in tasks]
        assert len(set(outputs)) == 4  # 4 個不同的輸出


class TestTaskInheritance:
    """測試 Task 不繼承父上下文"""

    @pytest.mark.asyncio
    async def test_task_does_not_inherit_parent_context(self, mock_task_api):
        """
        父 Task 設定變數後啟動子 Task，
        驗證子 Task 無法存取父 Task 的變數
        """
        # Arrange: 建立父 Task 並設定變數
        parent_task = mock_task_api.create_task(
            description="Parent Orchestrator",
            prompt="協調子任務..."
        )
        parent_task.set_variable("parent_secret", "sensitive_data")
        parent_task.set_variable("workflow_state", {"stage": "RESEARCH"})

        # Act: 建立子 Task
        child_task = mock_task_api.create_task(
            description="Child Worker",
            prompt="執行子任務..."
        )

        # Assert: 子 Task 無法存取父 Task 的變數
        assert child_task.get_variable("parent_secret") is None
        assert child_task.get_variable("workflow_state") is None

        # 子 Task 的變數空間是空的
        assert len(child_task.variables) == 0

        # 父 Task 的變數仍然存在
        assert parent_task.get_variable("parent_secret") == "sensitive_data"

    @pytest.mark.asyncio
    async def test_child_task_modifications_do_not_affect_parent(self, mock_task_api):
        """
        子 Task 設定的變數不會影響父 Task
        """
        # Arrange
        parent_task = mock_task_api.create_task(
            description="Parent",
            prompt="..."
        )
        parent_task.set_variable("shared_name", "parent_value")

        # Act: 子 Task 設定同名變數
        child_task = mock_task_api.create_task(
            description="Child",
            prompt="..."
        )
        child_task.set_variable("shared_name", "child_value")

        # Assert: 父 Task 的變數不受影響
        assert parent_task.get_variable("shared_name") == "parent_value"
        assert child_task.get_variable("shared_name") == "child_value"


class TestSequentialTaskFreshness:
    """測試連續 Task 的上下文新鮮性"""

    @pytest.mark.asyncio
    async def test_sequential_tasks_start_fresh(self, mock_task_api):
        """
        依序執行多個 Task，
        驗證後續 Task 不會繼承前一個 Task 的 context
        """
        # Arrange & Act: 依序建立並完成多個 Task
        task1 = mock_task_api.create_task(
            description="Step 1 - Research",
            prompt="..."
        )
        task1.set_variable("step1_data", {"findings": ["a", "b", "c"]})
        task1.read_file("/path/to/research.md")
        task1.complete("Research completed")

        task2 = mock_task_api.create_task(
            description="Step 2 - Plan",
            prompt="..."
        )
        task2.set_variable("step2_data", {"milestones": [1, 2, 3]})
        task2.read_file("/path/to/plan.md")
        task2.complete("Plan completed")

        task3 = mock_task_api.create_task(
            description="Step 3 - Implement",
            prompt="..."
        )

        # Assert: 第三個 Task 無法存取前面 Task 的變數
        assert task3.get_variable("step1_data") is None
        assert task3.get_variable("step2_data") is None

        # 第三個 Task 沒有繼承前面的檔案讀取記錄
        assert len(task3.read_files) == 0

        # 確認前面的 Task 仍保有自己的狀態
        assert task1.get_variable("step1_data") is not None
        assert task2.get_variable("step2_data") is not None

    @pytest.mark.asyncio
    async def test_task_context_cleared_after_completion(self, mock_task_api):
        """
        Task 完成後，其上下文不會被下一個 Task 繼承
        """
        # Arrange: 建立並完成第一個 Task
        task1 = mock_task_api.create_task(
            description="Completed Task",
            prompt="..."
        )
        task1.set_variable("temporary_data", "should_not_persist")
        task1.complete("Done")

        # 驗證 Task 1 已完成
        assert task1.status == "completed"

        # Act: 建立新 Task
        task2 = mock_task_api.create_task(
            description="New Fresh Task",
            prompt="..."
        )

        # Assert: 新 Task 從空上下文開始
        assert task2.get_variable("temporary_data") is None
        assert task2.status == "running"
        assert len(task2.variables) == 0

    @pytest.mark.asyncio
    async def test_failed_task_context_also_isolated(self, mock_task_api):
        """
        即使 Task 失敗，其上下文也不會影響下一個 Task
        """
        # Arrange: 建立並失敗第一個 Task
        task1 = mock_task_api.create_task(
            description="Failed Task",
            prompt="..."
        )
        task1.set_variable("error_state", "something_wrong")
        task1.fail("Task failed due to error")

        # 驗證 Task 1 已失敗
        assert task1.status == "failed"

        # Act: 建立新 Task
        task2 = mock_task_api.create_task(
            description="Recovery Task",
            prompt="..."
        )

        # Assert: 新 Task 不受失敗 Task 影響
        assert task2.get_variable("error_state") is None
        assert task2.status == "running"


class TestContextFreshnessPrinciple:
    """測試 Context Freshness 核心原則"""

    def test_task_equals_fresh_context_principle(self, mock_task_api):
        """
        驗證 Task = Fresh Context 原則：
        每個 Task 天生就有獨立的上下文
        """
        # 建立多個 Task
        tasks = [
            mock_task_api.create_task(f"Task {i}", f"Prompt {i}")
            for i in range(5)
        ]

        # 驗證每個 Task 都是獨立的
        task_ids = [t.task_id for t in tasks]
        assert len(set(task_ids)) == 5  # 5 個不同的 ID

        # 驗證變數空間獨立
        variable_spaces = [id(t.variables) for t in tasks]
        assert len(set(variable_spaces)) == 5  # 5 個不同的記憶體位置

    def test_no_shared_state_between_tasks(self, mock_task_api):
        """
        驗證 Tasks 之間沒有共享狀態
        """
        # 建立 Task 並修改 "全域" 風格的變數名
        task1 = mock_task_api.create_task("Task 1", "...")
        task1.set_variable("GLOBAL_CONFIG", {"setting": "value1"})

        task2 = mock_task_api.create_task("Task 2", "...")
        task2.set_variable("GLOBAL_CONFIG", {"setting": "value2"})

        # 即使變數名相同，值也是獨立的
        assert task1.get_variable("GLOBAL_CONFIG")["setting"] == "value1"
        assert task2.get_variable("GLOBAL_CONFIG")["setting"] == "value2"

    def test_task_completion_validates_sufficient_context(self, mock_task_api):
        """
        驗證 Task 完成本身就是「上下文足夠」的驗證
        """
        # 建立 Task
        task = mock_task_api.create_task(
            description="Analysis Task",
            prompt="分析並產出報告"
        )

        # 模擬 Agent 工作過程
        task.read_file("shared/config/context-freshness.yaml")
        task.set_variable("analysis_result", {"key": "findings"})
        task.write_file(".claude/memory/research/test/perspectives/report.md", "# Report")

        # Task 完成
        task.complete("分析完成，報告已寫入")

        # Assert: 完成狀態驗證上下文足夠
        assert task.status == "completed"
        assert task.output is not None
        assert len(task.read_files) > 0  # 有讀取檔案
        assert len(task.written_files) > 0  # 有寫入檔案
