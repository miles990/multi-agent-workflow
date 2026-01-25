#!/bin/bash
# Context 監控與自動壓縮
# 用法: ./context-monitor.sh [current_tokens]

CURRENT_TOKENS=${1:-0}
THRESHOLD=${THRESHOLD:-80000}  # tokens
WARNING_THRESHOLD=$((THRESHOLD * 70 / 100))
CRITICAL_THRESHOLD=$((THRESHOLD * 85 / 100))

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "═══════════════════════════════════════════"
echo "📊 Context 監控"
echo "═══════════════════════════════════════════"

usage_percent=$((CURRENT_TOKENS * 100 / THRESHOLD))

echo "當前使用: $CURRENT_TOKENS tokens"
echo "閾值上限: $THRESHOLD tokens"
echo "使用率: ${usage_percent}%"

# 視覺化進度條
bar_length=40
filled=$((usage_percent * bar_length / 100))
empty=$((bar_length - filled))

printf "["
if [[ $usage_percent -ge 85 ]]; then
  printf "${RED}"
elif [[ $usage_percent -ge 70 ]]; then
  printf "${YELLOW}"
else
  printf "${GREEN}"
fi

for ((i=0; i<filled; i++)); do printf "█"; done
printf "${NC}"
for ((i=0; i<empty; i++)); do printf "░"; done
printf "] %d%%\n" $usage_percent

echo ""

# 狀態判斷
if [[ $CURRENT_TOKENS -ge $THRESHOLD ]]; then
  echo -e "${RED}❌ CRITICAL: Context 已滿！${NC}"
  echo "建議動作:"
  echo "  1. 立即壓縮歷史對話"
  echo "  2. 移除已完成階段的詳細內容"
  echo "  3. 只保留關鍵決策"
  exit 2

elif [[ $CURRENT_TOKENS -ge $CRITICAL_THRESHOLD ]]; then
  echo -e "${YELLOW}⚠️  WARNING: Context 使用率過高 (${usage_percent}%)${NC}"
  echo "建議動作:"
  echo "  1. 考慮壓縮歷史對話"
  echo "  2. 準備分塊處理"
  exit 1

elif [[ $CURRENT_TOKENS -ge $WARNING_THRESHOLD ]]; then
  echo -e "${YELLOW}⚠️  NOTICE: Context 使用中等 (${usage_percent}%)${NC}"
  echo "狀態: 持續監控"
  exit 0

else
  echo -e "${GREEN}✅ OK: Context 使用正常${NC}"
  echo "剩餘空間: $((THRESHOLD - CURRENT_TOKENS)) tokens"
  exit 0
fi
