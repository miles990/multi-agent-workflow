#!/bin/bash
# Token 計算器 - 評估 Prompt 瘦身效果
# 用法: ./token-counter.sh <SKILL_DIR>

SKILL_DIR=${1:-.}

echo "═══════════════════════════════════════════"
echo "📊 Token 使用量分析"
echo "目錄: $SKILL_DIR"
echo "═══════════════════════════════════════════"

total_chars=0
total_lines=0
file_count=0

# 遍歷所有 .md 和 .yaml 檔案
while IFS= read -r -d '' file; do
  if [[ -f "$file" ]]; then
    chars=$(wc -c < "$file" | tr -d ' ')
    lines=$(wc -l < "$file" | tr -d ' ')
    tokens=$((chars / 4))  # 粗略估算：4 字元 ≈ 1 token

    # 相對路徑
    rel_path="${file#$SKILL_DIR/}"

    printf "%-50s %6d tokens (%4d 行)\n" "$rel_path" "$tokens" "$lines"

    total_chars=$((total_chars + chars))
    total_lines=$((total_lines + lines))
    ((file_count++))
  fi
done < <(find "$SKILL_DIR" -type f \( -name "*.md" -o -name "*.yaml" -o -name "*.yml" \) -print0 2>/dev/null)

total_tokens=$((total_chars / 4))

echo ""
echo "───────────────────────────────────────────"
echo "總計: $file_count 個檔案"
echo "總字元: $total_chars"
echo "總行數: $total_lines"
echo "估算 Token: ~$total_tokens"

# 與基準比較
BASELINE=${BASELINE:-150000}
if [[ $BASELINE -gt 0 ]]; then
  SAVINGS=$(( (BASELINE - total_tokens) * 100 / BASELINE ))
  echo ""
  echo "📈 與基準 ($BASELINE tokens) 比較:"
  if [[ $SAVINGS -gt 0 ]]; then
    echo "   節省: ${SAVINGS}%"
  else
    echo "   增加: $((-SAVINGS))%"
  fi
fi

echo "═══════════════════════════════════════════"
