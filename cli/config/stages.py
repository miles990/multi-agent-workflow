"""
階段配置 - 定義各階段的描述與配置

6 個階段：RESEARCH → PLAN → TASKS → IMPLEMENT → REVIEW → VERIFY
"""

from typing import Dict, List

from .models import StageConfig, StageID


# ─────────────────────────────────────────────────────────────────────────────
# 階段定義
# ─────────────────────────────────────────────────────────────────────────────

STAGES: Dict[StageID, StageConfig] = {
    StageID.RESEARCH: StageConfig(
        id=StageID.RESEARCH,
        name="研究階段",
        description="多視角並行研究，收集資訊與洞察",
        perspectives=[
            "architecture",
            "cognitive",
            "workflow",
            "industry",
        ],
        gate_threshold=70.0,
        required_outputs=["synthesis.md"],
    ),
    StageID.PLAN: StageConfig(
        id=StageID.PLAN,
        name="規劃階段",
        description="多視角設計，產出實作計劃",
        perspectives=[
            "system_architect",
            "ux_designer",
            "security_analyst",
            "quality_engineer",
        ],
        gate_threshold=75.0,
        required_outputs=["implementation-plan.md"],
    ),
    StageID.TASKS: StageConfig(
        id=StageID.TASKS,
        name="任務分解階段",
        description="將計劃分解為可執行的任務 DAG",
        perspectives=[
            "task_decomposer",
            "dependency_analyst",
            "test_planner",
            "risk_preventor",
        ],
        gate_threshold=80.0,
        required_outputs=["tasks.yaml"],
    ),
    StageID.IMPLEMENT: StageConfig(
        id=StageID.IMPLEMENT,
        name="實作階段",
        description="TDD 驅動、即時審查、品質守護",
        perspectives=[
            "developer",
            "tdd_coach",
            "reviewer",
        ],
        gate_threshold=80.0,
        required_outputs=["implementation.md"],
    ),
    StageID.REVIEW: StageConfig(
        id=StageID.REVIEW,
        name="審查階段",
        description="多視角程式碼審查，問題分類與優先排序",
        perspectives=[
            "code_quality",
            "security",
            "performance",
            "maintainability",
        ],
        gate_threshold=75.0,
        required_outputs=["review-summary.md"],
    ),
    StageID.VERIFY: StageConfig(
        id=StageID.VERIFY,
        name="驗證階段",
        description="多視角測試驗證，驗收標準確認",
        perspectives=[
            "functional_tester",
            "regression_tester",
            "acceptance_validator",
        ],
        gate_threshold=85.0,
        required_outputs=["verification.md"],
    ),
}

# 階段順序
STAGE_ORDER: List[StageID] = [
    StageID.RESEARCH,
    StageID.PLAN,
    StageID.TASKS,
    StageID.IMPLEMENT,
    StageID.REVIEW,
    StageID.VERIFY,
]

# 階段權重（用於進度計算）
STAGE_WEIGHTS: Dict[StageID, float] = {
    StageID.RESEARCH: 0.15,
    StageID.PLAN: 0.15,
    StageID.TASKS: 0.10,
    StageID.IMPLEMENT: 0.35,
    StageID.REVIEW: 0.15,
    StageID.VERIFY: 0.10,
}


# ─────────────────────────────────────────────────────────────────────────────
# 便捷函數
# ─────────────────────────────────────────────────────────────────────────────


def get_stage(stage_id: StageID) -> StageConfig:
    """取得階段配置"""
    return STAGES[stage_id]


def get_stage_index(stage_id: StageID) -> int:
    """取得階段索引 (1-based)"""
    return STAGE_ORDER.index(stage_id) + 1


def get_next_stage(stage_id: StageID) -> StageID | None:
    """取得下一個階段"""
    idx = STAGE_ORDER.index(stage_id)
    if idx < len(STAGE_ORDER) - 1:
        return STAGE_ORDER[idx + 1]
    return None


def get_prev_stage(stage_id: StageID) -> StageID | None:
    """取得上一個階段"""
    idx = STAGE_ORDER.index(stage_id)
    if idx > 0:
        return STAGE_ORDER[idx - 1]
    return None


def is_final_stage(stage_id: StageID) -> bool:
    """是否為最後階段"""
    return stage_id == STAGE_ORDER[-1]


def get_stage_by_name(name: str) -> StageID | None:
    """根據名稱取得階段 ID"""
    name_upper = name.upper()
    for stage_id in StageID:
        if stage_id.value == name_upper:
            return stage_id
    return None
