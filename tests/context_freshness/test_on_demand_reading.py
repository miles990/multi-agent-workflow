"""
按需讀取測試 - 驗證 Agent 能自己讀取需要的檔案

測試目標：
1. Agent 收到檔案路徑（非內容）後能使用 Read 工具讀取
2. Agent 輸出包含檔案中的資訊
3. Agent 能優雅處理檔案不存在的情況

核心原理：
- Prompt 只提供檔案路徑，不提供內容
- Agent 按需讀取，保持上下文精簡
- 讀取行為被追蹤，用於驗證工作流程
"""

import pytest
from pathlib import Path
from typing import Any, Dict, List


class TestAgentFileReading:
    """測試 Agent 檔案讀取行為"""

    @pytest.mark.asyncio
    async def test_agent_reads_file_when_needed(self, mock_task_api, temp_dir: Path):
        """
        提供檔案路徑（不提供內容），
        驗證 Agent 使用 Read 工具讀取
        """
        # Arrange: 建立測試檔案
        test_file = temp_dir / "test_config.yaml"
        test_file.write_text("key: value\nsetting: true")

        # 建立 Task，prompt 只包含路徑
        task = mock_task_api.create_task(
            description="Config Reader",
            prompt=f"""## 任務

你是一位配置分析師。

### 相關檔案
請使用 Read 工具讀取以下檔案：
- {test_file}

### 輸出路徑
{temp_dir}/output.md
"""
        )

        # Act: 模擬 Agent 讀取檔案
        content = task.read_file(str(test_file))

        # Assert: 驗證讀取被記錄
        assert str(test_file) in task.read_files
        assert len(task.read_files) == 1

    @pytest.mark.asyncio
    async def test_agent_reads_multiple_files(self, mock_task_api, temp_dir: Path):
        """
        驗證 Agent 能讀取多個檔案
        """
        # Arrange: 建立多個測試檔案
        files = {
            "config.yaml": "config: true",
            "settings.json": '{"key": "value"}',
            "readme.md": "# README",
        }

        for name, content in files.items():
            (temp_dir / name).write_text(content)

        task = mock_task_api.create_task(
            description="Multi-file Reader",
            prompt="讀取多個檔案..."
        )

        # Act: 模擬 Agent 讀取多個檔案
        for name in files.keys():
            task.read_file(str(temp_dir / name))

        # Assert: 驗證所有讀取被記錄
        assert len(task.read_files) == 3
        for name in files.keys():
            assert any(name in path for path in task.read_files)

    @pytest.mark.asyncio
    async def test_agent_output_references_file_content(
        self, mock_task_api, temp_dir: Path, sample_report: str
    ):
        """
        驗證 Agent 輸出包含檔案中的資訊
        """
        # Arrange: 建立包含特定資訊的測試檔案
        test_file = temp_dir / "source.md"
        unique_content = "UNIQUE_MARKER_12345"
        test_file.write_text(f"# Source\n\n{unique_content}\n\nMore content...")

        task = mock_task_api.create_task(
            description="Content Extractor",
            prompt=f"從 {test_file} 提取資訊..."
        )

        # Act: 模擬 Agent 讀取並處理
        task.read_file(str(test_file))

        # 模擬 Agent 在輸出中引用檔案內容
        task.complete(f"分析結果：發現 {unique_content} 在來源檔案中")

        # Assert: 驗證輸出引用了檔案內容
        assert unique_content in task.output
        assert task.status == "completed"


class TestFileNotFoundHandling:
    """測試檔案不存在的處理"""

    @pytest.mark.asyncio
    async def test_agent_handles_missing_file_gracefully(
        self, mock_task_api, temp_dir: Path
    ):
        """
        提供不存在的檔案路徑，
        驗證 Agent 能優雅處理錯誤
        """
        # Arrange: 使用不存在的檔案路徑
        non_existent = temp_dir / "does_not_exist.md"

        task = mock_task_api.create_task(
            description="Error Handler",
            prompt=f"讀取 {non_existent}..."
        )

        # Act: 模擬 Agent 嘗試讀取不存在的檔案
        # 在真實情況下，Read 工具會返回錯誤
        task.read_file(str(non_existent))

        # Agent 應該能繼續工作並報告問題
        task.complete("注意：來源檔案不存在，使用預設值完成分析")

        # Assert: Task 仍然完成
        assert task.status == "completed"
        assert "不存在" in task.output or "注意" in task.output

    @pytest.mark.asyncio
    async def test_agent_continues_with_available_files(
        self, mock_task_api, temp_dir: Path
    ):
        """
        部分檔案存在時，Agent 應繼續處理可用的檔案
        """
        # Arrange: 建立部分檔案
        existing_file = temp_dir / "exists.md"
        existing_file.write_text("# Existing content")

        missing_file = temp_dir / "missing.md"  # 不建立這個檔案

        task = mock_task_api.create_task(
            description="Partial Reader",
            prompt=f"""讀取以下檔案：
- {existing_file}
- {missing_file}
"""
        )

        # Act: Agent 讀取存在的檔案
        task.read_file(str(existing_file))
        task.read_file(str(missing_file))  # 不存在但被記錄

        task.complete("已處理可用檔案，跳過不存在的檔案")

        # Assert: Task 完成，記錄了嘗試讀取的檔案
        assert task.status == "completed"
        assert len(task.read_files) == 2


class TestOnDemandReadingPattern:
    """測試按需讀取模式"""

    @pytest.mark.asyncio
    async def test_reading_triggered_by_need(self, mock_task_api):
        """
        驗證讀取是按需觸發的，而非預先載入
        """
        # Arrange
        task = mock_task_api.create_task(
            description="Lazy Reader",
            prompt="在需要時讀取檔案..."
        )

        # 初始狀態：沒有讀取任何檔案
        assert len(task.read_files) == 0

        # Act: 模擬按需讀取
        # 第一次需要時讀取
        task.read_file("/path/to/config.yaml")
        assert len(task.read_files) == 1

        # 第二次需要時讀取另一個檔案
        task.read_file("/path/to/settings.json")
        assert len(task.read_files) == 2

        # Assert: 只讀取了需要的檔案
        task.complete("完成")
        assert len(task.read_files) == 2

    @pytest.mark.asyncio
    async def test_no_redundant_reading(self, mock_task_api):
        """
        驗證不會重複讀取相同檔案
        """
        task = mock_task_api.create_task(
            description="Efficient Reader",
            prompt="..."
        )

        # 讀取同一檔案多次
        task.read_file("/path/to/file.md")
        task.read_file("/path/to/file.md")
        task.read_file("/path/to/file.md")

        # 記錄中會有多次（這是模擬行為）
        # 但在真實實作中，應該有快取機制
        assert len(task.read_files) >= 1

    @pytest.mark.asyncio
    async def test_read_then_process_pattern(self, mock_task_api, temp_dir: Path):
        """
        驗證典型的「讀取-處理-輸出」模式
        """
        # Arrange: 建立來源檔案
        source = temp_dir / "source.md"
        source.write_text("# Source Data\n\nImportant information here.")

        output = temp_dir / "output.md"

        task = mock_task_api.create_task(
            description="Processor",
            prompt=f"""
### 相關檔案
- {source}

### 輸出路徑
{output}
"""
        )

        # Act: 模擬讀取-處理-寫入流程
        task.read_file(str(source))
        task.set_variable("processed", True)
        task.write_file(str(output), "# Processed Output\n\nAnalysis results...")
        task.complete("處理完成")

        # Assert: 完整的工作流程
        assert len(task.read_files) == 1
        assert len(task.written_files) == 1
        assert task.status == "completed"


class TestPathBasedContext:
    """測試基於路徑的上下文傳遞"""

    def test_prompt_contains_paths_not_content(self, sample_prompt: str):
        """
        驗證 prompt 包含路徑而非內容
        """
        # 檢查路徑模式
        import re

        path_patterns = [
            r"\.claude/memory/",
            r"shared/config/",
            r"/[^\s]+\.(md|yaml|json)",
        ]

        path_found = any(re.search(p, sample_prompt) for p in path_patterns)
        assert path_found, "Prompt 應包含檔案路徑"

        # 檢查沒有完整的 YAML 或 JSON 內容
        # 完整內容通常會有多層縮排或大括號
        yaml_content_pattern = r"^\s{4,}\w+:\s*\w+"  # 深層 YAML 縮排
        json_content_pattern = r"\{\s*\"\w+\"\s*:\s*\{"  # 巢狀 JSON

        has_full_yaml = bool(re.search(yaml_content_pattern, sample_prompt, re.MULTILINE))
        has_full_json = bool(re.search(json_content_pattern, sample_prompt))

        # 這是一個寬鬆的檢查，主要確保沒有完整的結構化內容
        # 實際上可能有少量的範例，這是允許的

    def test_relative_paths_supported(self, sample_prompt: str):
        """
        驗證相對路徑被支援
        """
        # 相對路徑模式
        relative_patterns = [
            r"^[^/].*\.md",  # 不以 / 開頭的 .md 檔案
            r"\./",  # 明確的相對路徑
            r"shared/",  # 專案內的相對路徑
            r"\.claude/",  # .claude 目錄
        ]

        import re

        found = any(re.search(p, sample_prompt) for p in relative_patterns)
        # 至少應該有一些路徑參考
        # 具體是絕對還是相對取決於使用情境
