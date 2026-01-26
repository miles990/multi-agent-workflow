"""
並行執行測試 - 驗證多 Agent 不互相干擾

測試目標：
1. 4 個視角 Agent 同時執行
2. 並行輸出互不干擾
3. 單一 Agent 失敗不影響其他 Agent

核心原理：
- Map-Reduce 模式：並行分析，獨立產出
- 失敗隔離：一個失敗不影響整體
- 結果獨立：各視角報告互不覆蓋
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

import pytest


class TestParallelPerspectives:
    """測試多視角並行執行"""

    @pytest.mark.asyncio
    async def test_four_perspectives_run_in_parallel(self, mock_task_api):
        """
        啟動 4 個視角 Agent，驗證並行執行
        """
        # Arrange: 定義 4 個視角
        perspectives = [
            {
                "id": "architecture",
                "name": "架構分析師",
                "focus": "系統結構、設計模式",
            },
            {
                "id": "cognitive",
                "name": "認知研究員",
                "focus": "方法論、思維框架",
            },
            {
                "id": "workflow",
                "name": "工作流設計師",
                "focus": "執行流程、整合策略",
            },
            {
                "id": "industry",
                "name": "業界實踐專家",
                "focus": "現有框架、最佳實踐",
            },
        ]

        # Act: 並行啟動 4 個 Agent
        agents = []
        for p in perspectives:
            agent = mock_task_api.create_task(
                description=f"{p['id']} perspective",
                prompt=f"你是一位 {p['name']}，專注於 {p['focus']}"
            )
            agents.append(agent)

        # Assert: 驗證 4 個 Agent 同時存在
        assert len(agents) == 4
        assert len(mock_task_api.tasks) == 4

        # 驗證都在運行狀態
        for agent in agents:
            assert agent.status == "running"

        # 驗證啟動時間接近（模擬並行）
        start_times = [a.start_time for a in agents]
        time_spread = (max(start_times) - min(start_times)).total_seconds()
        assert time_spread < 1, "並行啟動的 Agent 時間差應小於 1 秒"

    @pytest.mark.asyncio
    async def test_parallel_outputs_are_independent(self, mock_task_api):
        """
        驗證 4 個輸出互不干擾
        """
        # Arrange: 建立 4 個 Agent
        outputs = {
            "architecture": "發現系統採用 MVC 架構...",
            "cognitive": "使用者認知負載分析...",
            "workflow": "工作流程優化建議...",
            "industry": "與業界標準比較...",
        }

        agents = {}
        for perspective, expected_output in outputs.items():
            agent = mock_task_api.create_task(
                description=f"{perspective}",
                prompt=f"從 {perspective} 視角分析"
            )
            agents[perspective] = agent

        # Act: 各自完成並輸出
        for perspective, agent in agents.items():
            agent.complete(outputs[perspective])

        # Assert: 驗證輸出獨立且正確
        for perspective, agent in agents.items():
            assert agent.output == outputs[perspective]
            assert agent.status == "completed"

        # 驗證沒有輸出被覆蓋或混淆
        all_outputs = [a.output for a in agents.values()]
        assert len(set(all_outputs)) == 4, "每個 Agent 應有唯一輸出"

    @pytest.mark.asyncio
    async def test_parallel_variables_isolated(self, mock_task_api):
        """
        驗證並行 Agent 的變數完全隔離
        """
        # 建立 Agent 並設定相同名稱但不同值的變數
        agents = []
        for i in range(4):
            agent = mock_task_api.create_task(
                description=f"Agent {i}",
                prompt="..."
            )
            agent.set_variable("shared_name", f"value_{i}")
            agent.set_variable("unique_var", f"unique_{i}")
            agents.append(agent)

        # 驗證隔離
        for i, agent in enumerate(agents):
            assert agent.get_variable("shared_name") == f"value_{i}"
            assert agent.get_variable("unique_var") == f"unique_{i}"

        # 修改一個 Agent 的變數不影響其他
        agents[0].set_variable("shared_name", "modified")
        assert agents[1].get_variable("shared_name") == "value_1"
        assert agents[2].get_variable("shared_name") == "value_2"


class TestFailureIsolation:
    """測試失敗隔離"""

    @pytest.mark.asyncio
    async def test_parallel_failures_are_isolated(self, mock_task_api):
        """
        一個 Agent 失敗不影響其他 Agent
        """
        # Arrange: 建立 4 個 Agent
        agents = []
        for i in range(4):
            agent = mock_task_api.create_task(
                description=f"Perspective {i}",
                prompt=f"分析視角 {i}"
            )
            agents.append(agent)

        # Act: 第 2 個 Agent 失敗，其他成功
        agents[0].complete("成功完成分析 0")
        agents[1].fail("無法存取必要資源")
        agents[2].complete("成功完成分析 2")
        agents[3].complete("成功完成分析 3")

        # Assert: 驗證失敗隔離
        assert agents[0].status == "completed"
        assert agents[1].status == "failed"
        assert agents[2].status == "completed"
        assert agents[3].status == "completed"

        # 成功的 Agent 輸出正常
        assert agents[0].output == "成功完成分析 0"
        assert agents[2].output == "成功完成分析 2"
        assert agents[3].output == "成功完成分析 3"

        # 失敗的 Agent 有錯誤訊息
        assert "無法存取" in agents[1].output

    @pytest.mark.asyncio
    async def test_majority_success_still_valuable(self, mock_task_api):
        """
        即使部分失敗，成功的結果仍有價值
        """
        # 建立 4 個 Agent
        agents = []
        for i in range(4):
            agent = mock_task_api.create_task(
                description=f"Analyst {i}",
                prompt=f"分析 {i}"
            )
            agents.append(agent)

        # 2 個成功，2 個失敗
        agents[0].complete("Valuable insight 1")
        agents[1].fail("Error 1")
        agents[2].complete("Valuable insight 2")
        agents[3].fail("Error 2")

        # 收集成功的結果
        successful_outputs = [
            a.output for a in agents if a.status == "completed"
        ]

        assert len(successful_outputs) == 2
        assert "Valuable insight 1" in successful_outputs
        assert "Valuable insight 2" in successful_outputs

    @pytest.mark.asyncio
    async def test_all_failures_detected(self, mock_task_api):
        """
        全部失敗時能被正確偵測
        """
        agents = []
        for i in range(4):
            agent = mock_task_api.create_task(
                description=f"Agent {i}",
                prompt=f"..."
            )
            agent.fail(f"Error {i}")
            agents.append(agent)

        # 驗證全部失敗
        failed_count = sum(1 for a in agents if a.status == "failed")
        assert failed_count == 4

        # 沒有成功的輸出
        successful = [a for a in agents if a.status == "completed"]
        assert len(successful) == 0


class TestParallelExecution:
    """測試並行執行特性"""

    @pytest.mark.asyncio
    async def test_concurrent_file_operations(self, mock_task_api, temp_dir):
        """
        測試並行檔案操作不衝突
        """
        from pathlib import Path

        # 建立 4 個 Agent，各自寫入不同檔案
        agents = []
        for i in range(4):
            agent = mock_task_api.create_task(
                description=f"Writer {i}",
                prompt=f"..."
            )
            output_path = temp_dir / f"output_{i}.md"
            agent.write_file(str(output_path), f"Content {i}")
            agents.append(agent)

        # 驗證各自的寫入記錄
        for i, agent in enumerate(agents):
            assert len(agent.written_files) == 1
            assert f"output_{i}.md" in agent.written_files[0]

    @pytest.mark.asyncio
    async def test_independent_completion_order(self, mock_task_api):
        """
        測試 Agent 可以以任意順序完成
        """
        agents = []
        for i in range(4):
            agent = mock_task_api.create_task(
                description=f"Task {i}",
                prompt=f"..."
            )
            agents.append(agent)

        # 以亂序完成
        agents[2].complete("Done 2")
        agents[0].complete("Done 0")
        agents[3].complete("Done 3")
        agents[1].complete("Done 1")

        # 驗證完成順序不影響結果
        for i, agent in enumerate(agents):
            assert agent.status == "completed"
            assert agent.output == f"Done {i}"

    @pytest.mark.asyncio
    async def test_parallel_execution_no_race_condition(self, mock_task_api):
        """
        測試並行執行沒有競爭條件
        """
        # 模擬高並行場景
        num_agents = 10
        agents = []

        for i in range(num_agents):
            agent = mock_task_api.create_task(
                description=f"Concurrent {i}",
                prompt=f"..."
            )
            agent.set_variable("index", i)
            agents.append(agent)

        # 驗證每個 Agent 的狀態獨立
        for i, agent in enumerate(agents):
            assert agent.get_variable("index") == i

        # 並行完成
        for i, agent in enumerate(agents):
            agent.complete(f"Result {i}")

        # 驗證結果正確
        for i, agent in enumerate(agents):
            assert agent.output == f"Result {i}"


class TestMapReducePattern:
    """測試 Map-Reduce 模式"""

    @pytest.mark.asyncio
    async def test_map_phase_parallel(self, mock_task_api):
        """
        測試 Map Phase 並行執行
        """
        # Map: 4 個視角並行分析
        map_agents = []
        for perspective in ["A", "B", "C", "D"]:
            agent = mock_task_api.create_task(
                description=f"Map-{perspective}",
                prompt=f"從視角 {perspective} 分析"
            )
            map_agents.append(agent)

        # 驗證並行
        assert len(map_agents) == 4
        assert all(a.status == "running" for a in map_agents)

    @pytest.mark.asyncio
    async def test_reduce_phase_after_map(self, mock_task_api):
        """
        測試 Reduce Phase 在 Map 完成後執行
        """
        # Map Phase
        map_agents = []
        for i in range(4):
            agent = mock_task_api.create_task(
                description=f"Map-{i}",
                prompt=f"..."
            )
            agent.complete(f"Map result {i}")
            map_agents.append(agent)

        # 收集 Map 結果
        map_results = [a.output for a in map_agents]

        # Reduce Phase
        reduce_agent = mock_task_api.create_task(
            description="Reduce",
            prompt=f"整合以下結果: {map_results}"
        )
        reduce_agent.complete("Combined synthesis")

        # 驗證 Reduce 完成
        assert reduce_agent.status == "completed"
        assert "Combined" in reduce_agent.output

    @pytest.mark.asyncio
    async def test_map_reduce_isolation(self, mock_task_api):
        """
        測試 Map 和 Reduce Agent 之間的隔離
        """
        # Map Agent
        map_agent = mock_task_api.create_task(
            description="Map",
            prompt="..."
        )
        map_agent.set_variable("phase", "map")
        map_agent.complete("Map done")

        # Reduce Agent（新的上下文）
        reduce_agent = mock_task_api.create_task(
            description="Reduce",
            prompt="..."
        )

        # Reduce Agent 無法存取 Map Agent 的變數
        assert reduce_agent.get_variable("phase") is None
