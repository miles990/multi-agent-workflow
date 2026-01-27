#!/bin/bash
# =============================================================================
# log-tool-pre.sh - PreToolUse Hook
#
# 位置: ~/.claude/hooks/log-tool-pre.sh
# 用途: 記錄工具呼叫前的狀態
# =============================================================================

set -euo pipefail

# 配置
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
WORKFLOW_BASE="${PROJECT_DIR}/.claude/workflow"
CURRENT_FILE="${WORKFLOW_BASE}/current.json"

# 決定日誌位置（支援 fallback 到通用日誌）
WORKFLOW_ID=""
if [ -f "$CURRENT_FILE" ]; then
    WORKFLOW_ID=$(jq -r '.workflow_id // ""' "$CURRENT_FILE" 2>/dev/null || echo "")
fi

if [ -n "$WORKFLOW_ID" ]; then
    # 有活躍的 workflow，記錄到該 workflow 目錄
    WORKFLOW_DIR="${WORKFLOW_BASE}/${WORKFLOW_ID}"
    LOG_FILE="${WORKFLOW_DIR}/logs/events.jsonl"
else
    # 沒有活躍的 workflow，記錄到通用日誌（fallback）
    WORKFLOW_ID="general"
    LOG_FILE="${PROJECT_DIR}/.claude/logs/events.jsonl"
fi

# 確保目錄存在
mkdir -p "$(dirname "$LOG_FILE")"

# 生成事件 ID
EVENT_ID="evt_$(date +%Y%m%d_%H%M%S)_$(openssl rand -hex 3 2>/dev/null || echo $$)"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)

# 獲取工具資訊
TOOL_NAME="${CLAUDE_TOOL_NAME:-unknown}"
SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"

# 安全處理 JSON 輸入
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-{}}"
# 驗證是否為有效 JSON
if ! echo "$TOOL_INPUT" | jq empty 2>/dev/null; then
    TOOL_INPUT='{"raw":"invalid_json"}'
fi

# 對於某些高頻工具，跳過記錄以優化效能
case "$TOOL_NAME" in
    Read|Glob|Grep)
        # 可選：跳過讀取類操作
        # exit 0
        ;;
esac

# 截斷過長的輸入
INPUT_LENGTH=${#TOOL_INPUT}
if [ $INPUT_LENGTH -gt 1000 ]; then
    TOOL_INPUT=$(echo "$TOOL_INPUT" | jq -c '{truncated: true, length: '$INPUT_LENGTH', preview: (.[:500] + "...")}' 2>/dev/null || echo '{"truncated":true}')
fi

# 構建事件記錄
EVENT=$(jq -n \
    --arg id "$EVENT_ID" \
    --arg ts "$TIMESTAMP" \
    --arg session "$SESSION_ID" \
    --arg workflow "$WORKFLOW_ID" \
    --arg tool "$TOOL_NAME" \
    --argjson input "$TOOL_INPUT" \
    '{
        id: $id,
        timestamp: $ts,
        session_id: $session,
        workflow_id: $workflow,
        event_type: "tool_call",
        phase: "pre",
        tool_name: $tool,
        data: $input,
        status: "pending"
    }')

# 追加到日誌（原子操作）
echo "$EVENT" >> "$LOG_FILE"

# 保存事件 ID 供 post hook 使用
TMP_DIR="/tmp/claude_hooks"
mkdir -p "$TMP_DIR"
echo "$EVENT_ID" > "${TMP_DIR}/last_event_${SESSION_ID}.id"

exit 0
