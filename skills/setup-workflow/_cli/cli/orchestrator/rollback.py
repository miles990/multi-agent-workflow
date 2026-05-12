"""
智慧回退模組 - 根據迭代次數和錯誤類型決定回退目標

回退策略：
| 迭代 | 回退目標 | 原因 |
|------|----------|------|
| 1-2 | IMPLEMENT | 可能是實作問題 |
| 3 | TASKS | 可能是任務分解問題 |
| 4 | PLAN | 可能是設計問題 |
| 5+ | HUMAN | 超過自動修復能力 |

循環偵測：
- 相同錯誤兩次 → 升級回退層級
- 階段間振盪 → 暫停分析根因
- 總迭代 > 10 → 強制停止
"""

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from ..config.models import GateCheckResult, RollbackDecision, StageID


# 回退目標映射
ROLLBACK_TARGETS: Dict[int, StageID] = {
    1: StageID.IMPLEMENT,
    2: StageID.IMPLEMENT,
    3: StageID.TASKS,
    4: StageID.PLAN,
}

# 最大迭代次數
MAX_ITERATIONS = 10

# 相同錯誤閾值
SAME_ERROR_THRESHOLD = 2


class RollbackManager:
    """智慧回退管理器"""

    def __init__(self):
        """初始化回退管理器"""
        # 錯誤歷史：記錄每個階段的失敗原因
        self.error_history: Dict[str, List[str]] = defaultdict(list)
        # 階段轉換歷史：用於偵測振盪
        self.stage_transitions: List[Tuple[StageID, StageID]] = []

    def decide(
        self,
        current_stage: StageID,
        gate_result: GateCheckResult,
        iteration: int,
    ) -> RollbackDecision:
        """
        決定回退策略

        Args:
            current_stage: 當前階段
            gate_result: 品質閘門檢查結果
            iteration: 當前迭代次數

        Returns:
            RollbackDecision 物件
        """
        # 記錄錯誤
        error_key = self._create_error_key(current_stage, gate_result)
        self.error_history[current_stage.value].append(error_key)

        # 檢查是否超過最大迭代次數
        if iteration >= MAX_ITERATIONS:
            return RollbackDecision(
                should_rollback=False,
                from_stage=current_stage,
                to_stage=current_stage,
                iteration=iteration,
                reason=f"超過最大迭代次數 ({MAX_ITERATIONS})",
                require_human=True,
            )

        # 檢查循環偵測
        cycle_detected, cycle_reason = self._detect_cycle(
            current_stage,
            error_key,
            iteration,
        )
        if cycle_detected:
            return RollbackDecision(
                should_rollback=False,
                from_stage=current_stage,
                to_stage=current_stage,
                iteration=iteration,
                reason=cycle_reason,
                require_human=True,
            )

        # 根據迭代次數決定回退目標
        if iteration >= 5:
            return RollbackDecision(
                should_rollback=False,
                from_stage=current_stage,
                to_stage=current_stage,
                iteration=iteration,
                reason="迭代次數過多，需要人工介入",
                require_human=True,
            )

        # 取得回退目標
        target_stage = ROLLBACK_TARGETS.get(iteration, StageID.PLAN)

        # 確保不會回退到當前階段之後
        from ..config.stages import STAGE_ORDER

        current_idx = STAGE_ORDER.index(current_stage)
        target_idx = STAGE_ORDER.index(target_stage)

        if target_idx >= current_idx:
            # 回退到前一個階段
            if current_idx > 0:
                target_stage = STAGE_ORDER[current_idx - 1]
            else:
                # 已經是第一階段，需要人工介入
                return RollbackDecision(
                    should_rollback=False,
                    from_stage=current_stage,
                    to_stage=current_stage,
                    iteration=iteration,
                    reason="已經是第一階段，無法回退",
                    require_human=True,
                )

        # 記錄階段轉換
        self.stage_transitions.append((current_stage, target_stage))

        return RollbackDecision(
            should_rollback=True,
            from_stage=current_stage,
            to_stage=target_stage,
            iteration=iteration,
            reason=self._get_rollback_reason(iteration, gate_result),
            require_human=False,
        )

    def _create_error_key(
        self,
        stage: StageID,
        gate_result: GateCheckResult,
    ) -> str:
        """建立錯誤識別鍵"""
        failed = sorted(gate_result.failed_criteria)
        return f"{stage.value}:{','.join(failed)}"

    def _detect_cycle(
        self,
        current_stage: StageID,
        error_key: str,
        iteration: int,
    ) -> Tuple[bool, str]:
        """
        偵測循環

        Returns:
            (是否偵測到循環, 原因)
        """
        # 檢查相同錯誤
        stage_errors = self.error_history[current_stage.value]
        same_error_count = sum(1 for e in stage_errors if e == error_key)

        if same_error_count >= SAME_ERROR_THRESHOLD:
            return True, f"相同錯誤重複 {same_error_count} 次"

        # 檢查階段振盪 (A → B → A)
        if len(self.stage_transitions) >= 2:
            recent = self.stage_transitions[-2:]
            if len(recent) == 2:
                (from1, to1), (from2, to2) = recent
                if to1 == from2 and to2 == from1:
                    return True, f"階段振盪: {from1.value} ↔ {to1.value}"

        return False, ""

    def _get_rollback_reason(
        self,
        iteration: int,
        gate_result: GateCheckResult,
    ) -> str:
        """取得回退原因描述"""
        reasons = {
            1: "首次失敗，回退到實作階段重試",
            2: "第二次失敗，回退到實作階段進行修復",
            3: "多次實作失敗，回退到任務分解階段重新規劃",
            4: "任務分解可能有問題，回退到設計階段",
        }

        base_reason = reasons.get(iteration, "回退重試")

        if gate_result.failed_criteria:
            failed_str = ", ".join(gate_result.failed_criteria)
            return f"{base_reason} (失敗項目: {failed_str})"

        return base_reason

    def reset(self) -> None:
        """重置回退管理器"""
        self.error_history.clear()
        self.stage_transitions.clear()

    def get_history(self) -> Dict:
        """取得回退歷史"""
        return {
            "error_history": dict(self.error_history),
            "stage_transitions": [
                (f.value, t.value) for f, t in self.stage_transitions
            ],
        }
