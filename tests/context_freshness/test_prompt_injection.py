"""
Prompt 注入測試 - 驗證 Prompt 結構正確傳遞必要資訊

測試目標：
1. Prompt 包含所有必要欄位
2. Prompt 不包含完整檔案內容
3. 相關檔案僅以路徑形式提供
4. Prompt 結構符合 context-freshness.yaml 配置

配置參考：
- prompt_structure.required: 必須包含的欄位
- prompt_structure.never_include: 絕不包含的項目
"""

import re
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml


class TestRequiredFields:
    """測試 Prompt 必要欄位"""

    def test_prompt_contains_required_fields(
        self, sample_prompt: str, prompt_validator
    ):
        """
        驗證 prompt 包含必要欄位：
        - role_description
        - task_objective
        - focus_areas
        - output_requirements
        - output_path
        """
        missing = prompt_validator.validate_required_fields(sample_prompt)

        assert len(missing) == 0, f"缺少必要欄位: {missing}"

    def test_prompt_missing_fields_detected(self, prompt_validator):
        """
        驗證能正確偵測缺少的欄位
        """
        # 一個不完整的 prompt
        incomplete_prompt = """## 任務

你是一位分析師。

### 目標
分析系統。
"""

        missing = prompt_validator.validate_required_fields(incomplete_prompt)

        # 應該缺少 focus_areas, output_requirements, output_path
        assert "focus_areas" in missing or len(missing) > 0

    def test_prompt_with_chinese_field_names(self, prompt_validator):
        """
        驗證中文欄位名也能被識別
        """
        prompt = """## 任務

你是一位架構分析師。

### 目標
分析系統架構。

### 聚焦領域
- 系統結構
- 設計模式

### 輸出要求
- 詳細報告

### 輸出路徑
.claude/memory/research/test/report.md
"""
        missing = prompt_validator.validate_required_fields(prompt)
        assert len(missing) == 0, f"中文欄位應被識別，但缺少: {missing}"


class TestExcludedContent:
    """測試 Prompt 不包含禁止內容"""

    def test_prompt_excludes_full_file_contents(
        self, sample_prompt: str, prompt_validator
    ):
        """
        驗證 prompt 不包含完整檔案內容
        """
        result = prompt_validator.check_no_full_file_contents(sample_prompt)
        assert result is True, "Prompt 不應包含超過 100 行的程式碼區塊"

    def test_prompt_with_large_code_block_detected(self, prompt_validator):
        """
        驗證能偵測包含大量程式碼的 prompt
        """
        # 建立一個包含大量程式碼的 prompt
        large_code = "\n".join([f"line {i}" for i in range(150)])
        bad_prompt = f"""## 任務

這是任務描述。

### 完整原始碼
```python
{large_code}
```
"""

        result = prompt_validator.check_no_full_file_contents(bad_prompt)
        assert result is False, "應偵測到超過 100 行的程式碼區塊"

    def test_prompt_excludes_conversation_history(self, sample_prompt: str):
        """
        驗證 prompt 不包含對話歷史
        """
        # 檢查沒有典型的對話歷史標記
        conversation_markers = [
            "Human:",
            "Assistant:",
            "User:",
            "Claude:",
            "[Previous conversation]",
            "對話歷史",
        ]

        for marker in conversation_markers:
            assert marker not in sample_prompt, f"不應包含對話歷史標記: {marker}"

    def test_prompt_excludes_detailed_analysis(self, sample_prompt: str):
        """
        驗證 prompt 不包含完整的詳細分析（應該讓 Agent 自己讀取）
        """
        # 檢查沒有完整的分析報告
        # 如果包含完整報告，通常會有很多 markdown 標題
        h2_count = sample_prompt.count("\n## ")
        h3_count = sample_prompt.count("\n### ")

        # 標準 prompt 不應該有太多 section
        assert h2_count <= 2, "Prompt 有太多 ## 標題，可能包含完整報告"
        assert h3_count <= 10, "Prompt 有太多 ### 標題，可能包含詳細分析"


class TestFilePathsOnly:
    """測試檔案以路徑形式提供"""

    def test_prompt_includes_file_paths_only(
        self, sample_prompt: str, prompt_validator
    ):
        """
        驗證相關檔案以路徑形式提供，而非完整內容
        """
        result = prompt_validator.check_file_paths_only(sample_prompt)
        assert result is True, "相關檔案應以路徑形式提供"

    def test_prompt_contains_path_patterns(self, sample_prompt: str):
        """
        驗證 prompt 包含檔案路徑
        """
        path_patterns = [
            r"\.claude/",
            r"shared/",
            r"/[^\s]+\.md",
            r"/[^\s]+\.yaml",
        ]

        found_paths = []
        for pattern in path_patterns:
            if re.search(pattern, sample_prompt):
                found_paths.append(pattern)

        assert len(found_paths) > 0, "Prompt 應包含檔案路徑"

    def test_prompt_uses_read_instruction(self, sample_prompt: str):
        """
        驗證 prompt 包含「使用 Read 工具讀取」的指示
        """
        read_instructions = [
            "Read 工具",
            "Read tool",
            "讀取",
            "read",
        ]

        found = any(inst.lower() in sample_prompt.lower() for inst in read_instructions)
        assert found, "Prompt 應包含讀取檔案的指示"


class TestPromptStructure:
    """測試 Prompt 結構符合配置"""

    def test_prompt_structure_matches_config(
        self, context_freshness_config: Dict[str, Any]
    ):
        """
        驗證 prompt 結構符合 context-freshness.yaml 配置
        """
        prompt_structure = context_freshness_config.get("prompt_structure", {})

        # 驗證配置存在
        assert "required" in prompt_structure, "配置應有 required 欄位"
        assert "never_include" in prompt_structure, "配置應有 never_include 欄位"
        assert "optional" in prompt_structure, "配置應有 optional 欄位"

        # 驗證必要欄位
        required = prompt_structure["required"]
        expected_required = [
            "role_description",
            "task_objective",
            "focus_areas",
            "output_requirements",
            "output_path",
        ]
        for field in expected_required:
            assert field in required, f"required 應包含 {field}"

        # 驗證禁止項目
        never_include = prompt_structure["never_include"]
        expected_never = [
            "full_file_contents",
            "previous_reports",
            "conversation_history",
            "detailed_analysis",
        ]
        for item in expected_never:
            assert item in never_include, f"never_include 應包含 {item}"

    def test_prompt_template_exists(self, context_freshness_config: Dict[str, Any]):
        """
        驗證配置中有 prompt_template
        """
        template = context_freshness_config.get("prompt_template", "")
        assert len(template) > 0, "配置應有 prompt_template"

        # 驗證 template 包含佔位符
        placeholders = [
            "{role_description}",
            "{task_objective}",
            "{focus_areas}",
            "{output_requirements}",
            "{output_path}",
        ]
        for placeholder in placeholders:
            assert placeholder in template, f"Template 應包含 {placeholder}"

    def test_validation_method_is_task_completion(
        self, context_freshness_config: Dict[str, Any]
    ):
        """
        驗證驗證方式是 task_completion
        """
        validation = context_freshness_config.get("validation", {})
        method = validation.get("method", "")

        assert method == "task_completion", "驗證方式應為 task_completion"

    def test_quality_curve_defined(self, context_freshness_config: Dict[str, Any]):
        """
        驗證品質曲線定義存在
        """
        quality_curve = context_freshness_config.get("quality_curve", {})

        expected_ranges = ["0-30%", "30-50%", "50-70%", "70%+"]
        for range_key in expected_ranges:
            assert range_key in quality_curve, f"quality_curve 應包含 {range_key}"


class TestPromptGeneration:
    """測試 Prompt 生成邏輯"""

    def test_generate_prompt_from_template(
        self, context_freshness_config: Dict[str, Any]
    ):
        """
        測試從 template 生成 prompt
        """
        template = context_freshness_config.get("prompt_template", "")

        # 填充 template
        prompt = template.format(
            role_description="架構分析師",
            task_objective="分析系統架構，識別核心組件",
            focus_areas="- 系統結構\n- 設計模式",
            previous_stage_summary="這是一個多代理工作流系統。",
            relevant_file_paths="- shared/config/context-freshness.yaml",
            output_requirements="- 詳細的架構分析報告",
            output_path=".claude/memory/research/test/perspectives/architecture.md",
        )

        # 驗證生成的 prompt
        assert "架構分析師" in prompt
        assert "分析系統架構" in prompt
        assert "系統結構" in prompt
        assert ".claude/memory" in prompt

    def test_prompt_size_reasonable(self, sample_prompt: str):
        """
        驗證 prompt 大小合理（不會過大）
        """
        # 一個合理的 prompt 應該在 500-3000 字元之間
        prompt_len = len(sample_prompt)

        assert prompt_len >= 100, "Prompt 太短，可能缺少必要資訊"
        assert prompt_len <= 10000, "Prompt 太長，可能包含了不該包含的內容"

    def test_prompt_line_count_reasonable(self, sample_prompt: str):
        """
        驗證 prompt 行數合理
        """
        lines = sample_prompt.split("\n")

        assert len(lines) >= 10, "Prompt 行數太少"
        assert len(lines) <= 200, "Prompt 行數太多，可能包含完整檔案內容"
