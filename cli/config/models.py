"""
Pydantic 資料模型 - 定義所有資料結構

包含：
- Agent 相關模型
- 階段相關模型
- 工作流相關模型
- 品質閘門相關模型
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# 列舉類型
# ─────────────────────────────────────────────────────────────────────────────


class StageID(str, Enum):
    """階段 ID"""

    RESEARCH = "RESEARCH"
    PLAN = "PLAN"
    TASKS = "TASKS"
    IMPLEMENT = "IMPLEMENT"
    REVIEW = "REVIEW"
    VERIFY = "VERIFY"


class AgentStatus(str, Enum):
    """Agent 狀態"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStatus(str, Enum):
    """工作流狀態"""

    INITIALIZED = "initialized"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLBACK = "rollback"
    HUMAN_INTERVENTION = "human_intervention"


class WorkflowMode(str, Enum):
    """工作流模式"""

    QUICK = "quick"  # 快速模式：減少視角數量
    NORMAL = "normal"  # 正常模式
    DEEP = "deep"  # 深度模式：更多視角、更嚴格閘門


# ─────────────────────────────────────────────────────────────────────────────
# Agent 模型
# ─────────────────────────────────────────────────────────────────────────────


class AgentConfig(BaseModel):
    """Agent 配置"""

    id: str = Field(..., description="Agent ID")
    name: str = Field(..., description="Agent 名稱")
    description: Optional[str] = Field(None, description="Agent 描述")
    model: str = Field("sonnet", description="使用的模型")
    perspective: Optional[str] = Field(None, description="視角 ID")


class AgentResponse(BaseModel):
    """Agent 回應"""

    success: bool = Field(..., description="是否成功")
    content: Optional[Dict[str, Any]] = Field(None, description="JSON 回應內容")
    raw_output: Optional[str] = Field(None, description="原始輸出")
    error: Optional[str] = Field(None, description="錯誤訊息")
    tokens_used: Optional[int] = Field(None, description="使用的 token 數")
    duration_seconds: Optional[float] = Field(None, description="執行時間（秒）")


class AgentState(BaseModel):
    """Agent 執行狀態"""

    id: str
    name: str
    description: Optional[str] = None
    model: str = "sonnet"
    status: AgentStatus = AgentStatus.PENDING
    task: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ─────────────────────────────────────────────────────────────────────────────
# 階段模型
# ─────────────────────────────────────────────────────────────────────────────


class StageConfig(BaseModel):
    """階段配置"""

    id: StageID
    name: str
    description: str
    perspectives: List[str] = Field(default_factory=list)
    gate_threshold: float = Field(75.0, description="品質閘門閾值")
    required_outputs: List[str] = Field(default_factory=list)


class StageState(BaseModel):
    """階段狀態"""

    id: StageID
    name: str
    description: str
    index: int = Field(..., description="階段索引 (1-based)")
    total: int = Field(..., description="總階段數")
    status: AgentStatus = AgentStatus.PENDING


class StageResult(BaseModel):
    """階段執行結果"""

    stage_id: StageID
    success: bool
    outputs: Dict[str, str] = Field(default_factory=dict, description="輸出檔案路徑")
    quality_score: Optional[float] = None
    errors: List[str] = Field(default_factory=list)
    duration_seconds: Optional[float] = None


# ─────────────────────────────────────────────────────────────────────────────
# 品質閘門模型
# ─────────────────────────────────────────────────────────────────────────────


class GateCheckResult(BaseModel):
    """品質閘門檢查結果"""

    stage: StageID
    passed: bool
    score: float
    threshold: float
    criteria: Dict[str, bool] = Field(default_factory=dict)
    failed_criteria: List[str] = Field(default_factory=list)
    details: Optional[Dict[str, Any]] = None


class RollbackDecision(BaseModel):
    """回退決策"""

    should_rollback: bool
    from_stage: StageID
    to_stage: StageID
    iteration: int
    reason: str
    require_human: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# 工作流模型
# ─────────────────────────────────────────────────────────────────────────────


class WorkflowConfig(BaseModel):
    """工作流配置"""

    topic: str = Field(..., description="工作流主題/需求描述")
    mode: WorkflowMode = Field(WorkflowMode.NORMAL, description="執行模式")
    start_from: Optional[StageID] = Field(None, description="從指定階段開始")
    skip_stages: List[StageID] = Field(default_factory=list, description="跳過的階段")
    max_iterations: int = Field(10, description="最大迭代次數")


class WorkflowState(BaseModel):
    """工作流狀態"""

    id: str
    topic: str
    status: WorkflowStatus = WorkflowStatus.INITIALIZED
    current_stage: Optional[StageID] = None
    iteration: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class WorkflowResult(BaseModel):
    """工作流執行結果"""

    workflow_id: str
    success: bool
    final_status: WorkflowStatus
    quality_score: Optional[float] = None
    stage_results: Dict[str, StageResult] = Field(default_factory=dict)
    total_iterations: int = 0
    duration_seconds: Optional[float] = None
    errors: List[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# 視角模型
# ─────────────────────────────────────────────────────────────────────────────


class PerspectiveConfig(BaseModel):
    """視角配置"""

    id: str = Field(..., description="視角 ID")
    name: str = Field(..., description="視角名稱")
    description: str = Field(..., description="視角描述")
    focus_areas: List[str] = Field(default_factory=list, description="關注領域")
    model: str = Field("sonnet", description="使用的模型")


class PerspectiveReport(BaseModel):
    """視角報告"""

    perspective_id: str
    perspective_name: str
    content: str
    key_findings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# 輸出格式
# ─────────────────────────────────────────────────────────────────────────────


class CurrentState(BaseModel):
    """即時狀態（current.json 格式）"""

    updated_at: datetime = Field(default_factory=datetime.now)
    workflow: Dict[str, Any]
    stage: Optional[StageState] = None
    agents: List[AgentState] = Field(default_factory=list)
    progress: Dict[str, int] = Field(
        default_factory=lambda: {"agents_completed": 0, "agents_total": 0}
    )
