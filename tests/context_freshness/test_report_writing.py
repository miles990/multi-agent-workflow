"""
報告寫入測試 - 驗證強制寫入機制

測試目標：
1. 視角報告被正確創建
2. 報告滿足最小長度要求
3. 報告包含必要 section
4. verify-perspectives.sh 驗證邏輯正確

配置參考：
- perspectives/ 目錄結構
- 最少 50 行
- 必要 section: 核心發現、詳細分析
"""

import subprocess
import pytest
from pathlib import Path
from typing import Any, Dict, List


def create_test_report(path: Path, content: str = None, lines: int = 60) -> None:
    """建立測試報告檔案"""
    path.parent.mkdir(parents=True, exist_ok=True)
    if content:
        path.write_text(content)
    else:
        default_lines = [
            "# 測試報告",
            "",
            "## 核心發現",
            "",
            "這是測試核心發現內容。",
            "",
            "## 詳細分析",
            "",
            "這是測試詳細分析內容。",
            "",
        ]
        # 計算需要的填充行數
        padding_count = max(0, lines - len(default_lines))
        padding_lines = [f"# 填充行 {i}" for i in range(padding_count)]
        all_lines = default_lines + padding_lines
        path.write_text("\n".join(all_lines))


class TestPerspectiveReportCreation:
    """測試視角報告創建"""

    @pytest.mark.asyncio
    async def test_perspective_report_created(
        self, mock_task_api, temp_memory_dir: Path, sample_report: str
    ):
        """
        執行 research，驗證視角報告被創建
        """
        # Arrange: 設定記憶體目錄結構
        research_id = "test-research-001"
        perspectives_dir = temp_memory_dir / "research" / research_id / "perspectives"

        task = mock_task_api.create_task(
            description="Architecture Perspective",
            prompt=f"寫入報告到 {perspectives_dir}/architecture.md"
        )

        # Act: 模擬 Agent 寫入報告
        report_path = perspectives_dir / "architecture.md"
        create_test_report(report_path, sample_report)
        task.write_file(str(report_path), sample_report)
        task.complete("報告已寫入")

        # Assert: 驗證報告存在
        assert perspectives_dir.exists()
        assert report_path.exists()
        assert len(task.written_files) == 1

    @pytest.mark.asyncio
    async def test_multiple_perspectives_created(
        self, mock_task_api, temp_memory_dir: Path, sample_report: str
    ):
        """
        驗證多個視角報告被創建
        """
        # Arrange
        research_id = "test-research-002"
        perspectives_dir = temp_memory_dir / "research" / research_id / "perspectives"
        perspectives_dir.mkdir(parents=True)

        perspectives = ["architecture", "cognitive", "workflow", "industry"]

        # Act: 為每個視角創建報告
        for perspective in perspectives:
            report_path = perspectives_dir / f"{perspective}.md"
            create_test_report(report_path, sample_report)

        # Assert: 驗證所有報告存在
        reports = list(perspectives_dir.glob("*.md"))
        assert len(reports) == 4
        assert all(r.exists() for r in reports)


class TestReportLength:
    """測試報告長度要求"""

    def test_report_meets_minimum_length(
        self, report_validator, temp_memory_dir: Path, sample_report: str
    ):
        """
        驗證報告 > 50 行
        """
        # Arrange: 創建符合長度的報告
        report_path = temp_memory_dir / "research" / "test" / "perspectives" / "test.md"
        create_test_report(report_path, sample_report, lines=60)

        # Assert
        result = report_validator.validate_min_length(report_path)
        assert result is True

    def test_short_report_detected(self, report_validator, temp_memory_dir: Path):
        """
        驗證能偵測過短的報告
        """
        # Arrange: 創建過短的報告
        report_path = temp_memory_dir / "research" / "test" / "perspectives" / "short.md"
        create_test_report(report_path, "# Short Report\n\nToo short.", lines=10)

        # Assert
        result = report_validator.validate_min_length(report_path)
        assert result is False

    def test_exact_minimum_length(self, report_validator, temp_memory_dir: Path):
        """
        驗證剛好 50 行的報告通過
        """
        report_path = temp_memory_dir / "research" / "test" / "perspectives" / "exact.md"
        create_test_report(report_path, lines=50)

        result = report_validator.validate_min_length(report_path, min_lines=50)
        assert result is True


class TestRequiredSections:
    """測試必要 section"""

    def test_report_contains_required_sections(
        self, report_validator, temp_memory_dir: Path, sample_report: str
    ):
        """
        驗證報告包含「核心發現」等必要 section
        """
        # Arrange
        report_path = temp_memory_dir / "research" / "test" / "perspectives" / "full.md"
        create_test_report(report_path, sample_report)

        # Assert
        missing = report_validator.validate_sections(report_path)
        assert len(missing) == 0, f"缺少必要 section: {missing}"

    def test_missing_sections_detected(
        self, report_validator, temp_memory_dir: Path
    ):
        """
        驗證能偵測缺少的 section
        """
        # Arrange: 創建缺少 section 的報告（使用不包含關鍵詞的內容）
        incomplete_report = """# 報告

這是一份不完整的報告。

## 其他內容

一些其他內容...
"""
        report_path = temp_memory_dir / "research" / "test" / "perspectives" / "incomplete.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(incomplete_report)

        # Assert
        missing = report_validator.validate_sections(report_path)
        assert len(missing) > 0, "應偵測到缺少的 section"

    def test_english_sections_accepted(
        self, report_validator, temp_memory_dir: Path
    ):
        """
        驗證英文 section 名稱也被接受
        """
        english_report = """# Report

## Core Findings

This is the core findings section.

## Detailed Analysis

This is the detailed analysis section.
"""
        report_path = temp_memory_dir / "research" / "test" / "perspectives" / "english.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(english_report)

        missing = report_validator.validate_sections(report_path)
        assert len(missing) == 0, f"英文 section 應被接受，但缺少: {missing}"


class TestVerifyPerspectivesScript:
    """測試 verify-perspectives.sh 驗證腳本"""

    def test_verify_script_exists(self, tools_dir: Path):
        """
        驗證 verify-perspectives.sh 存在
        """
        script = tools_dir / "verify-perspectives.sh"
        assert script.exists(), "verify-perspectives.sh 應存在"

    def test_verify_script_is_executable(self, tools_dir: Path):
        """
        驗證腳本可執行
        """
        script = tools_dir / "verify-perspectives.sh"
        if script.exists():
            # 檢查是否有執行權限
            import os
            assert os.access(script, os.X_OK), "腳本應有執行權限"

    def test_verify_script_with_valid_reports(
        self, tools_dir: Path, temp_dir: Path, sample_report: str
    ):
        """
        測試腳本對有效報告的驗證
        """
        script = tools_dir / "verify-perspectives.sh"
        if not script.exists():
            pytest.skip("verify-perspectives.sh 不存在")

        # Arrange: 創建有效的報告結構
        research_id = "valid-test"
        perspectives_dir = temp_dir / ".claude" / "memory" / "research" / research_id / "perspectives"
        perspectives_dir.mkdir(parents=True)

        for p in ["architecture", "cognitive", "workflow", "industry"]:
            create_test_report(perspectives_dir / f"{p}.md", sample_report)

        # Act: 執行驗證腳本
        result = subprocess.run(
            [str(script), "research", research_id, "4"],
            cwd=temp_dir,
            capture_output=True,
            text=True,
        )

        # Assert: 應該通過（exit code 0）
        assert result.returncode == 0, f"驗證應通過: {result.stderr}"

    def test_verify_script_with_missing_reports(
        self, tools_dir: Path, temp_dir: Path
    ):
        """
        測試腳本對缺少報告的處理
        """
        script = tools_dir / "verify-perspectives.sh"
        if not script.exists():
            pytest.skip("verify-perspectives.sh 不存在")

        # Arrange: 創建不完整的報告結構（只有 2 個報告，期望 4 個）
        research_id = "incomplete-test"
        perspectives_dir = temp_dir / ".claude" / "memory" / "research" / research_id / "perspectives"
        perspectives_dir.mkdir(parents=True)

        for p in ["architecture", "cognitive"]:  # 只有 2 個
            create_test_report(perspectives_dir / f"{p}.md", lines=60)

        # Act
        result = subprocess.run(
            [str(script), "research", research_id, "4"],  # 期望 4 個
            cwd=temp_dir,
            capture_output=True,
            text=True,
        )

        # Assert: 應該失敗（exit code 1）
        assert result.returncode == 1, "缺少報告應導致驗證失敗"


class TestReportWritingWorkflow:
    """測試報告寫入工作流程"""

    @pytest.mark.asyncio
    async def test_agent_writes_to_correct_path(
        self, mock_task_api, temp_memory_dir: Path
    ):
        """
        驗證 Agent 寫入到正確的路徑
        """
        # Arrange
        expected_path = temp_memory_dir / "research" / "test-001" / "perspectives" / "architecture.md"

        task = mock_task_api.create_task(
            description="Writer",
            prompt=f"### 輸出路徑\n{expected_path}"
        )

        # Act
        task.write_file(str(expected_path), "# Report content")

        # Assert
        assert str(expected_path) in task.written_files

    @pytest.mark.asyncio
    async def test_write_before_complete(self, mock_task_api, temp_memory_dir: Path):
        """
        驗證 Agent 在完成前寫入報告
        """
        task = mock_task_api.create_task(
            description="Ordered Writer",
            prompt="..."
        )

        # 正確順序：先寫入，後完成
        report_path = temp_memory_dir / "report.md"
        task.write_file(str(report_path), "Content")

        assert len(task.written_files) == 1
        assert task.status == "running"  # 還沒完成

        task.complete("Done")

        assert task.status == "completed"
        assert len(task.written_files) == 1  # 仍然是 1

    @pytest.mark.asyncio
    async def test_directory_created_before_write(
        self, mock_task_api, temp_memory_dir: Path
    ):
        """
        驗證目錄在寫入前被創建
        """
        # Arrange: 使用 create_test_report 輔助函數
        nested_path = temp_memory_dir / "deep" / "nested" / "path" / "report.md"

        # Act: create_test_report 會自動創建父目錄
        create_test_report(nested_path, "# Content")

        # Assert
        assert nested_path.parent.exists()
        assert nested_path.exists()
