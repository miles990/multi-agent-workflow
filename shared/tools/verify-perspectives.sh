#!/bin/bash
# =============================================================================
# verify-perspectives.sh - 驗證視角報告完整性
#
# 位置: shared/tools/verify-perspectives.sh
# 用途: 驗證 MAP Phase 產出的視角報告是否完整
#
# 用法: ./verify-perspectives.sh <type> <id> <expected_count>
# 範例: ./verify-perspectives.sh research user-auth-20260126 4
# =============================================================================

set -euo pipefail

# 顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 參數
TYPE="${1:-}"
ID="${2:-}"
EXPECTED="${3:-4}"
MIN_LINES="${4:-50}"

# 驗證參數
if [ -z "$TYPE" ] || [ -z "$ID" ]; then
    echo -e "${RED}用法: $0 <type> <id> <expected_count> [min_lines]${NC}"
    echo ""
    echo "參數:"
    echo "  type           - skill 類型 (research/plan/tasks/implement/review/verify)"
    echo "  id             - 記錄 ID"
    echo "  expected_count - 預期報告數量 (預設: 4)"
    echo "  min_lines      - 每份報告最少行數 (預設: 50)"
    echo ""
    echo "範例:"
    echo "  $0 research user-auth-20260126 4"
    echo "  $0 plan feature-x-20260126 3 30"
    exit 1
fi

# 路徑
MEMORY_BASE=".claude/memory"
PERSPECTIVES_DIR="${MEMORY_BASE}/${TYPE}/${ID}/perspectives"

echo -e "${BLUE}驗證視角報告完整性${NC}"
echo "  類型: ${TYPE}"
echo "  ID: ${ID}"
echo "  預期報告數: ${EXPECTED}"
echo "  最少行數: ${MIN_LINES}"
echo ""

# 檢查 1: perspectives 目錄是否存在
if [ ! -d "$PERSPECTIVES_DIR" ]; then
    echo -e "${RED}ERROR: perspectives 目錄不存在${NC}"
    echo "  路徑: ${PERSPECTIVES_DIR}"
    echo ""
    echo "可能原因:"
    echo "  - MAP Phase 尚未執行"
    echo "  - Agent 未正確保存報告"
    echo "  - 路徑配置錯誤"
    exit 1
fi

echo -e "${GREEN}✓ perspectives 目錄存在${NC}"

# 檢查 2: 報告數量
REPORTS=($(find "$PERSPECTIVES_DIR" -name "*.md" -type f 2>/dev/null))
ACTUAL=${#REPORTS[@]}

if [ "$ACTUAL" -lt "$EXPECTED" ]; then
    echo -e "${RED}ERROR: 報告數量不足${NC}"
    echo "  預期: ${EXPECTED}"
    echo "  實際: ${ACTUAL}"
    echo ""
    echo "已找到的報告:"
    for report in "${REPORTS[@]}"; do
        echo "  - $(basename "$report")"
    done
    echo ""
    echo "缺失的報告請檢查 MAP Phase 是否正確執行。"
    exit 1
fi

echo -e "${GREEN}✓ 報告數量符合預期 (${ACTUAL}/${EXPECTED})${NC}"

# 檢查 3: 每份報告的行數和內容
ERRORS=0
WARNINGS=0

for report in "${REPORTS[@]}"; do
    REPORT_NAME=$(basename "$report")
    LINE_COUNT=$(wc -l < "$report" | tr -d ' ')

    # 檢查行數
    if [ "$LINE_COUNT" -lt "$MIN_LINES" ]; then
        echo -e "${YELLOW}⚠ ${REPORT_NAME}: 只有 ${LINE_COUNT} 行 (< ${MIN_LINES})${NC}"
        ((WARNINGS++))
    else
        echo -e "${GREEN}✓ ${REPORT_NAME}: ${LINE_COUNT} 行${NC}"
    fi

    # 檢查必要 section
    if ! grep -q "## 核心發現" "$report" && ! grep -q "## Core Findings" "$report"; then
        echo -e "${YELLOW}  ⚠ 缺少「核心發現」section${NC}"
        ((WARNINGS++))
    fi

    if ! grep -q "## 詳細分析" "$report" && ! grep -q "## Detailed Analysis" "$report"; then
        echo -e "${YELLOW}  ⚠ 缺少「詳細分析」section${NC}"
        ((WARNINGS++))
    fi
done

echo ""

# 結果摘要
if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}驗證失敗: ${ERRORS} 個錯誤, ${WARNINGS} 個警告${NC}"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}驗證通過（有警告）: ${WARNINGS} 個警告${NC}"
    echo "建議檢查報告內容是否完整。"
    exit 0
else
    echo -e "${GREEN}驗證通過: 所有報告完整${NC}"
    exit 0
fi
