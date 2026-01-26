"""
Prompts 模組 - 各階段 Prompt 模板

包含：
- research.py: 研究階段
- plan.py: 規劃階段
- tasks.py: 任務分解階段
- implement.py: 實作階段
- review.py: 審查階段
- verify.py: 驗證階段
"""

from typing import Any, Dict

from ..config.models import PerspectiveConfig, StageID

# 導入各階段模組
from . import research, plan, tasks, implement, review, verify


# 視角 Prompt 映射
_PERSPECTIVE_PROMPT_FUNCS = {
    StageID.RESEARCH: research.get_research_perspective_prompt,
    StageID.PLAN: plan.get_plan_perspective_prompt,
    StageID.TASKS: tasks.get_tasks_perspective_prompt,
    StageID.IMPLEMENT: implement.get_implement_perspective_prompt,
    StageID.REVIEW: review.get_review_perspective_prompt,
    StageID.VERIFY: verify.get_verify_perspective_prompt,
}

# 綜合報告 Prompt 映射
_SYNTHESIS_PROMPT_FUNCS = {
    StageID.RESEARCH: research.get_research_synthesis_prompt,
    StageID.PLAN: plan.get_plan_synthesis_prompt,
    StageID.TASKS: tasks.get_tasks_synthesis_prompt,
    StageID.IMPLEMENT: implement.get_implement_synthesis_prompt,
    StageID.REVIEW: review.get_review_synthesis_prompt,
    StageID.VERIFY: verify.get_verify_synthesis_prompt,
}


def get_perspective_prompt(
    stage_id: StageID,
    perspective: PerspectiveConfig,
    context: Dict[str, Any],
) -> str:
    """
    取得視角 Prompt

    Args:
        stage_id: 階段 ID
        perspective: 視角配置
        context: 執行上下文

    Returns:
        完整 Prompt 字串
    """
    func = _PERSPECTIVE_PROMPT_FUNCS.get(stage_id)
    if func:
        return func(perspective, context)

    # 預設 Prompt
    from .base import (
        build_system_context,
        build_perspective_header,
        build_json_output_format,
        PERSPECTIVE_REPORT_SCHEMA_DESC,
    )

    parts = [
        build_system_context(context),
        build_perspective_header(perspective),
        f"## Task\n\nAnalyze the topic from your perspective: {context.get('topic', '')}",
        build_json_output_format(PERSPECTIVE_REPORT_SCHEMA_DESC),
    ]
    return "\n".join(parts)


def get_synthesis_prompt(
    stage_id: StageID,
    perspective_contents: Dict[str, Dict],
    context: Dict[str, Any],
) -> str:
    """
    取得綜合報告 Prompt

    Args:
        stage_id: 階段 ID
        perspective_contents: 各視角的報告內容
        context: 執行上下文

    Returns:
        完整 Prompt 字串
    """
    func = _SYNTHESIS_PROMPT_FUNCS.get(stage_id)
    if func:
        return func(perspective_contents, context)

    # 預設 Prompt
    from .base import (
        build_system_context,
        build_json_output_format,
        SYNTHESIS_REPORT_SCHEMA_DESC,
    )

    parts = [
        build_system_context(context),
        "# Task: Synthesize Findings",
        f"Synthesize findings from {len(perspective_contents)} perspectives.",
        build_json_output_format(SYNTHESIS_REPORT_SCHEMA_DESC),
    ]
    return "\n".join(parts)


__all__ = [
    "get_perspective_prompt",
    "get_synthesis_prompt",
]
