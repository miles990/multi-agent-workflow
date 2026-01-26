"""
Claude Code Hooks for Multi-Agent Workflow

自動處理：
- Action logging (所有工具調用)
- State tracking (Agent 狀態更新)
- Memory commits (CP4 自動 commit)
"""

from .log_action import log_action
from .update_state import update_state

__all__ = ["log_action", "update_state"]
