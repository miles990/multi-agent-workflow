"""
Context Freshness Tests - Shared Fixtures
上下文新鮮機制測試共用 fixtures

提供：
- 測試環境初始化
- Mock 工具（Task API, Hooks）
- 驗證器
- 清理邏輯
"""

import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional
from unittest.mock import MagicMock, patch

import pytest
import yaml


# ===========================================================================
# 路徑 Fixtures
# ===========================================================================


@pytest.fixture
def project_root() -> Path:
    """取得專案根目錄"""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def config_dir(project_root: Path) -> Path:
    """取得配置目錄"""
    return project_root / "shared" / "config"


@pytest.fixture
def tools_dir(project_root: Path) -> Path:
    """取得工具目錄"""
    return project_root / "shared" / "tools"


@pytest.fixture
def hooks_dir(project_root: Path) -> Path:
    """取得 hooks 目錄"""
    return project_root / "scripts" / "hooks"


# ===========================================================================
# 臨時目錄 Fixtures
# ===========================================================================


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """建立並清理臨時目錄"""
    tmp = Path(tempfile.mkdtemp(prefix="cf_test_"))
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def temp_memory_dir(temp_dir: Path) -> Path:
    """建立臨時 memory 目錄結構"""
    memory_dir = temp_dir / ".claude" / "memory"
    memory_dir.mkdir(parents=True)
    return memory_dir


@pytest.fixture
def temp_workflow_dir(temp_dir: Path) -> Path:
    """建立臨時 workflow 目錄結構"""
    workflow_dir = temp_dir / ".claude" / "workflow"
    workflow_dir.mkdir(parents=True)
    return workflow_dir


# ===========================================================================
# 配置 Fixtures
# ===========================================================================


@pytest.fixture
def context_freshness_config(config_dir: Path) -> Dict[str, Any]:
    """載入 context-freshness.yaml 配置"""
    config_file = config_dir / "context-freshness.yaml"
    if config_file.exists():
        with open(config_file) as f:
            return yaml.safe_load(f)
    return {}


@pytest.fixture
def execution_profiles_config(config_dir: Path) -> Dict[str, Any]:
    """載入 execution-profiles.yaml 配置"""
    config_file = config_dir / "execution-profiles.yaml"
    if config_file.exists():
        with open(config_file) as f:
            return yaml.safe_load(f)
    return {}


@pytest.fixture
def quality_gates_config(project_root: Path) -> Dict[str, Any]:
    """載入 gates.yaml 配置"""
    config_file = project_root / "shared" / "quality" / "gates.yaml"
    if config_file.exists():
        with open(config_file) as f:
            return yaml.safe_load(f)
    return {}


# ===========================================================================
# Mock Task API Fixtures
# ===========================================================================


class MockTaskContext:
    """模擬 Task 的獨立上下文"""

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.variables: Dict[str, Any] = {}
        self.read_files: List[str] = []
        self.written_files: List[str] = []
        self.output: Optional[str] = None
        self.start_time = datetime.utcnow()
        self.end_time: Optional[datetime] = None
        self.status = "pending"

    def set_variable(self, key: str, value: Any) -> None:
        """設定上下文變數"""
        self.variables[key] = value

    def get_variable(self, key: str, default: Any = None) -> Any:
        """取得上下文變數"""
        return self.variables.get(key, default)

    def read_file(self, path: str) -> str:
        """記錄檔案讀取"""
        self.read_files.append(path)
        return f"[mock content of {path}]"

    def write_file(self, path: str, content: str) -> None:
        """記錄檔案寫入"""
        self.written_files.append(path)

    def complete(self, output: str) -> None:
        """完成 Task"""
        self.output = output
        self.end_time = datetime.utcnow()
        self.status = "completed"

    def fail(self, error: str) -> None:
        """Task 失敗"""
        self.output = f"Error: {error}"
        self.end_time = datetime.utcnow()
        self.status = "failed"


class MockTaskAPI:
    """模擬 Claude Code Task API"""

    def __init__(self):
        self.tasks: Dict[str, MockTaskContext] = {}
        self._task_counter = 0

    def create_task(self, description: str, prompt: str) -> MockTaskContext:
        """建立新 Task（獨立上下文）"""
        self._task_counter += 1
        task_id = f"task_{self._task_counter}"
        task = MockTaskContext(task_id)
        task.status = "running"
        self.tasks[task_id] = task
        return task

    def get_task(self, task_id: str) -> Optional[MockTaskContext]:
        """取得 Task"""
        return self.tasks.get(task_id)

    def list_tasks(self) -> List[MockTaskContext]:
        """列出所有 Tasks"""
        return list(self.tasks.values())

    def clear(self) -> None:
        """清除所有 Tasks"""
        self.tasks.clear()
        self._task_counter = 0


@pytest.fixture
def mock_task_api() -> Generator[MockTaskAPI, None, None]:
    """提供 Mock Task API"""
    api = MockTaskAPI()
    yield api
    api.clear()


# ===========================================================================
# Prompt 驗證 Fixtures
# ===========================================================================


class PromptValidator:
    """Prompt 結構驗證器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.required_fields = config.get("prompt_structure", {}).get("required", [])
        self.never_include = config.get("prompt_structure", {}).get("never_include", [])

    def validate_required_fields(self, prompt: str) -> List[str]:
        """檢查必要欄位，回傳缺失的欄位"""
        missing = []
        field_patterns = {
            "role_description": ["你是一位", "你是", "role:", "角色"],
            "task_objective": ["目標", "objective", "任務"],
            "focus_areas": ["聚焦", "focus", "專注"],
            "output_requirements": ["輸出要求", "output", "產出"],
            "output_path": ["輸出路徑", "output_path", "寫入"],
        }

        for field in self.required_fields:
            patterns = field_patterns.get(field, [field])
            found = any(p.lower() in prompt.lower() for p in patterns)
            if not found:
                missing.append(field)

        return missing

    def check_no_full_file_contents(self, prompt: str) -> bool:
        """檢查是否包含完整檔案內容（> 100 行）"""
        lines = prompt.split("\n")
        code_block_lines = 0
        in_code_block = False

        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
            elif in_code_block:
                code_block_lines += 1

        # 如果代碼塊超過 100 行，視為包含完整檔案內容
        return code_block_lines < 100

    def check_file_paths_only(self, prompt: str) -> bool:
        """檢查相關檔案是否僅以路徑形式提供"""
        # 搜尋路徑模式
        path_patterns = [
            r"\.claude/",
            r"shared/",
            r"skills/",
            r"/.*\.md",
            r"/.*\.yaml",
        ]

        import re

        has_paths = any(re.search(p, prompt) for p in path_patterns)

        # 檢查沒有內嵌大量內容
        no_full_contents = self.check_no_full_file_contents(prompt)

        return has_paths and no_full_contents


@pytest.fixture
def prompt_validator(context_freshness_config: Dict[str, Any]) -> PromptValidator:
    """提供 Prompt 驗證器"""
    return PromptValidator(context_freshness_config)


# ===========================================================================
# Report 驗證 Fixtures
# ===========================================================================


class ReportValidator:
    """報告驗證器"""

    REQUIRED_SECTIONS = ["核心發現", "詳細分析", "Core Findings", "Detailed Analysis"]
    MIN_LINES = 50

    def validate_exists(self, path: Path) -> bool:
        """檢查報告是否存在"""
        return path.exists() and path.is_file()

    def validate_min_length(self, path: Path, min_lines: int = None) -> bool:
        """檢查報告長度"""
        if not self.validate_exists(path):
            return False

        min_lines = min_lines or self.MIN_LINES
        with open(path) as f:
            lines = f.readlines()

        return len(lines) >= min_lines

    def validate_sections(self, path: Path) -> List[str]:
        """檢查必要 section，回傳缺失的 section"""
        if not self.validate_exists(path):
            return self.REQUIRED_SECTIONS

        with open(path) as f:
            content = f.read().lower()

        missing = []
        # 檢查中文或英文的 section
        section_pairs = [
            ("核心發現", "core findings"),
            ("詳細分析", "detailed analysis"),
        ]

        for zh, en in section_pairs:
            if zh.lower() not in content and en.lower() not in content:
                missing.append(zh)

        return missing


@pytest.fixture
def report_validator() -> ReportValidator:
    """提供報告驗證器"""
    return ReportValidator()


# ===========================================================================
# Hook 模擬 Fixtures
# ===========================================================================


class MockHookTracker:
    """Hook 呼叫追蹤器"""

    def __init__(self):
        self.calls: List[Dict[str, Any]] = []
        self.pre_task_calls: List[Dict[str, Any]] = []
        self.post_task_calls: List[Dict[str, Any]] = []
        self.subagent_start_calls: List[Dict[str, Any]] = []
        self.subagent_stop_calls: List[Dict[str, Any]] = []

    def record_pre_task(self, data: Dict[str, Any]) -> None:
        """記錄 pre_task hook 呼叫"""
        record = {"hook": "pre_task", "timestamp": datetime.utcnow().isoformat(), **data}
        self.calls.append(record)
        self.pre_task_calls.append(record)

    def record_post_task(self, data: Dict[str, Any]) -> None:
        """記錄 post_task hook 呼叫"""
        record = {
            "hook": "post_task",
            "timestamp": datetime.utcnow().isoformat(),
            **data,
        }
        self.calls.append(record)
        self.post_task_calls.append(record)

    def record_subagent_start(self, data: Dict[str, Any]) -> None:
        """記錄 subagent_start hook 呼叫"""
        record = {
            "hook": "subagent_start",
            "timestamp": datetime.utcnow().isoformat(),
            **data,
        }
        self.calls.append(record)
        self.subagent_start_calls.append(record)

    def record_subagent_stop(self, data: Dict[str, Any]) -> None:
        """記錄 subagent_stop hook 呼叫"""
        record = {
            "hook": "subagent_stop",
            "timestamp": datetime.utcnow().isoformat(),
            **data,
        }
        self.calls.append(record)
        self.subagent_stop_calls.append(record)

    def clear(self) -> None:
        """清除所有記錄"""
        self.calls.clear()
        self.pre_task_calls.clear()
        self.post_task_calls.clear()
        self.subagent_start_calls.clear()
        self.subagent_stop_calls.clear()


@pytest.fixture
def hook_tracker() -> Generator[MockHookTracker, None, None]:
    """提供 Hook 追蹤器"""
    tracker = MockHookTracker()
    yield tracker
    tracker.clear()


# ===========================================================================
# Sample Data Fixtures
# ===========================================================================


@pytest.fixture
def sample_prompt() -> str:
    """提供範例 Prompt"""
    return """## 任務

你是一位 架構分析師。

### 目標
分析系統架構，識別核心組件和設計模式。

### 聚焦領域
- 系統結構
- 設計模式
- 組件關係

### 背景（精簡）
這是一個多代理工作流系統。

### 相關檔案
以下檔案可能有用，請使用 Read 工具讀取：
- .claude/memory/research/previous/synthesis.md
- shared/config/context-freshness.yaml

### 輸出要求
- 詳細的架構分析報告
- 關鍵發現和建議

### 輸出路徑
完成後，將報告寫入：.claude/memory/research/test-001/perspectives/architecture.md
"""


@pytest.fixture
def sample_report() -> str:
    """提供範例報告"""
    return """# 架構分析報告

## 核心發現

### 1. 系統採用 Map-Reduce 模式
系統使用並行視角分析（Map）和結果整合（Reduce）的模式。

### 2. 上下文新鮮機制
每個 Task 擁有獨立的上下文，確保分析品質。

### 3. 品質閘門控制
每個階段都有品質閘門，確保產出符合標準。

## 詳細分析

### 架構概述
多代理工作流系統採用 6 階段設計：
1. RESEARCH - 研究階段
2. PLAN - 規劃階段
3. TASKS - 任務分解
4. IMPLEMENT - 實作階段
5. REVIEW - 審查階段
6. VERIFY - 驗證階段

### 組件分析

#### 1. Skills 模組
Skills 定義了可重用的工作流能力。

#### 2. Agents 模組
Agents 是執行具體任務的實體。

#### 3. Coordination 模組
協調模組管理多視角的並行執行和結果整合。

### 設計模式

#### Map-Reduce
- Map: 多視角並行分析
- Reduce: 結果整合與衝突解決

#### 品質閘門
- 每階段有明確的通過標準
- 失敗時觸發修復循環

## 建議

1. 保持 Task 獨立性原則
2. 避免跨 Task 共享狀態
3. 使用品質閘門確保產出

## 結論

系統架構設計良好，支援可擴展的多代理協作。
"""


@pytest.fixture
def sample_tasks_yaml() -> Dict[str, Any]:
    """提供範例 tasks.yaml"""
    return {
        "version": "1.0",
        "tasks": [
            {
                "id": "SETUP-001",
                "title": "環境設置",
                "description": "設置開發環境",
                "status": "completed",
                "wave": 1,
            },
            {
                "id": "TEST-001",
                "title": "撰寫測試",
                "description": "撰寫單元測試",
                "status": "pending",
                "depends_on": ["SETUP-001"],
                "wave": 2,
            },
            {
                "id": "T-F-001",
                "title": "實作功能",
                "description": "實作主要功能",
                "status": "pending",
                "depends_on": ["TEST-001"],
                "wave": 3,
            },
        ],
    }


@pytest.fixture
def sample_action_log() -> List[Dict[str, Any]]:
    """提供範例 action log"""
    return [
        {
            "id": "act_20260127_120000_abc123",
            "timestamp": "2026-01-27T12:00:00Z",
            "workflow_id": "wf-test-001",
            "agent_id": "research-architecture",
            "stage": "RESEARCH",
            "tool": "Task",
            "status": "started",
            "input": {"description": "research architecture"},
        },
        {
            "id": "act_20260127_120500_def456",
            "timestamp": "2026-01-27T12:05:00Z",
            "workflow_id": "wf-test-001",
            "agent_id": "research-architecture",
            "stage": "RESEARCH",
            "tool": "Read",
            "status": "success",
            "input": {"file_path": "/path/to/file.md"},
            "output_size": 1024,
        },
        {
            "id": "act_20260127_121000_ghi789",
            "timestamp": "2026-01-27T12:10:00Z",
            "workflow_id": "wf-test-001",
            "agent_id": "research-architecture",
            "stage": "RESEARCH",
            "tool": "Task",
            "status": "success",
            "input": {"description": "research architecture"},
            "output_preview": "完成架構分析...",
        },
    ]


# ===========================================================================
# 工具函數
# ===========================================================================


def create_test_report(path: Path, content: str = None, lines: int = 60) -> None:
    """建立測試報告檔案"""
    path.parent.mkdir(parents=True, exist_ok=True)

    if content:
        path.write_text(content)
    else:
        # 生成指定行數的預設報告
        default_content = """# 測試報告

## 核心發現

這是測試核心發現內容。

## 詳細分析

這是測試詳細分析內容。

"""
        # 填充到指定行數
        padding_lines = max(0, lines - len(default_content.split("\n")))
        padding = "\n".join([f"# 填充行 {i}" for i in range(padding_lines)])
        path.write_text(default_content + padding)


def create_test_workflow_state(
    workflow_dir: Path, workflow_id: str, stage: str = "RESEARCH"
) -> None:
    """建立測試 workflow 狀態"""
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


def create_test_action_log(
    workflow_dir: Path, workflow_id: str, actions: List[Dict[str, Any]]
) -> Path:
    """建立測試 action log"""
    log_dir = workflow_dir / workflow_id / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "actions.jsonl"
    with open(log_file, "w") as f:
        for action in actions:
            f.write(json.dumps(action, ensure_ascii=False) + "\n")

    return log_file
