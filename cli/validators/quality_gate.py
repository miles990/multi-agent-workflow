"""
品質閘門模組 - 各階段的品質檢查

閘門分數要求：
| 階段 | 閘門分數 | 必要條件 |
|------|---------|---------|
| RESEARCH | ≥70 | 共識≥2、無關鍵矛盾 |
| PLAN | ≥75 | 組件設計、風險評估、里程碑 |
| TASKS | ≥80 | DAG 有效、TDD 對應 |
| IMPLEMENT | ≥80 | 任務完成、測試通過 |
| REVIEW | ≥75 | 無 BLOCKER、HIGH≤2 |
| VERIFY | ≥85 | 功能測試、回歸測試 |
"""

from typing import Any, Dict, List, Optional

from ..config.models import GateCheckResult, StageID, StageResult


# 階段閘門閾值
GATE_THRESHOLDS = {
    StageID.RESEARCH: 70.0,
    StageID.PLAN: 75.0,
    StageID.TASKS: 80.0,
    StageID.IMPLEMENT: 80.0,
    StageID.REVIEW: 75.0,
    StageID.VERIFY: 85.0,
}


class QualityGate:
    """品質閘門"""

    def __init__(self, threshold: Optional[float] = None):
        """
        初始化品質閘門

        Args:
            threshold: 自訂閾值（覆蓋預設值）
        """
        self.custom_threshold = threshold

    def check(
        self,
        stage_id: StageID,
        result: StageResult,
        extra_data: Optional[Dict] = None,
    ) -> GateCheckResult:
        """
        執行品質閘門檢查

        Args:
            stage_id: 階段 ID
            result: 階段執行結果
            extra_data: 額外資料（用於特定階段的檢查）

        Returns:
            GateCheckResult 物件
        """
        threshold = self.custom_threshold or GATE_THRESHOLDS.get(stage_id, 75.0)

        # 執行階段特定的檢查
        checker = self._get_stage_checker(stage_id)
        criteria, details = checker(result, extra_data or {})

        # 計算總分
        score = result.quality_score or 0.0

        # 額外扣分
        failed_criteria = [k for k, v in criteria.items() if not v]

        # 每個失敗的關鍵條件扣 10 分
        critical_deduction = len(failed_criteria) * 10
        final_score = max(0, score - critical_deduction)

        passed = final_score >= threshold and len(failed_criteria) == 0

        return GateCheckResult(
            stage=stage_id,
            passed=passed,
            score=final_score,
            threshold=threshold,
            criteria=criteria,
            failed_criteria=failed_criteria,
            details=details,
        )

    def _get_stage_checker(self, stage_id: StageID):
        """取得階段特定的檢查器"""
        checkers = {
            StageID.RESEARCH: self._check_research,
            StageID.PLAN: self._check_plan,
            StageID.TASKS: self._check_tasks,
            StageID.IMPLEMENT: self._check_implement,
            StageID.REVIEW: self._check_review,
            StageID.VERIFY: self._check_verify,
        }
        return checkers.get(stage_id, self._check_default)

    def _check_default(
        self,
        result: StageResult,
        extra_data: Dict,
    ) -> tuple[Dict[str, bool], Dict]:
        """預設檢查"""
        criteria = {
            "stage_success": result.success,
            "has_outputs": len(result.outputs) > 0,
        }
        return criteria, {}

    def _check_research(
        self,
        result: StageResult,
        extra_data: Dict,
    ) -> tuple[Dict[str, bool], Dict]:
        """
        RESEARCH 階段檢查

        必要條件：
        - 共識數量 ≥ 2
        - 無關鍵矛盾
        """
        criteria = {
            "stage_success": result.success,
            "has_synthesis": "synthesis" in result.outputs,
        }

        # 檢查共識和矛盾（從 extra_data 或 outputs 讀取）
        synthesis_data = extra_data.get("synthesis", {})
        consensus = synthesis_data.get("consensus", {})

        if consensus:
            consensus_points = len(consensus.get("points", []))
            criteria["consensus_count"] = consensus_points >= 2

            conflicts = synthesis_data.get("conflicts", [])
            critical_conflicts = [
                c for c in conflicts
                if not c.get("resolution")
            ]
            criteria["no_critical_conflicts"] = len(critical_conflicts) == 0

        details = {
            "consensus_count": len(consensus.get("points", [])) if consensus else 0,
        }

        return criteria, details

    def _check_plan(
        self,
        result: StageResult,
        extra_data: Dict,
    ) -> tuple[Dict[str, bool], Dict]:
        """
        PLAN 階段檢查

        必要條件：
        - 組件設計
        - 風險評估
        - 里程碑
        """
        criteria = {
            "stage_success": result.success,
            "has_plan": any("plan" in k.lower() for k in result.outputs),
        }

        plan_data = extra_data.get("plan", {})

        if plan_data:
            criteria["has_components"] = bool(plan_data.get("components"))
            criteria["has_risks"] = bool(plan_data.get("risks"))
            criteria["has_milestones"] = bool(plan_data.get("milestones"))

        return criteria, {}

    def _check_tasks(
        self,
        result: StageResult,
        extra_data: Dict,
    ) -> tuple[Dict[str, bool], Dict]:
        """
        TASKS 階段檢查

        必要條件：
        - DAG 有效（無循環）
        - TDD 對應（feature 有對應 test）
        """
        criteria = {
            "stage_success": result.success,
            "has_tasks": any("task" in k.lower() for k in result.outputs),
        }

        tasks_data = extra_data.get("tasks", {})
        tasks = tasks_data.get("tasks", []) if isinstance(tasks_data, dict) else []

        if tasks:
            # 檢查 DAG 有效性
            criteria["dag_valid"] = self._validate_dag(tasks)

            # 檢查 TDD 對應
            criteria["tdd_mapping"] = self._validate_tdd_mapping(tasks)

        details = {
            "task_count": len(tasks),
        }

        return criteria, details

    def _validate_dag(self, tasks: List[Dict]) -> bool:
        """驗證 DAG 無循環"""
        from collections import defaultdict

        # 建立鄰接表
        graph = defaultdict(list)
        all_ids = set()

        for task in tasks:
            task_id = task.get("id", "")
            all_ids.add(task_id)
            deps = task.get("depends_on", []) or task.get("blockedBy", []) or []
            if isinstance(deps, str):
                deps = [deps]
            for dep in deps:
                graph[dep].append(task_id)

        # DFS 檢測循環
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for task_id in all_ids:
            if task_id not in visited:
                if has_cycle(task_id):
                    return False

        return True

    def _validate_tdd_mapping(self, tasks: List[Dict]) -> bool:
        """驗證 TDD 對應"""
        task_ids = {t.get("id", "") for t in tasks}

        for task in tasks:
            task_id = task.get("id", "")
            # 檢查 feature 任務是否有對應的 test
            if task_id.startswith("T-F-"):
                test_id = task_id.replace("T-F-", "TEST-")
                if test_id not in task_ids:
                    return False

        return True

    def _check_implement(
        self,
        result: StageResult,
        extra_data: Dict,
    ) -> tuple[Dict[str, bool], Dict]:
        """
        IMPLEMENT 階段檢查

        必要條件：
        - 任務完成率 ≥ 90%
        - 測試通過率 ≥ 95%
        """
        criteria = {
            "stage_success": result.success,
        }

        impl_data = extra_data.get("implementation", {})

        if impl_data:
            task_completion = impl_data.get("task_completion", 0)
            test_pass_rate = impl_data.get("test_pass_rate", 0)

            criteria["task_completion"] = task_completion >= 0.9
            criteria["test_pass_rate"] = test_pass_rate >= 0.95

        details = {
            "task_completion": impl_data.get("task_completion", 0) if impl_data else 0,
            "test_pass_rate": impl_data.get("test_pass_rate", 0) if impl_data else 0,
        }

        return criteria, details

    def _check_review(
        self,
        result: StageResult,
        extra_data: Dict,
    ) -> tuple[Dict[str, bool], Dict]:
        """
        REVIEW 階段檢查

        必要條件：
        - 無 BLOCKER 問題
        - HIGH 問題 ≤ 2
        """
        criteria = {
            "stage_success": result.success,
        }

        review_data = extra_data.get("review", {})
        issues = review_data.get("issues", []) if isinstance(review_data, dict) else []

        blocker_count = sum(1 for i in issues if i.get("severity") == "BLOCKER")
        high_count = sum(1 for i in issues if i.get("severity") == "HIGH")

        criteria["no_blockers"] = blocker_count == 0
        criteria["high_issues_limit"] = high_count <= 2

        details = {
            "blocker_count": blocker_count,
            "high_count": high_count,
            "total_issues": len(issues),
        }

        return criteria, details

    def _check_verify(
        self,
        result: StageResult,
        extra_data: Dict,
    ) -> tuple[Dict[str, bool], Dict]:
        """
        VERIFY 階段檢查

        必要條件：
        - 功能測試通過
        - 回歸測試通過
        """
        criteria = {
            "stage_success": result.success,
        }

        verify_data = extra_data.get("verification", {})

        if verify_data:
            test_results = verify_data.get("test_results", [])

            # 檢查功能測試
            functional_tests = [t for t in test_results if "functional" in t.get("test_id", "").lower()]
            functional_passed = all(t.get("status") == "passed" for t in functional_tests) if functional_tests else True
            criteria["functional_tests"] = functional_passed

            # 檢查回歸測試
            regression_tests = [t for t in test_results if "regression" in t.get("test_id", "").lower()]
            regression_passed = all(t.get("status") == "passed" for t in regression_tests) if regression_tests else True
            criteria["regression_tests"] = regression_passed

            # 檢查整體通過率
            if test_results:
                pass_rate = sum(1 for t in test_results if t.get("status") == "passed") / len(test_results)
                criteria["pass_rate"] = pass_rate >= 0.95

        details = {
            "verdict": verify_data.get("verdict", "unknown") if verify_data else "unknown",
        }

        return criteria, details


# 便捷函數
def check_quality_gate(
    stage_id: StageID,
    result: StageResult,
    extra_data: Optional[Dict] = None,
) -> GateCheckResult:
    """快速執行品質閘門檢查"""
    gate = QualityGate()
    return gate.check(stage_id, result, extra_data)
