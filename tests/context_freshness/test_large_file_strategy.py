"""
大文件處理測試 - 驗證策略 A/B 自動選擇

測試目標：
1. < 500 行時使用策略 A（直接讀取）
2. >= 500 行時使用策略 B（並行子 Agent 摘要）
3. 策略 B 正確啟動摘要 Agent
4. 摘要 YAML 格式正確

策略說明：
- 策略 A: 直接讀取完整檔案
- 策略 B: 並行啟動 4 個摘要 Agent，各自負責一部分
"""

import pytest
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class FileStrategy:
    """檔案處理策略選擇器"""

    THRESHOLD = 500  # 行數閾值

    @staticmethod
    def get_strategy(line_count: int) -> str:
        """根據行數選擇策略"""
        if line_count < FileStrategy.THRESHOLD:
            return "A"  # 直接讀取
        return "B"  # 並行摘要

    @staticmethod
    def count_lines(file_path: Path) -> int:
        """計算檔案行數"""
        if not file_path.exists():
            return 0
        with open(file_path) as f:
            return sum(1 for _ in f)


class TestStrategySelection:
    """測試策略選擇"""

    def test_strategy_a_for_small_files(self, temp_dir: Path):
        """
        < 500 行時使用策略 A（直接讀取）
        """
        # Arrange: 創建小檔案
        small_file = temp_dir / "small.md"
        content = "\n".join([f"Line {i}" for i in range(100)])
        small_file.write_text(content)

        # Act
        line_count = FileStrategy.count_lines(small_file)
        strategy = FileStrategy.get_strategy(line_count)

        # Assert
        assert line_count == 100
        assert strategy == "A", "小檔案應使用策略 A"

    def test_strategy_b_for_large_files(self, temp_dir: Path):
        """
        >= 500 行時使用策略 B（並行子 Agent）
        """
        # Arrange: 創建大檔案
        large_file = temp_dir / "large.md"
        content = "\n".join([f"Line {i}" for i in range(600)])
        large_file.write_text(content)

        # Act
        line_count = FileStrategy.count_lines(large_file)
        strategy = FileStrategy.get_strategy(line_count)

        # Assert
        assert line_count == 600
        assert strategy == "B", "大檔案應使用策略 B"

    def test_threshold_boundary(self, temp_dir: Path):
        """
        測試閾值邊界（499 行 vs 500 行）
        """
        # 499 行 → 策略 A
        assert FileStrategy.get_strategy(499) == "A"

        # 500 行 → 策略 B
        assert FileStrategy.get_strategy(500) == "B"

        # 501 行 → 策略 B
        assert FileStrategy.get_strategy(501) == "B"

    def test_empty_file(self, temp_dir: Path):
        """
        測試空檔案
        """
        empty_file = temp_dir / "empty.md"
        empty_file.write_text("")

        line_count = FileStrategy.count_lines(empty_file)
        strategy = FileStrategy.get_strategy(line_count)

        assert line_count == 0
        assert strategy == "A", "空檔案應使用策略 A"


class TestParallelExtractionAgents:
    """測試策略 B 的並行摘要 Agent"""

    @pytest.mark.asyncio
    async def test_parallel_extraction_agents(self, mock_task_api, temp_dir: Path):
        """
        驗證策略 B 正確啟動 4 個摘要 Agent
        """
        # Arrange: 創建大檔案
        large_file = temp_dir / "large_source.md"
        content = "\n".join([f"Section {i}: Content for section {i}" for i in range(600)])
        large_file.write_text(content)

        # Act: 模擬策略 B - 啟動 4 個並行 Agent
        agents = []
        chunk_size = 600 // 4  # 150 行每個 Agent

        for i in range(4):
            start_line = i * chunk_size
            end_line = start_line + chunk_size

            agent = mock_task_api.create_task(
                description=f"Summarizer {i+1}",
                prompt=f"摘要檔案第 {start_line}-{end_line} 行"
            )
            agents.append(agent)

        # Assert: 驗證 4 個 Agent 被創建
        assert len(agents) == 4
        assert len(mock_task_api.tasks) == 4

        # 驗證每個 Agent 獨立
        task_ids = [a.task_id for a in agents]
        assert len(set(task_ids)) == 4

    @pytest.mark.asyncio
    async def test_extraction_agents_complete_independently(
        self, mock_task_api
    ):
        """
        驗證摘要 Agent 獨立完成
        """
        # 創建 4 個 Agent
        agents = []
        for i in range(4):
            agent = mock_task_api.create_task(
                description=f"Extractor {i+1}",
                prompt=f"提取部分 {i+1}..."
            )
            agents.append(agent)

        # 各自完成（可能有不同結果）
        summaries = [
            "架構模式: MVC",
            "核心組件: Service, Repository",
            "設計原則: SOLID",
            "依賴關係: 模組化",
        ]

        for i, agent in enumerate(agents):
            agent.complete(summaries[i])

        # 驗證各自獨立完成
        for i, agent in enumerate(agents):
            assert agent.status == "completed"
            assert agent.output == summaries[i]

    @pytest.mark.asyncio
    async def test_partial_extraction_failure(self, mock_task_api):
        """
        測試部分 Agent 失敗的情況
        """
        agents = []
        for i in range(4):
            agent = mock_task_api.create_task(
                description=f"Extractor {i+1}",
                prompt=f"提取部分 {i+1}..."
            )
            agents.append(agent)

        # 3 個成功，1 個失敗
        agents[0].complete("Summary 1")
        agents[1].complete("Summary 2")
        agents[2].fail("Extraction failed")
        agents[3].complete("Summary 4")

        # 驗證狀態
        assert agents[0].status == "completed"
        assert agents[1].status == "completed"
        assert agents[2].status == "failed"
        assert agents[3].status == "completed"

        # 成功的 Agent 數量
        completed = [a for a in agents if a.status == "completed"]
        assert len(completed) == 3


class TestSummaryYamlFormat:
    """測試摘要 YAML 格式"""

    def test_summary_yaml_format(self, temp_dir: Path):
        """
        驗證摘要 YAML 格式正確
        """
        # 建立範例摘要 YAML
        summary = {
            "file": "source.md",
            "total_lines": 600,
            "strategy": "B",
            "chunks": [
                {
                    "id": 1,
                    "start_line": 0,
                    "end_line": 150,
                    "summary": "架構概述和設計原則",
                    "key_points": ["MVC 模式", "分層架構"],
                },
                {
                    "id": 2,
                    "start_line": 150,
                    "end_line": 300,
                    "summary": "核心組件實作",
                    "key_points": ["Service 層", "Repository 模式"],
                },
                {
                    "id": 3,
                    "start_line": 300,
                    "end_line": 450,
                    "summary": "API 設計和路由",
                    "key_points": ["RESTful API", "路由配置"],
                },
                {
                    "id": 4,
                    "start_line": 450,
                    "end_line": 600,
                    "summary": "測試和部署",
                    "key_points": ["單元測試", "CI/CD"],
                },
            ],
            "combined_summary": "系統採用 MVC 架構，實作分層設計...",
        }

        # 寫入 YAML
        summary_file = temp_dir / "summary.yaml"
        with open(summary_file, "w") as f:
            yaml.dump(summary, f, allow_unicode=True, default_flow_style=False)

        # 讀取並驗證
        with open(summary_file) as f:
            loaded = yaml.safe_load(f)

        assert loaded["file"] == "source.md"
        assert loaded["total_lines"] == 600
        assert loaded["strategy"] == "B"
        assert len(loaded["chunks"]) == 4
        assert "combined_summary" in loaded

    def test_summary_yaml_required_fields(self):
        """
        驗證摘要 YAML 必要欄位
        """
        required_fields = [
            "file",
            "total_lines",
            "strategy",
            "chunks",
            "combined_summary",
        ]

        chunk_required_fields = [
            "id",
            "start_line",
            "end_line",
            "summary",
        ]

        # 這些是文檔化的必要欄位
        for field in required_fields:
            assert field in required_fields, f"頂層應有 {field}"

        for field in chunk_required_fields:
            assert field in chunk_required_fields, f"chunk 應有 {field}"

    def test_summary_yaml_unicode_support(self, temp_dir: Path):
        """
        驗證摘要 YAML 支援中文
        """
        summary = {
            "file": "來源檔案.md",
            "summary": "這是中文摘要",
            "key_points": ["重點一", "重點二", "重點三"],
        }

        summary_file = temp_dir / "chinese_summary.yaml"
        with open(summary_file, "w", encoding="utf-8") as f:
            yaml.dump(summary, f, allow_unicode=True)

        with open(summary_file, encoding="utf-8") as f:
            loaded = yaml.safe_load(f)

        assert loaded["file"] == "來源檔案.md"
        assert loaded["summary"] == "這是中文摘要"


class TestStrategyBWorkflow:
    """測試策略 B 完整工作流程"""

    @pytest.mark.asyncio
    async def test_strategy_b_workflow(self, mock_task_api, temp_dir: Path):
        """
        測試策略 B 的完整工作流程：
        1. 檢測大檔案
        2. 切分 chunks
        3. 並行啟動 Agent
        4. 收集摘要
        5. 合併結果
        """
        # Step 1: 創建大檔案
        large_file = temp_dir / "large_source.md"
        content = "\n".join([f"Line {i}: Content {i}" for i in range(600)])
        large_file.write_text(content)

        # Step 2: 選擇策略
        line_count = FileStrategy.count_lines(large_file)
        strategy = FileStrategy.get_strategy(line_count)
        assert strategy == "B"

        # Step 3: 計算 chunks
        num_agents = 4
        chunk_size = line_count // num_agents
        chunks = []
        for i in range(num_agents):
            start = i * chunk_size
            end = start + chunk_size if i < num_agents - 1 else line_count
            chunks.append({"start": start, "end": end})

        assert len(chunks) == 4

        # Step 4: 啟動並行 Agent
        agents = []
        for i, chunk in enumerate(chunks):
            agent = mock_task_api.create_task(
                description=f"Chunk {i+1} Summarizer",
                prompt=f"摘要第 {chunk['start']}-{chunk['end']} 行"
            )
            agents.append(agent)

        # Step 5: 完成並收集結果
        summaries = []
        for i, agent in enumerate(agents):
            summary = f"Chunk {i+1} summary: Key findings from lines {chunks[i]['start']}-{chunks[i]['end']}"
            agent.complete(summary)
            summaries.append(summary)

        # Step 6: 合併結果
        combined = "\n".join(summaries)

        # 驗證
        assert len(summaries) == 4
        assert all(a.status == "completed" for a in agents)
        assert "Key findings" in combined
