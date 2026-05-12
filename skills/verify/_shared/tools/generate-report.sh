#!/bin/bash
# 報告生成器 - 生成完整的人類友好報告
# 用法: ./generate-report.sh <WORKFLOW_ID>

set -e

WORKFLOW_ID=$1
SCRIPT_DIR="$(dirname "$0")"
OUTPUT_DIR=".claude/memory/workflows/$WORKFLOW_ID"

# 顏色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

if [[ -z "$WORKFLOW_ID" ]]; then
  echo "用法: $0 <WORKFLOW_ID>"
  echo "範例: $0 wf-20260125-001"
  exit 1
fi

echo "═══════════════════════════════════════════"
echo "📊 生成工作流報告"
echo "工作流 ID: $WORKFLOW_ID"
echo "輸出目錄: $OUTPUT_DIR"
echo "═══════════════════════════════════════════"

# 確保輸出目錄存在
mkdir -p "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/stages"
mkdir -p "$OUTPUT_DIR/agents"
mkdir -p "$OUTPUT_DIR/tools"
mkdir -p "$OUTPUT_DIR/exports"

# 1. 生成 Dashboard
echo -e "${BLUE}📋 生成 Dashboard...${NC}"
if [[ -f "$SCRIPT_DIR/generate-dashboard.py" ]]; then
  python3 "$SCRIPT_DIR/generate-dashboard.py" "$OUTPUT_DIR"
else
  echo "  (跳過: generate-dashboard.py 不存在)"
fi

# 2. 生成時間線
echo -e "${BLUE}📅 生成時間線...${NC}"
if [[ -f "$SCRIPT_DIR/generate-timeline.py" ]]; then
  python3 "$SCRIPT_DIR/generate-timeline.py" "$OUTPUT_DIR"
else
  echo "  (跳過: generate-timeline.py 不存在)"
fi

# 3. 生成品質報告
echo -e "${BLUE}📊 生成品質報告...${NC}"
if [[ -f "$SCRIPT_DIR/generate-quality-report.py" ]]; then
  python3 "$SCRIPT_DIR/generate-quality-report.py" "$OUTPUT_DIR"
else
  echo "  (跳過: generate-quality-report.py 不存在)"
fi

# 4. 計算統計
echo -e "${BLUE}📈 計算統計指標...${NC}"
if [[ -f "$SCRIPT_DIR/calculate-metrics.py" ]]; then
  python3 "$SCRIPT_DIR/calculate-metrics.py" "$OUTPUT_DIR"
else
  echo "  (跳過: calculate-metrics.py 不存在)"
fi

# 5. 生成 PDF（可選）
if command -v pandoc &> /dev/null; then
  echo -e "${BLUE}📄 生成 PDF 報告...${NC}"
  if [[ -f "$OUTPUT_DIR/dashboard.md" ]]; then
    pandoc "$OUTPUT_DIR/dashboard.md" \
      -o "$OUTPUT_DIR/exports/full-report.pdf" \
      --pdf-engine=xelatex \
      -V mainfont="PingFang SC" 2>/dev/null || \
    pandoc "$OUTPUT_DIR/dashboard.md" \
      -o "$OUTPUT_DIR/exports/full-report.pdf" 2>/dev/null || \
    echo "  (PDF 生成失敗，但 Markdown 報告可用)"
  fi
else
  echo "  (跳過 PDF: pandoc 未安裝)"
fi

echo ""
echo -e "${GREEN}✅ 報告生成完成${NC}"
echo ""
echo "報告位置:"
echo "  - Dashboard: $OUTPUT_DIR/dashboard.md"
echo "  - 時間線: $OUTPUT_DIR/timeline.md"
echo "  - 品質報告: $OUTPUT_DIR/quality-report.md"
if [[ -f "$OUTPUT_DIR/exports/full-report.pdf" ]]; then
  echo "  - PDF: $OUTPUT_DIR/exports/full-report.pdf"
fi
echo "═══════════════════════════════════════════"
