"""
視角配置 - 定義各階段的視角

每個視角代表一個專業角色，負責從特定角度分析問題。
"""

from typing import Dict, List

from .models import PerspectiveConfig, StageID


# ─────────────────────────────────────────────────────────────────────────────
# 視角定義
# ─────────────────────────────────────────────────────────────────────────────

PERSPECTIVES: Dict[str, PerspectiveConfig] = {
    # ───────────────────────────────────────────────────────────────────────
    # RESEARCH 階段視角
    # ───────────────────────────────────────────────────────────────────────
    "architecture": PerspectiveConfig(
        id="architecture",
        name="架構分析師",
        description="分析系統結構、設計模式、技術選型",
        focus_areas=[
            "系統架構",
            "設計模式",
            "技術棧選擇",
            "可擴展性",
            "模組化",
        ],
        model="sonnet",
    ),
    "cognitive": PerspectiveConfig(
        id="cognitive",
        name="認知研究員",
        description="研究使用者心智模型、認知負荷、學習曲線",
        focus_areas=[
            "使用者心智模型",
            "認知負荷",
            "學習曲線",
            "錯誤預防",
            "直覺性",
        ],
        model="sonnet",
    ),
    "workflow": PerspectiveConfig(
        id="workflow",
        name="工作流設計師",
        description="設計操作流程、狀態轉換、錯誤處理",
        focus_areas=[
            "操作流程",
            "狀態管理",
            "錯誤處理",
            "邊界情況",
            "資料流",
        ],
        model="sonnet",
    ),
    "industry": PerspectiveConfig(
        id="industry",
        name="業界實踐專家",
        description="研究業界最佳實踐、競品分析、趨勢",
        focus_areas=[
            "業界標準",
            "最佳實踐",
            "競品分析",
            "技術趨勢",
            "案例研究",
        ],
        model="sonnet",
    ),
    # ───────────────────────────────────────────────────────────────────────
    # PLAN 階段視角
    # ───────────────────────────────────────────────────────────────────────
    "system_architect": PerspectiveConfig(
        id="system_architect",
        name="系統架構師",
        description="設計系統架構、元件關係、介面定義",
        focus_areas=[
            "系統設計",
            "元件劃分",
            "介面定義",
            "依賴管理",
            "部署架構",
        ],
        model="sonnet",
    ),
    "ux_designer": PerspectiveConfig(
        id="ux_designer",
        name="UX 設計師",
        description="設計使用者體驗、互動流程、介面規格",
        focus_areas=[
            "使用者體驗",
            "互動設計",
            "資訊架構",
            "可用性",
            "無障礙",
        ],
        model="sonnet",
    ),
    "security_analyst": PerspectiveConfig(
        id="security_analyst",
        name="安全分析師",
        description="分析安全風險、設計防護措施",
        focus_areas=[
            "威脅模型",
            "安全控制",
            "資料保護",
            "認證授權",
            "合規要求",
        ],
        model="sonnet",
    ),
    "quality_engineer": PerspectiveConfig(
        id="quality_engineer",
        name="品質工程師",
        description="設計測試策略、品質指標、驗收標準",
        focus_areas=[
            "測試策略",
            "品質指標",
            "驗收標準",
            "效能要求",
            "可靠性",
        ],
        model="sonnet",
    ),
    # ───────────────────────────────────────────────────────────────────────
    # TASKS 階段視角
    # ───────────────────────────────────────────────────────────────────────
    "task_decomposer": PerspectiveConfig(
        id="task_decomposer",
        name="任務分解專家",
        description="將計劃分解為可執行的原子任務",
        focus_areas=[
            "任務粒度",
            "完成定義",
            "驗收條件",
            "可測試性",
            "獨立性",
        ],
        model="sonnet",
    ),
    "dependency_analyst": PerspectiveConfig(
        id="dependency_analyst",
        name="依賴分析師",
        description="分析任務依賴、設計執行順序",
        focus_areas=[
            "依賴關係",
            "執行順序",
            "並行機會",
            "瓶頸識別",
            "關鍵路徑",
        ],
        model="sonnet",
    ),
    "test_planner": PerspectiveConfig(
        id="test_planner",
        name="測試規劃師",
        description="為每個任務設計對應的測試",
        focus_areas=[
            "TDD 映射",
            "測試用例",
            "邊界條件",
            "錯誤路徑",
            "整合測試",
        ],
        model="sonnet",
    ),
    "risk_preventor": PerspectiveConfig(
        id="risk_preventor",
        name="風險預防師",
        description="識別任務風險、設計預防措施",
        focus_areas=[
            "風險識別",
            "影響評估",
            "預防措施",
            "回退計劃",
            "監控指標",
        ],
        model="sonnet",
    ),
    # ───────────────────────────────────────────────────────────────────────
    # IMPLEMENT 階段視角
    # ───────────────────────────────────────────────────────────────────────
    "developer": PerspectiveConfig(
        id="developer",
        name="開發者",
        description="實作功能、撰寫程式碼",
        focus_areas=[
            "功能實作",
            "程式碼品質",
            "效能優化",
            "錯誤處理",
            "文件註解",
        ],
        model="sonnet",
    ),
    "tdd_coach": PerspectiveConfig(
        id="tdd_coach",
        name="TDD 教練",
        description="指導測試驅動開發、確保測試覆蓋",
        focus_areas=[
            "測試先行",
            "紅綠重構",
            "測試覆蓋",
            "測試品質",
            "邊界測試",
        ],
        model="sonnet",
    ),
    "reviewer": PerspectiveConfig(
        id="reviewer",
        name="即時審查者",
        description="即時審查程式碼、提供改進建議",
        focus_areas=[
            "程式碼審查",
            "最佳實踐",
            "一致性",
            "可讀性",
            "改進建議",
        ],
        model="sonnet",
    ),
    # ───────────────────────────────────────────────────────────────────────
    # REVIEW 階段視角
    # ───────────────────────────────────────────────────────────────────────
    "code_quality": PerspectiveConfig(
        id="code_quality",
        name="程式碼品質審查員",
        description="審查程式碼品質、一致性、可讀性",
        focus_areas=[
            "程式碼風格",
            "命名規範",
            "結構清晰",
            "重複程式碼",
            "複雜度",
        ],
        model="sonnet",
    ),
    "security": PerspectiveConfig(
        id="security",
        name="安全審查員",
        description="審查安全漏洞、敏感資料處理",
        focus_areas=[
            "注入攻擊",
            "認證授權",
            "資料暴露",
            "加密處理",
            "日誌安全",
        ],
        model="sonnet",
    ),
    "performance": PerspectiveConfig(
        id="performance",
        name="效能審查員",
        description="審查效能問題、資源使用",
        focus_areas=[
            "時間複雜度",
            "空間複雜度",
            "資源洩漏",
            "並發處理",
            "快取策略",
        ],
        model="sonnet",
    ),
    "maintainability": PerspectiveConfig(
        id="maintainability",
        name="可維護性審查員",
        description="審查可維護性、擴展性、文件",
        focus_areas=[
            "模組化",
            "解耦合",
            "文件完整",
            "測試覆蓋",
            "技術債務",
        ],
        model="sonnet",
    ),
    # ───────────────────────────────────────────────────────────────────────
    # VERIFY 階段視角
    # ───────────────────────────────────────────────────────────────────────
    "functional_tester": PerspectiveConfig(
        id="functional_tester",
        name="功能測試員",
        description="驗證功能正確性、邊界情況",
        focus_areas=[
            "功能驗證",
            "邊界測試",
            "錯誤處理",
            "使用者流程",
            "異常情況",
        ],
        model="sonnet",
    ),
    "regression_tester": PerspectiveConfig(
        id="regression_tester",
        name="回歸測試員",
        description="驗證既有功能未受影響",
        focus_areas=[
            "回歸測試",
            "整合測試",
            "相容性",
            "向後相容",
            "副作用",
        ],
        model="sonnet",
    ),
    "acceptance_validator": PerspectiveConfig(
        id="acceptance_validator",
        name="驗收驗證員",
        description="驗證是否符合驗收標準",
        focus_areas=[
            "驗收標準",
            "需求符合",
            "品質達標",
            "文件完整",
            "發布準備",
        ],
        model="sonnet",
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# 階段視角映射
# ─────────────────────────────────────────────────────────────────────────────

STAGE_PERSPECTIVES: Dict[StageID, List[str]] = {
    StageID.RESEARCH: ["architecture", "cognitive", "workflow", "industry"],
    StageID.PLAN: ["system_architect", "ux_designer", "security_analyst", "quality_engineer"],
    StageID.TASKS: ["task_decomposer", "dependency_analyst", "test_planner", "risk_preventor"],
    StageID.IMPLEMENT: ["developer", "tdd_coach", "reviewer"],
    StageID.REVIEW: ["code_quality", "security", "performance", "maintainability"],
    StageID.VERIFY: ["functional_tester", "regression_tester", "acceptance_validator"],
}

# 快速模式視角（減少數量）
QUICK_MODE_PERSPECTIVES: Dict[StageID, List[str]] = {
    StageID.RESEARCH: ["architecture", "workflow"],
    StageID.PLAN: ["system_architect", "quality_engineer"],
    StageID.TASKS: ["task_decomposer", "dependency_analyst"],
    StageID.IMPLEMENT: ["developer", "reviewer"],
    StageID.REVIEW: ["code_quality", "security"],
    StageID.VERIFY: ["functional_tester", "acceptance_validator"],
}


# ─────────────────────────────────────────────────────────────────────────────
# 便捷函數
# ─────────────────────────────────────────────────────────────────────────────


def get_perspective(perspective_id: str) -> PerspectiveConfig | None:
    """取得視角配置"""
    return PERSPECTIVES.get(perspective_id)


def get_stage_perspectives(
    stage_id: StageID,
    quick_mode: bool = False,
) -> List[PerspectiveConfig]:
    """取得階段的視角列表"""
    if quick_mode:
        perspective_ids = QUICK_MODE_PERSPECTIVES.get(stage_id, [])
    else:
        perspective_ids = STAGE_PERSPECTIVES.get(stage_id, [])

    return [PERSPECTIVES[pid] for pid in perspective_ids if pid in PERSPECTIVES]


def list_all_perspectives() -> List[PerspectiveConfig]:
    """列出所有視角"""
    return list(PERSPECTIVES.values())
