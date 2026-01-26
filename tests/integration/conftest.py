"""
Integration Tests - Shared Fixtures
整合測試共用 fixtures

從 context_freshness/conftest.py 導入共用的 fixtures
"""

import pytest
import sys
from pathlib import Path

# 導入 context_freshness 的 fixtures
sys.path.insert(0, str(Path(__file__).parent.parent / "context_freshness"))
from conftest import (
    # 路徑 Fixtures
    project_root,
    config_dir,
    tools_dir,
    hooks_dir,
    # 臨時目錄 Fixtures
    temp_dir,
    temp_memory_dir,
    temp_workflow_dir,
    # 配置 Fixtures
    context_freshness_config,
    execution_profiles_config,
    quality_gates_config,
    # Mock Task API
    MockTaskAPI,
    MockTaskContext,
    mock_task_api,
    # 驗證器
    PromptValidator,
    prompt_validator,
    ReportValidator,
    report_validator,
    # Hook 追蹤
    MockHookTracker,
    hook_tracker,
    # Sample Data
    sample_prompt,
    sample_report,
    sample_tasks_yaml,
    sample_action_log,
)
