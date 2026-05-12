#!/bin/bash
# =============================================================================
# log-tool-post.sh - PostToolUse Hook
#
# 位置: ~/.claude/hooks/log-tool-post.sh
# 用途: 記錄工具呼叫後的結果
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/dependency-utils.sh" ]; then
    # shellcheck source=dependency-utils.sh
    source "${SCRIPT_DIR}/dependency-utils.sh"
elif [ -f "${SCRIPT_DIR}/../dependency-utils.sh" ]; then
    # shellcheck source=../dependency-utils.sh
    source "${SCRIPT_DIR}/../dependency-utils.sh"
fi

if declare -f maw_ensure_command >/dev/null 2>&1; then
    maw_ensure_command jq jq || exit 0
else
    command -v jq >/dev/null 2>&1 || exit 0
fi

if ! declare -f maw_random_hex >/dev/null 2>&1; then
    maw_random_hex() {
        local bytes="${1:-3}"
        openssl rand -hex "$bytes" 2>/dev/null || printf '%s' "$(date +%s)$$"
    }
fi

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
    ERROR_DIR="${WORKFLOW_DIR}/logs"
else
    # 沒有活躍的 workflow，記錄到通用日誌（fallback）
    WORKFLOW_ID="general"
    LOG_FILE="${PROJECT_DIR}/.claude/logs/events.jsonl"
    ERROR_DIR="${PROJECT_DIR}/.claude/logs"
fi

# 確保目錄存在
mkdir -p "$(dirname "$LOG_FILE")"

# 生成事件 ID
EVENT_ID="evt_$(date +%Y%m%d_%H%M%S)_$(maw_random_hex 3)"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)

# 獲取工具資訊
TOOL_NAME="${CLAUDE_TOOL_NAME:-unknown}"
SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"
EXIT_CODE="${CLAUDE_TOOL_EXIT_CODE:-0}"
DURATION_MS="${CLAUDE_TOOL_DURATION_MS:-0}"

# 判斷狀態
if [ "$EXIT_CODE" = "0" ]; then
    STATUS="success"
else
    STATUS="failed"
fi

# 處理輸出（截斷以避免日誌過大）
TOOL_OUTPUT="${CLAUDE_TOOL_OUTPUT:-}"
OUTPUT_LENGTH=${#TOOL_OUTPUT}
OUTPUT_SUMMARY=""

if [ $OUTPUT_LENGTH -gt 500 ]; then
    OUTPUT_SUMMARY="[truncated: ${OUTPUT_LENGTH} chars]"
elif [ $OUTPUT_LENGTH -gt 0 ]; then
    # 安全處理：移除可能破壞 JSON 的字元
    OUTPUT_SUMMARY=$(echo "$TOOL_OUTPUT" | tr -d '\000-\037' | head -c 500 || echo "")
fi

# 讀取關聯的 pre-event ID（如果存在）
PRE_EVENT_ID=""
TMP_FILE="/tmp/claude_hooks/last_event_${SESSION_ID}.id"
if [ -f "$TMP_FILE" ]; then
    PRE_EVENT_ID=$(cat "$TMP_FILE" 2>/dev/null || echo "")
    rm -f "$TMP_FILE"
fi

# 構建事件記錄
EVENT=$(jq -c -n \
    --arg id "$EVENT_ID" \
    --arg ts "$TIMESTAMP" \
    --arg session "$SESSION_ID" \
    --arg workflow "$WORKFLOW_ID" \
    --arg tool "$TOOL_NAME" \
    --arg output "$OUTPUT_SUMMARY" \
    --argjson exit_code "$EXIT_CODE" \
    --argjson duration "$DURATION_MS" \
    --arg status "$STATUS" \
    --arg pre_id "$PRE_EVENT_ID" \
    '{
        id: $id,
        timestamp: $ts,
        session_id: $session,
        workflow_id: $workflow,
        event_type: "tool_call",
        phase: "post",
        tool_name: $tool,
        data: {
            output_length: ($output | length),
            output_preview: (if ($output | length) > 0 then $output else null end),
            exit_code: $exit_code
        },
        duration_ms: $duration,
        status: $status,
        related_event: (if $pre_id != "" then $pre_id else null end)
    }')

# 追加到日誌
echo "$EVENT" >> "$LOG_FILE"

# 如果失敗，同時記錄到錯誤日誌
if [ "$STATUS" = "failed" ]; then
    ERROR_FILE="${ERROR_DIR}/errors.jsonl"
    mkdir -p "$ERROR_DIR"
    ERROR=$(jq -c -n \
        --arg id "err_$(date +%Y%m%d_%H%M%S)_$(maw_random_hex 3)" \
        --arg ts "$TIMESTAMP" \
        --arg workflow "$WORKFLOW_ID" \
        --arg tool "$TOOL_NAME" \
        --argjson exit_code "$EXIT_CODE" \
        --arg output "$OUTPUT_SUMMARY" \
        '{
            id: $id,
            timestamp: $ts,
            workflow_id: $workflow,
            error_type: "tool_failure",
            tool_name: $tool,
            exit_code: $exit_code,
            message: $output
        }')
    echo "$ERROR" >> "$ERROR_FILE"
fi

exit 0
