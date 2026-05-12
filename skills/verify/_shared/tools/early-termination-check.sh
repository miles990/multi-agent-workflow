#!/bin/bash
# 早期終止檢查器 - 判斷是否可以提前結束
# 用法: ./early-termination-check.sh <STAGE> <METRICS_FILE>

STAGE=$1
METRICS_FILE=$2

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [[ -z "$STAGE" ]]; then
  echo "用法: $0 <STAGE> [METRICS_FILE]"
  exit 1
fi

echo "🔍 早期終止檢查: $STAGE"

# 從 metrics 檔案讀取值（如果存在）
get_metric() {
  local key=$1
  local default=$2

  if [[ -f "$METRICS_FILE" ]]; then
    value=$(grep "^$key:" "$METRICS_FILE" 2>/dev/null | cut -d: -f2 | tr -d ' ')
    echo "${value:-$default}"
  else
    echo "$default"
  fi
}

case $STAGE in
  "RESEARCH")
    CONSENSUS_RATE=$(get_metric "consensus_rate" "0")

    # 使用 awk 進行浮點數比較
    if awk "BEGIN {exit !($CONSENSUS_RATE >= 0.9)}"; then
      echo -e "${GREEN}EARLY_STOP:skip_conflict_resolution${NC}"
      echo "原因: 共識率 $CONSENSUS_RATE >= 0.9，跳過衝突解決"
      exit 0
    fi
    ;;

  "PLAN")
    RISK_SCORE=$(get_metric "risk_score" "1")

    if awk "BEGIN {exit !($RISK_SCORE < 0.2)}"; then
      echo -e "${GREEN}EARLY_STOP:use_quick_mode${NC}"
      echo "原因: 風險分數 $RISK_SCORE < 0.2，使用快速模式"
      exit 0
    fi
    ;;

  "REVIEW")
    BLOCKER_COUNT=$(get_metric "blocker_count" "0")
    HIGH_COUNT=$(get_metric "high_issue_count" "0")

    if [[ "$BLOCKER_COUNT" -eq 0 && "$HIGH_COUNT" -eq 0 ]]; then
      echo -e "${GREEN}EARLY_STOP:approve_immediately${NC}"
      echo "原因: 無 BLOCKER 和 HIGH 問題，直接通過"
      exit 0
    fi
    ;;

  "VERIFY")
    PASS_RATE=$(get_metric "first_pass_rate" "0")

    if awk "BEGIN {exit !($PASS_RATE >= 0.98)}"; then
      echo -e "${GREEN}EARLY_STOP:ship_it${NC}"
      echo "原因: 首次通過率 $PASS_RATE >= 98%，可以發布"
      exit 0
    fi
    ;;

  *)
    echo -e "${YELLOW}未知階段: $STAGE${NC}"
    ;;
esac

echo "CONTINUE"
echo "原因: 不滿足早期終止條件"
exit 0
