"""
視角報告驗證器 - 驗證 Agent 返回的視角報告格式

驗證項目：
- 必要欄位存在
- 欄位格式正確
- 內容品質檢查
"""

from typing import Any, Dict, List, Optional, Tuple

from ..config.schema import PERSPECTIVE_REPORT_SCHEMA


class PerspectiveValidator:
    """視角報告驗證器"""

    # 必要欄位
    REQUIRED_FIELDS = [
        "perspective_id",
        "perspective_name",
        "findings",
        "recommendations",
    ]

    # 欄位類型
    FIELD_TYPES = {
        "perspective_id": str,
        "perspective_name": str,
        "summary": str,
        "findings": list,
        "recommendations": list,
        "concerns": list,
    }

    def validate(
        self,
        report: Dict[str, Any],
        perspective_id: Optional[str] = None,
    ) -> Tuple[bool, List[str]]:
        """
        驗證視角報告

        Args:
            report: 視角報告內容
            perspective_id: 預期的視角 ID（可選）

        Returns:
            (是否有效, 錯誤列表)
        """
        errors = []

        # 1. 檢查必要欄位
        for field in self.REQUIRED_FIELDS:
            if field not in report:
                errors.append(f"缺少必要欄位: {field}")

        if errors:
            return False, errors

        # 2. 檢查欄位類型
        for field, expected_type in self.FIELD_TYPES.items():
            if field in report and not isinstance(report[field], expected_type):
                errors.append(
                    f"欄位類型錯誤: {field} 應為 {expected_type.__name__}"
                )

        # 3. 檢查視角 ID 一致性
        if perspective_id and report.get("perspective_id") != perspective_id:
            errors.append(
                f"視角 ID 不一致: 預期 {perspective_id}, 實際 {report.get('perspective_id')}"
            )

        # 4. 檢查 findings 結構
        findings_errors = self._validate_findings(report.get("findings", []))
        errors.extend(findings_errors)

        # 5. 檢查 recommendations 結構
        rec_errors = self._validate_recommendations(report.get("recommendations", []))
        errors.extend(rec_errors)

        # 6. 檢查 concerns 結構（如果存在）
        if "concerns" in report:
            concern_errors = self._validate_concerns(report.get("concerns", []))
            errors.extend(concern_errors)

        return len(errors) == 0, errors

    def _validate_findings(self, findings: List) -> List[str]:
        """驗證 findings 結構"""
        errors = []

        if not isinstance(findings, list):
            return ["findings 必須是陣列"]

        for i, finding in enumerate(findings):
            if not isinstance(finding, dict):
                errors.append(f"findings[{i}] 必須是物件")
                continue

            if "title" not in finding:
                errors.append(f"findings[{i}] 缺少 title")
            if "description" not in finding:
                errors.append(f"findings[{i}] 缺少 description")

            # 檢查 importance（如果存在）
            importance = finding.get("importance")
            if importance and importance not in ["high", "medium", "low"]:
                errors.append(
                    f"findings[{i}].importance 無效: {importance}"
                )

        return errors

    def _validate_recommendations(self, recommendations: List) -> List[str]:
        """驗證 recommendations 結構"""
        errors = []

        if not isinstance(recommendations, list):
            return ["recommendations 必須是陣列"]

        for i, rec in enumerate(recommendations):
            if not isinstance(rec, dict):
                errors.append(f"recommendations[{i}] 必須是物件")
                continue

            if "title" not in rec:
                errors.append(f"recommendations[{i}] 缺少 title")
            if "description" not in rec:
                errors.append(f"recommendations[{i}] 缺少 description")

            # 檢查 priority（如果存在）
            priority = rec.get("priority")
            if priority and priority not in ["must", "should", "could"]:
                errors.append(
                    f"recommendations[{i}].priority 無效: {priority}"
                )

        return errors

    def _validate_concerns(self, concerns: List) -> List[str]:
        """驗證 concerns 結構"""
        errors = []

        if not isinstance(concerns, list):
            return ["concerns 必須是陣列"]

        for i, concern in enumerate(concerns):
            if not isinstance(concern, dict):
                errors.append(f"concerns[{i}] 必須是物件")
                continue

            if "title" not in concern:
                errors.append(f"concerns[{i}] 缺少 title")
            if "description" not in concern:
                errors.append(f"concerns[{i}] 缺少 description")

            # 檢查 severity（如果存在）
            severity = concern.get("severity")
            if severity and severity not in ["critical", "high", "medium", "low"]:
                errors.append(
                    f"concerns[{i}].severity 無效: {severity}"
                )

        return errors

    def calculate_quality_score(self, report: Dict[str, Any]) -> float:
        """
        計算視角報告的品質分數

        評分標準：
        - 必要欄位完整: 30%
        - findings 數量與品質: 30%
        - recommendations 數量與品質: 30%
        - 額外內容 (summary, concerns): 10%

        Returns:
            品質分數 (0-100)
        """
        score = 0.0

        # 1. 必要欄位完整性 (30%)
        required_present = sum(
            1 for f in self.REQUIRED_FIELDS if f in report
        )
        score += (required_present / len(self.REQUIRED_FIELDS)) * 30

        # 2. findings 品質 (30%)
        findings = report.get("findings", [])
        if findings:
            # 數量分數 (最多 5 個)
            count_score = min(len(findings) / 5, 1.0) * 15
            # 品質分數
            quality_score = self._calculate_items_quality(findings) * 15
            score += count_score + quality_score

        # 3. recommendations 品質 (30%)
        recommendations = report.get("recommendations", [])
        if recommendations:
            # 數量分數 (最多 5 個)
            count_score = min(len(recommendations) / 5, 1.0) * 15
            # 品質分數
            quality_score = self._calculate_items_quality(recommendations) * 15
            score += count_score + quality_score

        # 4. 額外內容 (10%)
        if report.get("summary"):
            score += 5
        if report.get("concerns"):
            score += 5

        return round(score, 2)

    def _calculate_items_quality(self, items: List[Dict]) -> float:
        """計算項目列表的品質分數"""
        if not items:
            return 0.0

        quality_sum = 0.0
        for item in items:
            # 有 title: +0.3
            # 有 description: +0.3
            # description 長度 >= 50: +0.2
            # 有 importance/priority/severity: +0.2
            item_score = 0.0

            if item.get("title"):
                item_score += 0.3
            if item.get("description"):
                item_score += 0.3
                if len(item["description"]) >= 50:
                    item_score += 0.2
            if any(k in item for k in ["importance", "priority", "severity"]):
                item_score += 0.2

            quality_sum += item_score

        return quality_sum / len(items)


# 全域實例
_validator: Optional[PerspectiveValidator] = None


def get_perspective_validator() -> PerspectiveValidator:
    """取得視角驗證器"""
    global _validator
    if _validator is None:
        _validator = PerspectiveValidator()
    return _validator


def validate_perspective_report(
    report: Dict[str, Any],
    perspective_id: Optional[str] = None,
) -> Tuple[bool, List[str]]:
    """快速驗證視角報告"""
    return get_perspective_validator().validate(report, perspective_id)
