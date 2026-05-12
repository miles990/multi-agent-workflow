"""
JSON Schema 定義 - 定義各種輸出格式的 Schema

用於驗證 Agent 返回的 JSON 格式。
"""

from typing import Any, Dict


# ─────────────────────────────────────────────────────────────────────────────
# 視角報告 Schema
# ─────────────────────────────────────────────────────────────────────────────

PERSPECTIVE_REPORT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["perspective_id", "perspective_name", "findings", "recommendations"],
    "properties": {
        "perspective_id": {
            "type": "string",
            "description": "視角 ID",
        },
        "perspective_name": {
            "type": "string",
            "description": "視角名稱",
        },
        "summary": {
            "type": "string",
            "description": "摘要（1-2 句話）",
        },
        "findings": {
            "type": "array",
            "description": "主要發現",
            "items": {
                "type": "object",
                "required": ["title", "description"],
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "importance": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                    },
                },
            },
        },
        "recommendations": {
            "type": "array",
            "description": "建議",
            "items": {
                "type": "object",
                "required": ["title", "description"],
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {
                        "type": "string",
                        "enum": ["must", "should", "could"],
                    },
                },
            },
        },
        "concerns": {
            "type": "array",
            "description": "擔憂或風險",
            "items": {
                "type": "object",
                "required": ["title", "description"],
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "severity": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low"],
                    },
                },
            },
        },
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 階段綜合報告 Schema
# ─────────────────────────────────────────────────────────────────────────────

SYNTHESIS_REPORT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["stage_id", "consensus", "key_insights", "action_items"],
    "properties": {
        "stage_id": {
            "type": "string",
            "description": "階段 ID",
        },
        "consensus": {
            "type": "object",
            "description": "共識點",
            "properties": {
                "score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "共識分數 (0-1)",
                },
                "points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "共識要點",
                },
            },
        },
        "key_insights": {
            "type": "array",
            "description": "關鍵洞察",
            "items": {
                "type": "object",
                "required": ["insight", "source_perspectives"],
                "properties": {
                    "insight": {"type": "string"},
                    "source_perspectives": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                    },
                },
            },
        },
        "conflicts": {
            "type": "array",
            "description": "衝突點",
            "items": {
                "type": "object",
                "required": ["topic", "perspectives"],
                "properties": {
                    "topic": {"type": "string"},
                    "perspectives": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "perspective_id": {"type": "string"},
                                "position": {"type": "string"},
                            },
                        },
                    },
                    "resolution": {"type": "string"},
                },
            },
        },
        "action_items": {
            "type": "array",
            "description": "行動項目",
            "items": {
                "type": "object",
                "required": ["action", "priority"],
                "properties": {
                    "action": {"type": "string"},
                    "priority": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low"],
                    },
                    "owner": {"type": "string"},
                },
            },
        },
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 任務清單 Schema
# ─────────────────────────────────────────────────────────────────────────────

TASKS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["tasks"],
    "properties": {
        "metadata": {
            "type": "object",
            "properties": {
                "total_tasks": {"type": "integer"},
                "total_waves": {"type": "integer"},
                "estimated_effort": {"type": "string"},
            },
        },
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "title", "type"],
                "properties": {
                    "id": {
                        "type": "string",
                        "pattern": "^(T-[A-Z]+-[0-9]+|TEST-[0-9]+|SETUP-[0-9]+)$",
                        "description": "任務 ID (如 T-F-01, TEST-01)",
                    },
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": ["feature", "test", "setup", "config", "docs"],
                    },
                    "wave": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "執行波次",
                    },
                    "depends_on": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "依賴的任務 ID",
                    },
                    "acceptance_criteria": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "test_id": {
                        "type": "string",
                        "description": "對應的測試任務 ID (TDD)",
                    },
                },
            },
        },
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 審查報告 Schema
# ─────────────────────────────────────────────────────────────────────────────

REVIEW_REPORT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["perspective_id", "issues"],
    "properties": {
        "perspective_id": {"type": "string"},
        "perspective_name": {"type": "string"},
        "summary": {"type": "string"},
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "title", "severity", "category"],
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "severity": {
                        "type": "string",
                        "enum": ["BLOCKER", "HIGH", "MEDIUM", "LOW", "INFO"],
                    },
                    "category": {
                        "type": "string",
                        "enum": [
                            "bug",
                            "security",
                            "performance",
                            "style",
                            "maintainability",
                            "documentation",
                        ],
                    },
                    "file": {"type": "string"},
                    "line": {"type": "integer"},
                    "suggestion": {"type": "string"},
                },
            },
        },
        "approval": {
            "type": "string",
            "enum": ["approved", "approved_with_comments", "changes_requested"],
        },
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 驗證結果 Schema
# ─────────────────────────────────────────────────────────────────────────────

VERIFICATION_REPORT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["perspective_id", "test_results"],
    "properties": {
        "perspective_id": {"type": "string"},
        "perspective_name": {"type": "string"},
        "summary": {"type": "string"},
        "test_results": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["test_id", "status"],
                "properties": {
                    "test_id": {"type": "string"},
                    "test_name": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["passed", "failed", "skipped", "error"],
                    },
                    "details": {"type": "string"},
                    "duration_ms": {"type": "number"},
                },
            },
        },
        "coverage": {
            "type": "object",
            "properties": {
                "line_coverage": {"type": "number"},
                "branch_coverage": {"type": "number"},
                "function_coverage": {"type": "number"},
            },
        },
        "verdict": {
            "type": "string",
            "enum": ["pass", "fail", "conditional"],
        },
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Schema 映射
# ─────────────────────────────────────────────────────────────────────────────

SCHEMAS: Dict[str, Dict[str, Any]] = {
    "perspective_report": PERSPECTIVE_REPORT_SCHEMA,
    "synthesis_report": SYNTHESIS_REPORT_SCHEMA,
    "tasks": TASKS_SCHEMA,
    "review_report": REVIEW_REPORT_SCHEMA,
    "verification_report": VERIFICATION_REPORT_SCHEMA,
}


def get_schema(schema_name: str) -> Dict[str, Any] | None:
    """取得 Schema"""
    return SCHEMAS.get(schema_name)
