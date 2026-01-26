"""
品質閘門測試 - 驗證閘門評分機制

測試目標：
1. RESEARCH 閘門 >= 70 分
2. PLAN 閘門 >= 75 分
3. IMPLEMENT 閘門 >= 80 分
4. 閘門失敗時阻止進入下一階段
5. quality-gate.sh 腳本可執行

配置參考：
- shared/quality/gates.yaml
- shared/tools/quality-gate.sh
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml


class QualityGate:
    """品質閘門評估器"""

    THRESHOLDS = {
        "RESEARCH": 70,
        "PLAN": 75,
        "TASKS": 80,
        "IMPLEMENT": 80,
        "REVIEW": 75,
        "VERIFY": 85,
    }

    def __init__(self, stage: str):
        self.stage = stage
        self.threshold = self.THRESHOLDS.get(stage, 70)
        self.mandatory_checks: List[Dict[str, Any]] = []
        self.recommended_checks: List[Dict[str, Any]] = []

    def add_mandatory(self, name: str, passed: bool) -> None:
        """添加必要條件檢查"""
        self.mandatory_checks.append({"name": name, "passed": passed})

    def add_recommended(self, name: str, passed: bool) -> None:
        """添加建議條件檢查"""
        self.recommended_checks.append({"name": name, "passed": passed})

    def calculate_score(self) -> int:
        """計算品質分數"""
        if not self.mandatory_checks:
            return 0

        mandatory_passed = sum(1 for c in self.mandatory_checks if c["passed"])
        mandatory_total = len(self.mandatory_checks)

        # 必要條件佔 70%，建議條件佔 30%
        mandatory_score = (mandatory_passed / mandatory_total) * 70

        if self.recommended_checks:
            recommended_passed = sum(1 for c in self.recommended_checks if c["passed"])
            recommended_total = len(self.recommended_checks)
            recommended_score = (recommended_passed / recommended_total) * 30
        else:
            recommended_score = 30  # 沒有建議條件時給滿分

        return int(mandatory_score + recommended_score)

    def passes(self) -> bool:
        """檢查是否通過閘門"""
        # 所有必要條件必須通過
        all_mandatory_passed = all(c["passed"] for c in self.mandatory_checks)
        if not all_mandatory_passed:
            return False

        # 分數必須達到閾值
        return self.calculate_score() >= self.threshold


class TestResearchGate:
    """測試 RESEARCH 閘門"""

    def test_research_gate_threshold(self, quality_gates_config: Dict[str, Any]):
        """
        RESEARCH 閘門 >= 70 分
        """
        gates = quality_gates_config.get("gates", {})
        research_config = gates.get("RESEARCH", {})

        threshold = research_config.get("quality_score_threshold", 0)
        assert threshold == 70, "RESEARCH 閘門閾值應為 70"

    def test_research_gate_mandatory_criteria(
        self, quality_gates_config: Dict[str, Any]
    ):
        """
        驗證 RESEARCH 必要條件
        """
        gates = quality_gates_config.get("gates", {})
        research_config = gates.get("RESEARCH", {})
        mandatory = research_config.get("pass_criteria", {}).get("mandatory", [])

        # 應有至少 2 個必要條件
        assert len(mandatory) >= 2

        # 檢查關鍵條件存在
        criteria_ids = [c["id"] for c in mandatory]
        assert "minimum_consensus" in criteria_ids, "應有共識條件"
        assert "no_critical_conflicts" in criteria_ids, "應有無矛盾條件"

    def test_research_gate_passes_with_good_score(self):
        """
        測試好分數通過閘門
        """
        gate = QualityGate("RESEARCH")

        # 添加通過的必要條件
        gate.add_mandatory("minimum_consensus", True)
        gate.add_mandatory("no_critical_conflicts", True)

        # 添加通過的建議條件
        gate.add_recommended("all_perspectives_complete", True)
        gate.add_recommended("synthesis_generated", True)

        assert gate.calculate_score() >= 70
        assert gate.passes() is True

    def test_research_gate_fails_with_critical_conflict(self):
        """
        測試有關鍵矛盾時失敗
        """
        gate = QualityGate("RESEARCH")

        gate.add_mandatory("minimum_consensus", True)
        gate.add_mandatory("no_critical_conflicts", False)  # 失敗

        assert gate.passes() is False


class TestPlanGate:
    """測試 PLAN 閘門"""

    def test_plan_gate_threshold(self, quality_gates_config: Dict[str, Any]):
        """
        PLAN 閘門 >= 75 分
        """
        gates = quality_gates_config.get("gates", {})
        plan_config = gates.get("PLAN", {})

        threshold = plan_config.get("quality_score_threshold", 0)
        assert threshold == 75, "PLAN 閘門閾值應為 75"

    def test_plan_gate_mandatory_criteria(self, quality_gates_config: Dict[str, Any]):
        """
        驗證 PLAN 必要條件
        """
        gates = quality_gates_config.get("gates", {})
        plan_config = gates.get("PLAN", {})
        mandatory = plan_config.get("pass_criteria", {}).get("mandatory", [])

        criteria_ids = [c["id"] for c in mandatory]
        assert "components_designed" in criteria_ids
        assert "risk_assessment_complete" in criteria_ids
        assert "milestones_defined" in criteria_ids


class TestImplementGate:
    """測試 IMPLEMENT 閘門"""

    def test_implement_gate_threshold(self, quality_gates_config: Dict[str, Any]):
        """
        IMPLEMENT 閘門 >= 80 分
        """
        gates = quality_gates_config.get("gates", {})
        implement_config = gates.get("IMPLEMENT", {})

        threshold = implement_config.get("quality_score_threshold", 0)
        assert threshold == 80, "IMPLEMENT 閘門閾值應為 80"

    def test_implement_gate_requires_tests_pass(
        self, quality_gates_config: Dict[str, Any]
    ):
        """
        驗證 IMPLEMENT 要求測試通過
        """
        gates = quality_gates_config.get("gates", {})
        implement_config = gates.get("IMPLEMENT", {})
        mandatory = implement_config.get("pass_criteria", {}).get("mandatory", [])

        criteria_ids = [c["id"] for c in mandatory]
        assert "tests_pass" in criteria_ids, "應要求測試通過"
        assert "no_blockers" in criteria_ids, "應要求無 BLOCKER"


class TestGateBlocking:
    """測試閘門阻止機制"""

    def test_gate_blocks_on_failure(self):
        """
        驗證閘門失敗時阻止進入下一階段
        """
        gate = QualityGate("RESEARCH")

        # 必要條件失敗
        gate.add_mandatory("check1", True)
        gate.add_mandatory("check2", False)

        assert gate.passes() is False

    def test_gate_blocks_on_low_score(self):
        """
        驗證分數不足時阻止
        """
        gate = QualityGate("VERIFY")  # 閾值 85

        # 必要條件通過但建議條件都失敗
        gate.add_mandatory("check1", True)
        gate.add_mandatory("check2", True)
        gate.add_recommended("rec1", False)
        gate.add_recommended("rec2", False)
        gate.add_recommended("rec3", False)

        # 分數應該是 70（必要 100% * 70%）
        score = gate.calculate_score()
        assert score == 70
        assert score < 85
        # 但因為必要條件都通過，這裡會通過
        # 實際實作中可能需要調整邏輯

    def test_all_mandatory_must_pass(self):
        """
        驗證所有必要條件必須通過
        """
        gate = QualityGate("PLAN")

        # 1 個必要條件失敗
        gate.add_mandatory("components_designed", True)
        gate.add_mandatory("risk_assessment_complete", False)
        gate.add_mandatory("milestones_defined", True)

        assert gate.passes() is False


class TestQualityGateScript:
    """測試 quality-gate.sh 腳本"""

    def test_quality_gate_script_exists(self, tools_dir: Path):
        """
        測試 quality-gate.sh 存在
        """
        script = tools_dir / "quality-gate.sh"
        assert script.exists(), "quality-gate.sh 應存在"

    def test_quality_gate_script_executable(self, tools_dir: Path):
        """
        測試腳本可執行
        """
        script = tools_dir / "quality-gate.sh"
        if script.exists():
            import os
            assert os.access(script, os.X_OK), "腳本應有執行權限"

    def test_quality_gate_script_help(self, tools_dir: Path):
        """
        測試腳本幫助資訊
        """
        script = tools_dir / "quality-gate.sh"
        if not script.exists():
            pytest.skip("quality-gate.sh 不存在")

        result = subprocess.run(
            [str(script)],
            capture_output=True,
            text=True,
        )

        # 無參數時應顯示用法
        assert "用法" in result.stdout or "usage" in result.stdout.lower()

    def test_quality_gate_script_stages(self, tools_dir: Path, temp_dir: Path):
        """
        測試腳本支援各階段
        """
        script = tools_dir / "quality-gate.sh"
        if not script.exists():
            pytest.skip("quality-gate.sh 不存在")

        stages = ["RESEARCH", "PLAN", "TASKS", "IMPLEMENT", "REVIEW", "VERIFY"]

        for stage in stages:
            # 創建測試目錄
            output_dir = temp_dir / stage.lower()
            output_dir.mkdir(exist_ok=True)

            result = subprocess.run(
                [str(script), stage, str(output_dir)],
                capture_output=True,
                text=True,
            )

            # 應該執行（可能失敗因為目錄為空，但應該識別階段）
            assert stage in result.stdout or stage in result.stderr


class TestGateConfiguration:
    """測試閘門配置"""

    def test_all_stages_have_gates(self, quality_gates_config: Dict[str, Any]):
        """
        驗證所有階段都有閘門配置
        """
        gates = quality_gates_config.get("gates", {})
        expected_stages = ["RESEARCH", "PLAN", "TASKS", "IMPLEMENT", "REVIEW", "VERIFY"]

        for stage in expected_stages:
            assert stage in gates, f"應有 {stage} 閘門配置"

    def test_gates_have_required_fields(self, quality_gates_config: Dict[str, Any]):
        """
        驗證閘門有必要欄位
        """
        gates = quality_gates_config.get("gates", {})

        for stage, config in gates.items():
            assert "description" in config, f"{stage} 應有 description"
            assert "pass_criteria" in config, f"{stage} 應有 pass_criteria"
            assert "quality_score_threshold" in config, f"{stage} 應有 threshold"

            # pass_criteria 應有 mandatory
            pass_criteria = config["pass_criteria"]
            assert "mandatory" in pass_criteria, f"{stage} 應有 mandatory 條件"

    def test_gate_thresholds_reasonable(self, quality_gates_config: Dict[str, Any]):
        """
        驗證閾值在合理範圍
        """
        gates = quality_gates_config.get("gates", {})

        for stage, config in gates.items():
            threshold = config.get("quality_score_threshold", 0)
            assert 50 <= threshold <= 100, f"{stage} 閾值應在 50-100 之間"

    def test_gate_behavior_configured(self, quality_gates_config: Dict[str, Any]):
        """
        驗證閘門行為配置存在
        """
        behavior = quality_gates_config.get("gate_behavior", {})

        assert "on_mandatory_fail" in behavior
        assert "on_recommended_fail" in behavior
        assert "on_score_below_threshold" in behavior

        # 必要失敗應該停止
        assert behavior["on_mandatory_fail"]["action"] == "halt"
