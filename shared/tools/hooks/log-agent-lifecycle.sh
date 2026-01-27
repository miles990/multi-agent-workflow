#!/bin/bash
# =============================================================================
# log-agent-lifecycle.sh - SubagentStart/SubagentStop Hook
#
# 位置: ~/.claude/hooks/log-agent-lifecycle.sh
# 用途: 記錄 Subagent 生命週期事件
#
# 使用方式:
#   SubagentStart: LIFECYCLE_EVENT=start ./log-agent-lifecycle.sh
#   SubagentStop:  LIFECYCLE_EVENT=stop ./log-agent-lifecycle.sh
# =============================================================================

set -euo pipefail

# 配置
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
WORKFLOW_BASE="${PROJECT_DIR}/.claude/workflow"
CURRENT_FILE="${WORKFLOW_BASE}/current.json"

# 事件類型（start 或 stop）
LIFECYCLE_EVENT="${LIFECYCLE_EVENT:-start}"

# 決定日誌位置（支援 fallback 到通用日誌）
WORKFLOW_ID=""
HAS_WORKFLOW=false
if [ -f "$CURRENT_FILE" ]; then
    WORKFLOW_ID=$(jq -r '.workflow_id // ""' "$CURRENT_FILE" 2>/dev/null || echo "")
fi

if [ -n "$WORKFLOW_ID" ]; then
    # 有活躍的 workflow
    HAS_WORKFLOW=true
    WORKFLOW_DIR="${WORKFLOW_BASE}/${WORKFLOW_ID}"
    LOG_FILE="${WORKFLOW_DIR}/logs/events.jsonl"
    AGENTS_FILE="${WORKFLOW_DIR}/state/agents.json"
    ERROR_DIR="${WORKFLOW_DIR}/logs"
else
    # 沒有活躍的 workflow，記錄到通用日誌（fallback）
    WORKFLOW_ID="general"
    LOG_FILE="${PROJECT_DIR}/.claude/logs/events.jsonl"
    AGENTS_FILE=""  # 沒有 agents 狀態檔案
    ERROR_DIR="${PROJECT_DIR}/.claude/logs"
fi

# 確保目錄存在
mkdir -p "$(dirname "$LOG_FILE")"

# 生成事件 ID
EVENT_ID="evt_$(date +%Y%m%d_%H%M%S)_$(openssl rand -hex 3 2>/dev/null || echo $$)"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)

# 獲取 Subagent 資訊
SUBAGENT_ID="${CLAUDE_SUBAGENT_ID:-unknown}"
SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"

if [ "$LIFECYCLE_EVENT" = "start" ]; then
    # SubagentStart 事件

    # 提取 prompt 摘要
    PROMPT="${CLAUDE_SUBAGENT_PROMPT:-}"
    PROMPT_PREVIEW=""
    if [ ${#PROMPT} -gt 200 ]; then
        PROMPT_PREVIEW=$(echo "$PROMPT" | head -c 200)"..."
    else
        PROMPT_PREVIEW="$PROMPT"
    fi

    # 嘗試從 prompt 提取視角資訊
    PERSPECTIVE="unknown"
    if echo "$PROMPT" | grep -qi "architecture\|架構"; then
        PERSPECTIVE="architecture"
    elif echo "$PROMPT" | grep -qi "cognitive\|認知"; then
        PERSPECTIVE="cognitive"
    elif echo "$PROMPT" | grep -qi "workflow\|工作流"; then
        PERSPECTIVE="workflow"
    elif echo "$PROMPT" | grep -qi "industry\|產業"; then
        PERSPECTIVE="industry"
    elif echo "$PROMPT" | grep -qi "risk\|風險"; then
        PERSPECTIVE="risk"
    fi

    # 構建事件記錄
    EVENT=$(jq -n \
        --arg id "$EVENT_ID" \
        --arg ts "$TIMESTAMP" \
        --arg session "$SESSION_ID" \
        --arg workflow "$WORKFLOW_ID" \
        --arg agent "$SUBAGENT_ID" \
        --arg perspective "$PERSPECTIVE" \
        --arg prompt "$PROMPT_PREVIEW" \
        '{
            id: $id,
            timestamp: $ts,
            session_id: $session,
            workflow_id: $workflow,
            event_type: "agent_start",
            agent_id: $agent,
            data: {
                perspective: $perspective,
                prompt_preview: $prompt
            },
            status: "started"
        }')

    # 更新 agents.json（如果存在且有活躍的 workflow）
    if [ "$HAS_WORKFLOW" = true ] && [ -n "$AGENTS_FILE" ] && [ -f "$AGENTS_FILE" ]; then
        TMP_FILE=$(mktemp)
        jq --arg id "$SUBAGENT_ID" \
           --arg perspective "$PERSPECTIVE" \
           --arg ts "$TIMESTAMP" \
           '.agents[$id] = {
             "perspective": $perspective,
             "status": "running",
             "started_at": $ts,
             "last_heartbeat": $ts
           }' "$AGENTS_FILE" > "$TMP_FILE" && mv "$TMP_FILE" "$AGENTS_FILE"
    fi

    # 保存啟動時間供 stop hook 計算 duration
    TMP_DIR="/tmp/claude_hooks"
    mkdir -p "$TMP_DIR"
    echo "$TIMESTAMP" > "${TMP_DIR}/agent_start_${SUBAGENT_ID}.ts"

else
    # SubagentStop 事件

    EXIT_CODE="${CLAUDE_SUBAGENT_EXIT_CODE:-0}"

    # 判斷狀態
    if [ "$EXIT_CODE" = "0" ]; then
        STATUS="completed"
    else
        STATUS="failed"
    fi

    # 計算 duration
    DURATION_MS=0
    TMP_FILE="/tmp/claude_hooks/agent_start_${SUBAGENT_ID}.ts"
    if [ -f "$TMP_FILE" ]; then
        START_TIME=$(cat "$TMP_FILE")
        # 計算時間差（簡化版，假設在同一天內）
        START_EPOCH=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${START_TIME%.*}" +%s 2>/dev/null || echo 0)
        NOW_EPOCH=$(date +%s)
        DURATION_MS=$(( (NOW_EPOCH - START_EPOCH) * 1000 ))
        rm -f "$TMP_FILE"
    fi

    # 構建事件記錄
    EVENT=$(jq -n \
        --arg id "$EVENT_ID" \
        --arg ts "$TIMESTAMP" \
        --arg session "$SESSION_ID" \
        --arg workflow "$WORKFLOW_ID" \
        --arg agent "$SUBAGENT_ID" \
        --argjson exit_code "$EXIT_CODE" \
        --argjson duration "$DURATION_MS" \
        --arg status "$STATUS" \
        '{
            id: $id,
            timestamp: $ts,
            session_id: $session,
            workflow_id: $workflow,
            event_type: "agent_stop",
            agent_id: $agent,
            data: {
                exit_code: $exit_code
            },
            duration_ms: $duration,
            status: $status
        }')

    # 更新 agents.json（如果存在且有活躍的 workflow）
    if [ "$HAS_WORKFLOW" = true ] && [ -n "$AGENTS_FILE" ] && [ -f "$AGENTS_FILE" ]; then
        TMP_FILE=$(mktemp)
        jq --arg id "$SUBAGENT_ID" \
           --arg status "$STATUS" \
           --arg ts "$TIMESTAMP" \
           '.agents[$id].status = $status | .agents[$id].stopped_at = $ts' \
           "$AGENTS_FILE" > "$TMP_FILE" && mv "$TMP_FILE" "$AGENTS_FILE"
    fi

    # 如果失敗，記錄錯誤
    if [ "$STATUS" = "failed" ]; then
        ERROR_FILE="${ERROR_DIR}/errors.jsonl"
        mkdir -p "$ERROR_DIR"
        ERROR=$(jq -n \
            --arg id "err_$(date +%Y%m%d_%H%M%S)_$(openssl rand -hex 3 2>/dev/null || echo $$)" \
            --arg ts "$TIMESTAMP" \
            --arg workflow "$WORKFLOW_ID" \
            --arg agent "$SUBAGENT_ID" \
            --argjson exit_code "$EXIT_CODE" \
            '{
                id: $id,
                timestamp: $ts,
                workflow_id: $workflow,
                error_type: "agent_failure",
                agent_id: $agent,
                exit_code: $exit_code,
                message: "Subagent terminated with non-zero exit code"
            }')
        echo "$ERROR" >> "$ERROR_FILE"
    fi
fi

# 追加到日誌
echo "$EVENT" >> "$LOG_FILE"

exit 0
