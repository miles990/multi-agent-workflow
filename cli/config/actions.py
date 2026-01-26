"""
Action 描述映射 - 定義所有 Action 的描述與格式
"""

from typing import Dict, List, TypedDict


class ActionInfo(TypedDict):
    """Action 資訊"""

    name: str
    description: str
    level: str  # info, warning, error
    format: str  # 格式化字串模板


# ─────────────────────────────────────────────────────────────────────────────
# Action 定義
# ─────────────────────────────────────────────────────────────────────────────

ACTIONS: Dict[str, ActionInfo] = {
    "workflow_init": ActionInfo(
        name="工作流初始化",
        description="開始新的工作流",
        level="info",
        format="🚀 工作流開始: {topic}",
    ),
    "stage_start": ActionInfo(
        name="階段開始",
        description="開始執行新階段",
        level="info",
        format="📋 階段開始: {stage_name} ({stage_id})",
    ),
    "stage_complete": ActionInfo(
        name="階段完成",
        description="階段執行完成",
        level="info",
        format="✅ 階段完成: {stage_id}",
    ),
    "agent_start": ActionInfo(
        name="Agent 開始",
        description="Agent 開始執行任務",
        level="info",
        format="🤖 Agent 開始: {agent_name} ({agent_id})",
    ),
    "agent_complete": ActionInfo(
        name="Agent 完成",
        description="Agent 執行完成",
        level="info",
        format="✅ Agent 完成: {agent_id}",
    ),
    "agent_call_error": ActionInfo(
        name="Agent 錯誤",
        description="Agent 調用失敗",
        level="error",
        format="❌ Agent 錯誤: {agent_id} - {reason}",
    ),
    "file_write": ActionInfo(
        name="檔案寫入",
        description="寫入檔案",
        level="info",
        format="📝 寫入: {path} ({size_bytes} bytes)",
    ),
    "gate_check": ActionInfo(
        name="品質閘門檢查",
        description="執行品質閘門檢查",
        level="info",
        format="🔍 閘門檢查: {stage} - {score}/{threshold}",
    ),
    "gate_failed": ActionInfo(
        name="閘門失敗",
        description="品質閘門檢查失敗",
        level="error",
        format="❌ 閘門失敗: {stage} - {failed_criteria}",
    ),
    "rollback_triggered": ActionInfo(
        name="回退觸發",
        description="觸發智慧回退",
        level="warning",
        format="🔙 回退: {from_stage} → {to_stage} (第 {iteration} 次)",
    ),
    "workflow_complete": ActionInfo(
        name="工作流完成",
        description="工作流執行完成",
        level="info",
        format="🎉 工作流完成: {final_status} ({duration_seconds:.1f}s)",
    ),
    "workflow_error": ActionInfo(
        name="工作流錯誤",
        description="工作流執行錯誤",
        level="error",
        format="❌ 工作流錯誤: {error}",
    ),
    "human_intervention": ActionInfo(
        name="人工介入",
        description="需要人工介入",
        level="warning",
        format="👤 需要人工介入: {reason}",
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# 便捷函數
# ─────────────────────────────────────────────────────────────────────────────


def get_action_info(action: str) -> ActionInfo | None:
    """取得 Action 資訊"""
    return ACTIONS.get(action)


def format_action(action: str, details: Dict) -> str:
    """格式化 Action 訊息"""
    info = ACTIONS.get(action)
    if not info:
        return f"{action}: {details}"

    try:
        return info["format"].format(**details)
    except KeyError:
        return f"{info['name']}: {details}"


def get_action_level(action: str) -> str:
    """取得 Action 等級"""
    info = ACTIONS.get(action)
    return info["level"] if info else "info"


def list_actions() -> List[str]:
    """列出所有 Action"""
    return list(ACTIONS.keys())


def list_error_actions() -> List[str]:
    """列出所有錯誤類型的 Action"""
    return [action for action, info in ACTIONS.items() if info["level"] == "error"]


def list_warning_actions() -> List[str]:
    """列出所有警告類型的 Action"""
    return [action for action, info in ACTIONS.items() if info["level"] == "warning"]
