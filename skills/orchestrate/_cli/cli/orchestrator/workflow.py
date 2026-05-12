"""
工作流狀態機 - 管理完整工作流執行

流程：
RESEARCH → PLAN → TASKS → IMPLEMENT → REVIEW → VERIFY
                                        ↑__________↓
                                      智慧回退機制
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import hashlib

from ..config.models import (
    GateCheckResult,
    StageID,
    StageResult,
    WorkflowConfig,
    WorkflowMode,
    WorkflowResult,
    WorkflowStatus,
)
from ..config.stages import (
    STAGE_ORDER,
    get_stage,
    get_stage_index,
    get_next_stage,
    is_final_stage,
)
from ..io.logging import ActionLogger, get_logger
from ..io.memory import MemoryManager, get_memory
from ..io.state import StateTracker, get_tracker
from .agent_caller import AgentCaller
from .errors import (
    GateFailedError,
    HumanInterventionRequired,
    RollbackError,
    WorkflowError,
)
from .rollback import RollbackManager
from .stage_runner import StageRunner


def generate_workflow_id(topic: str) -> str:
    """生成工作流 ID"""
    date_str = datetime.now().strftime("%Y%m%d")
    hash_str = hashlib.md5(f"{topic}{time.time()}".encode()).hexdigest()[:6]
    # 簡化 topic 作為 ID 的一部分
    topic_slug = "".join(c for c in topic[:20] if c.isalnum() or c in "-_").lower()
    if not topic_slug:
        topic_slug = "workflow"
    return f"{topic_slug}-{date_str}-{hash_str}"


class Workflow:
    """工作流狀態機"""

    def __init__(
        self,
        config: WorkflowConfig,
        memory: Optional[MemoryManager] = None,
        caller: Optional[AgentCaller] = None,
    ):
        """
        初始化工作流

        Args:
            config: 工作流配置
            memory: Memory 管理器
            caller: Agent 調用器
        """
        self.config = config
        self.workflow_id = generate_workflow_id(config.topic)
        self.memory = memory or get_memory()
        self.caller = caller or AgentCaller()

        # 初始化元件
        self.logger = get_logger(self.workflow_id)
        self.tracker = get_tracker(self.workflow_id)
        self.rollback_manager = RollbackManager()

        # 狀態
        self.status = WorkflowStatus.INITIALIZED
        self.current_stage: Optional[StageID] = None
        self.iteration = 0
        self.stage_results: Dict[str, StageResult] = {}
        self.start_time: Optional[float] = None

        # 建立工作流目錄
        self._init_workflow()

    def _init_workflow(self) -> None:
        """初始化工作流目錄與狀態"""
        self.memory.create_workflow_dir(
            self.workflow_id,
            self.config.topic,
            {
                "mode": self.config.mode.value,
                "start_from": self.config.start_from.value if self.config.start_from else None,
                "skip_stages": [s.value for s in self.config.skip_stages],
            },
        )

        self.tracker.set_workflow(self.config.topic)
        self.logger.workflow_init(self.config.topic, {"mode": self.config.mode.value})

    def run(self) -> WorkflowResult:
        """
        執行完整工作流

        Returns:
            WorkflowResult 物件
        """
        self.start_time = time.time()
        self.status = WorkflowStatus.RUNNING
        errors: List[str] = []

        try:
            # 決定起始階段
            start_idx = 0
            if self.config.start_from:
                start_idx = STAGE_ORDER.index(self.config.start_from)

            # 執行各階段
            stage_idx = start_idx
            while stage_idx < len(STAGE_ORDER):
                stage_id = STAGE_ORDER[stage_idx]

                # 檢查是否跳過
                if stage_id in self.config.skip_stages:
                    stage_idx += 1
                    continue

                # 執行階段
                self.current_stage = stage_id
                self.memory.update_workflow_meta(
                    self.workflow_id,
                    {"current_stage": stage_id.value, "status": "running"},
                )

                result = self._run_stage(stage_id)
                self.stage_results[stage_id.value] = result

                if not result.success:
                    errors.extend(result.errors)

                # 品質閘門檢查
                gate_result = self._check_quality_gate(stage_id, result)

                if not gate_result.passed:
                    # 觸發回退
                    rollback_decision = self.rollback_manager.decide(
                        stage_id,
                        gate_result,
                        self.iteration,
                    )

                    if rollback_decision.require_human:
                        raise HumanInterventionRequired(
                            "需要人工介入",
                            reason=rollback_decision.reason,
                            context={
                                "stage": stage_id.value,
                                "iteration": self.iteration,
                            },
                        )

                    if rollback_decision.should_rollback:
                        self.logger.rollback_triggered(
                            from_stage=stage_id.value,
                            to_stage=rollback_decision.to_stage.value,
                            iteration=self.iteration,
                            reason=rollback_decision.reason,
                        )

                        # 回退到指定階段
                        stage_idx = STAGE_ORDER.index(rollback_decision.to_stage)
                        self.iteration += 1

                        # 檢查最大迭代次數
                        if self.iteration >= self.config.max_iterations:
                            raise HumanInterventionRequired(
                                "超過最大迭代次數",
                                reason=f"已迭代 {self.iteration} 次",
                            )

                        continue

                # 進入下一階段
                stage_idx += 1

            # 完成
            self.status = WorkflowStatus.COMPLETED
            duration = time.time() - self.start_time

            # 計算最終品質分數
            final_score = self._calculate_final_score()

            self.memory.update_workflow_meta(
                self.workflow_id,
                {
                    "status": "completed",
                    "quality_score": final_score,
                    "completed_at": datetime.now().isoformat(),
                },
            )

            self.logger.workflow_complete(
                duration_seconds=duration,
                final_status="completed",
                quality_score=final_score,
            )

            return WorkflowResult(
                workflow_id=self.workflow_id,
                success=True,
                final_status=WorkflowStatus.COMPLETED,
                quality_score=final_score,
                stage_results=self.stage_results,
                total_iterations=self.iteration,
                duration_seconds=duration,
                errors=errors,
            )

        except HumanInterventionRequired as e:
            self.status = WorkflowStatus.HUMAN_INTERVENTION
            duration = time.time() - self.start_time

            self.memory.update_workflow_meta(
                self.workflow_id,
                {"status": "human_intervention"},
            )

            self.logger.human_intervention(
                reason=e.reason,
                context=e.context,
            )

            return WorkflowResult(
                workflow_id=self.workflow_id,
                success=False,
                final_status=WorkflowStatus.HUMAN_INTERVENTION,
                stage_results=self.stage_results,
                total_iterations=self.iteration,
                duration_seconds=duration,
                errors=[str(e)],
            )

        except Exception as e:
            self.status = WorkflowStatus.FAILED
            duration = time.time() - self.start_time

            self.memory.update_workflow_meta(
                self.workflow_id,
                {"status": "failed"},
            )

            self.logger.workflow_error(
                error=str(e),
                stage=self.current_stage.value if self.current_stage else None,
            )

            return WorkflowResult(
                workflow_id=self.workflow_id,
                success=False,
                final_status=WorkflowStatus.FAILED,
                stage_results=self.stage_results,
                total_iterations=self.iteration,
                duration_seconds=duration,
                errors=[str(e)],
            )

    def _run_stage(self, stage_id: StageID) -> StageResult:
        """執行單一階段"""
        runner = StageRunner(
            workflow_id=self.workflow_id,
            memory=self.memory,
            logger=self.logger,
            tracker=self.tracker,
            caller=self.caller,
        )

        # 構建上下文
        context = self._build_stage_context(stage_id)

        # 執行
        quick_mode = self.config.mode == WorkflowMode.QUICK
        return runner.run(stage_id, context, quick_mode)

    def _build_stage_context(self, stage_id: StageID) -> Dict[str, Any]:
        """構建階段執行上下文"""
        context = {
            "workflow_id": self.workflow_id,
            "topic": self.config.topic,
            "stage_id": stage_id.value,
            "iteration": self.iteration,
            "mode": self.config.mode.value,
        }

        # 添加前階段的輸出
        prev_stages = STAGE_ORDER[:STAGE_ORDER.index(stage_id)]
        for prev_stage in prev_stages:
            if prev_stage.value in self.stage_results:
                result = self.stage_results[prev_stage.value]
                context[f"{prev_stage.value.lower()}_outputs"] = result.outputs
                context[f"{prev_stage.value.lower()}_score"] = result.quality_score

        return context

    def _check_quality_gate(
        self,
        stage_id: StageID,
        result: StageResult,
    ) -> GateCheckResult:
        """檢查品質閘門"""
        from ..validators.quality_gate import QualityGate

        stage_config = get_stage(stage_id)
        gate = QualityGate(stage_config.gate_threshold)

        gate_result = gate.check(stage_id, result)

        self.logger.gate_check(
            stage=stage_id.value,
            passed=gate_result.passed,
            score=gate_result.score,
            threshold=gate_result.threshold,
        )

        if not gate_result.passed:
            self.logger.gate_failed(
                stage=stage_id.value,
                failed_criteria=gate_result.failed_criteria,
            )

        return gate_result

    def _calculate_final_score(self) -> float:
        """計算最終品質分數"""
        if not self.stage_results:
            return 0.0

        scores = [
            r.quality_score
            for r in self.stage_results.values()
            if r.quality_score is not None
        ]

        if not scores:
            return 0.0

        return sum(scores) / len(scores)

    def resume(self, from_stage: Optional[StageID] = None) -> WorkflowResult:
        """
        恢復中斷的工作流

        Args:
            from_stage: 從指定階段恢復（預設從中斷處繼續）

        Returns:
            WorkflowResult 物件
        """
        # 更新配置
        if from_stage:
            self.config.start_from = from_stage

        # 重新執行
        return self.run()


def create_workflow(
    topic: str,
    mode: str = "normal",
    start_from: Optional[str] = None,
    skip_stages: Optional[List[str]] = None,
) -> Workflow:
    """
    建立工作流

    Args:
        topic: 工作流主題/需求描述
        mode: 執行模式 (quick/normal/deep)
        start_from: 從指定階段開始
        skip_stages: 跳過的階段列表

    Returns:
        Workflow 實例
    """
    # 轉換模式
    workflow_mode = WorkflowMode(mode) if mode in [m.value for m in WorkflowMode] else WorkflowMode.NORMAL

    # 轉換階段
    start_stage = None
    if start_from:
        start_stage = StageID(start_from.upper())

    skip = []
    if skip_stages:
        skip = [StageID(s.upper()) for s in skip_stages]

    config = WorkflowConfig(
        topic=topic,
        mode=workflow_mode,
        start_from=start_stage,
        skip_stages=skip,
    )

    return Workflow(config)
