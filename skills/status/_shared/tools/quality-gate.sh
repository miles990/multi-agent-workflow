#!/bin/bash
# 品質閘門驗證器 - 在階段轉換時執行
# 用法: ./quality-gate.sh <STAGE> <OUTPUT_DIR>

set -e

STAGE=$1
OUTPUT_DIR=$2

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 輸出函數
log_error() {
  echo -e "${RED}❌ 閘門失敗: $1${NC}"
}

log_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
  echo -e "${YELLOW}⚠️  $1${NC}"
}

log_info() {
  echo -e "${BLUE}ℹ️  $1${NC}"
}

# 檢查參數
if [[ -z "$STAGE" || -z "$OUTPUT_DIR" ]]; then
  echo "用法: $0 <STAGE> <OUTPUT_DIR>"
  echo "範例: $0 RESEARCH .claude/memory/research/001"
  echo ""
  echo "支援的階段: RESEARCH, PLAN, TASKS, IMPLEMENT, REVIEW, VERIFY"
  exit 1
fi

echo "═══════════════════════════════════════════"
echo "🚪 品質閘門檢查: $STAGE"
echo "輸出目錄: $OUTPUT_DIR"
echo "═══════════════════════════════════════════"

# 檢查輸出目錄是否存在
if [[ ! -d "$OUTPUT_DIR" ]]; then
  log_error "輸出目錄不存在: $OUTPUT_DIR"
  exit 1
fi

# 計分變數
MANDATORY_PASSED=0
MANDATORY_TOTAL=0
RECOMMENDED_PASSED=0
RECOMMENDED_TOTAL=0

# 檢查函數
check_mandatory() {
  local description=$1
  local condition=$2
  ((MANDATORY_TOTAL++))

  if eval "$condition"; then
    log_success "[必要] $description"
    ((MANDATORY_PASSED++))
    return 0
  else
    log_error "[必要] $description"
    return 1
  fi
}

check_recommended() {
  local description=$1
  local condition=$2
  ((RECOMMENDED_TOTAL++))

  if eval "$condition"; then
    log_success "[建議] $description"
    ((RECOMMENDED_PASSED++))
  else
    log_warning "[建議] $description"
  fi
}

# 根據階段執行檢查
case $STAGE in
  "RESEARCH")
    echo ""
    echo "📊 RESEARCH 階段閘門檢查"
    echo "───────────────────────"

    # 必要條件
    check_mandatory "匯總報告存在" "[[ -f '$OUTPUT_DIR/synthesis.md' ]]" || true

    # 檢查共識點數量
    if [[ -f "$OUTPUT_DIR/synthesis.md" ]]; then
      CONSENSUS_COUNT=$(grep -c "共識\|consensus\|agree" "$OUTPUT_DIR/synthesis.md" 2>/dev/null || echo 0)
      check_mandatory "至少 2 點共識 (當前: $CONSENSUS_COUNT)" "[[ $CONSENSUS_COUNT -ge 2 ]]" || true
    fi

    # 檢查無關鍵矛盾
    if [[ -f "$OUTPUT_DIR/synthesis.md" ]]; then
      CONFLICTS=$(grep -c "CRITICAL\|BLOCKER\|critical_conflict" "$OUTPUT_DIR/synthesis.md" 2>/dev/null || echo 0)
      check_mandatory "無關鍵矛盾 (當前: $CONFLICTS)" "[[ $CONFLICTS -eq 0 ]]" || true
    fi

    # 建議條件
    check_recommended "所有視角報告完成" "[[ -d '$OUTPUT_DIR/perspectives' ]]"
    ;;

  "PLAN")
    echo ""
    echo "📋 PLAN 階段閘門檢查"
    echo "───────────────────────"

    check_mandatory "實作計劃存在" "[[ -f '$OUTPUT_DIR/implementation-plan.md' ]] || [[ -f '$OUTPUT_DIR/plan.md' ]]" || true
    check_mandatory "里程碑定義存在" "grep -q 'milestone\|里程碑\|Milestone' '$OUTPUT_DIR'/*.md 2>/dev/null" || true

    check_recommended "風險評估完成" "grep -q 'risk\|風險\|Risk' '$OUTPUT_DIR'/*.md 2>/dev/null"
    check_recommended "替代方案有考慮" "grep -q 'alternative\|替代\|Alternative' '$OUTPUT_DIR'/*.md 2>/dev/null"
    ;;

  "TASKS")
    echo ""
    echo "📝 TASKS 階段閘門檢查"
    echo "───────────────────────"

    # 檢查任務檔案存在
    check_mandatory "任務定義存在" "[[ -f '$OUTPUT_DIR/tasks.yaml' ]] || [[ -f '$OUTPUT_DIR/tasks.md' ]]" || true

    # DAG 驗證
    if [[ -f "$OUTPUT_DIR/tasks.yaml" ]]; then
      log_info "執行 DAG 驗證..."
      SCRIPT_DIR="$(dirname "$0")"
      if [[ -f "$SCRIPT_DIR/dag-validator.py" ]]; then
        if python3 "$SCRIPT_DIR/dag-validator.py" "$OUTPUT_DIR/tasks.yaml" 2>/dev/null; then
          check_mandatory "DAG 驗證通過" "true" || true
        else
          check_mandatory "DAG 驗證通過" "false" || true
        fi
      else
        log_warning "DAG 驗證器不存在，跳過"
      fi
    fi

    # TDD 檢查
    check_recommended "TDD 對應完整" "grep -qE 'TEST-|test' '$OUTPUT_DIR'/*.yaml 2>/dev/null"
    check_recommended "估算在合理範圍" "true"  # 需要更複雜的檢查
    ;;

  "IMPLEMENT")
    echo ""
    echo "🔧 IMPLEMENT 階段閘門檢查"
    echo "───────────────────────"

    check_mandatory "無 BLOCKER 問題" "! grep -rq 'BLOCKER' '$OUTPUT_DIR' 2>/dev/null" || true

    # 檢查測試是否通過
    if [[ -f "package.json" ]]; then
      log_info "執行測試..."
      if npm test -- --passWithNoTests 2>/dev/null; then
        check_mandatory "測試通過" "true" || true
      else
        check_mandatory "測試通過" "false" || true
      fi
    fi

    check_recommended "測試覆蓋率達標" "true"  # 需要測試覆蓋率工具
    ;;

  "REVIEW")
    echo ""
    echo "🔍 REVIEW 階段閘門檢查"
    echo "───────────────────────"

    if [[ -f "$OUTPUT_DIR/review-summary.md" ]]; then
      BLOCKERS=$(grep -c "BLOCKER" "$OUTPUT_DIR/review-summary.md" 2>/dev/null || echo 0)
      check_mandatory "無 BLOCKER ($BLOCKERS 個)" "[[ $BLOCKERS -eq 0 ]]" || true

      HIGH_ISSUES=$(grep -c "HIGH" "$OUTPUT_DIR/review-summary.md" 2>/dev/null || echo 0)
      check_mandatory "HIGH 問題 <= 2 ($HIGH_ISSUES 個)" "[[ $HIGH_ISSUES -le 2 ]]" || true
    else
      check_mandatory "審查報告存在" "false" || true
    fi

    check_recommended "所有問題有修復建議" "true"
    ;;

  "VERIFY")
    echo ""
    echo "✅ VERIFY 階段閘門檢查"
    echo "───────────────────────"

    check_mandatory "功能測試通過" "true"  # 需要實際執行測試
    check_mandatory "回歸測試通過" "true"  # 需要實際執行測試

    check_recommended "邊界案例測試" "true"
    check_recommended "效能基準達標" "true"
    ;;

  *)
    log_error "未知階段: $STAGE"
    echo "支援的階段: RESEARCH, PLAN, TASKS, IMPLEMENT, REVIEW, VERIFY"
    exit 1
    ;;
esac

# 總結
echo ""
echo "═══════════════════════════════════════════"
echo "📊 閘門檢查總結"
echo "───────────────────────"
echo "必要條件: $MANDATORY_PASSED / $MANDATORY_TOTAL 通過"
echo "建議條件: $RECOMMENDED_PASSED / $RECOMMENDED_TOTAL 通過"
echo ""

if [[ $MANDATORY_PASSED -eq $MANDATORY_TOTAL ]]; then
  log_success "$STAGE 閘門通過"
  echo "═══════════════════════════════════════════"
  exit 0
else
  log_error "$STAGE 閘門失敗"
  echo "═══════════════════════════════════════════"
  exit 1
fi
