"""
錯誤定義模組 - 所有自定義例外
"""

from typing import Optional


class MAWError(Exception):
    """Multi-Agent Workflow 基礎錯誤"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | {self.details}"
        return self.message


class WorkflowError(MAWError):
    """工作流層級錯誤"""

    pass


class StageError(MAWError):
    """階段執行錯誤"""

    def __init__(
        self,
        message: str,
        stage: str,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.stage = stage


class AgentError(MAWError):
    """Agent 調用錯誤"""

    def __init__(
        self,
        message: str,
        agent_id: Optional[str] = None,
        retryable: bool = True,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.agent_id = agent_id
        self.retryable = retryable


class ValidationError(MAWError):
    """驗證錯誤"""

    def __init__(
        self,
        message: str,
        validator: str,
        errors: Optional[list] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.validator = validator
        self.errors = errors or []


class RollbackError(MAWError):
    """回退錯誤"""

    def __init__(
        self,
        message: str,
        from_stage: str,
        to_stage: str,
        iteration: int,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.from_stage = from_stage
        self.to_stage = to_stage
        self.iteration = iteration


class GateFailedError(MAWError):
    """品質閘門失敗"""

    def __init__(
        self,
        message: str,
        stage: str,
        score: float,
        threshold: float,
        failed_criteria: Optional[list] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.stage = stage
        self.score = score
        self.threshold = threshold
        self.failed_criteria = failed_criteria or []


class HumanInterventionRequired(MAWError):
    """需要人工介入"""

    def __init__(
        self,
        message: str,
        reason: str,
        context: Optional[dict] = None,
    ):
        super().__init__(message, context)
        self.reason = reason
        self.context = context or {}
