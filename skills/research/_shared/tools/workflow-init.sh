#!/bin/bash
# =============================================================================
# workflow-init.sh - Workflow 通訊環境初始化
#
# 位置: ~/.claude/hooks/workflow-init.sh 或 shared/tools/workflow-init.sh
# 用途: 為多 Agent 工作流創建通訊基礎設施
# =============================================================================

set -euo pipefail

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 版本
VERSION="1.0.0"

# 預設值
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
WORKFLOW_BASE="${PROJECT_DIR}/.claude/workflow"

#######################################
# 輔助函數
#######################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

generate_id() {
    local prefix="${1:-wf}"
    echo "${prefix}_$(date +%Y%m%d_%H%M%S)_$(openssl rand -hex 4)"
}

#######################################
# 初始化 Workflow 目錄結構
#######################################

init_workflow() {
    local workflow_id="${1:-$(generate_id 'workflow')}"
    local workflow_type="${2:-research}"
    local topic="${3:-default}"

    log_info "初始化 Workflow: ${workflow_id}"

    local workflow_dir="${WORKFLOW_BASE}/${workflow_id}"

    # 創建目錄結構
    mkdir -p "${workflow_dir}/channel/agents"
    mkdir -p "${workflow_dir}/state/heartbeat"
    mkdir -p "${workflow_dir}/logs"

    log_success "創建目錄結構"

    # 初始化 agents.json
    cat > "${workflow_dir}/state/agents.json" << EOF
{
  "workflow_id": "${workflow_id}",
  "workflow_type": "${workflow_type}",
  "topic": "${topic}",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)",
  "status": "initializing",
  "agents": {}
}
EOF
    log_success "初始化 agents.json"

    # 創建空的通訊頻道
    touch "${workflow_dir}/channel/broadcast.jsonl"
    touch "${workflow_dir}/channel/orchestrator.jsonl"
    log_success "創建通訊頻道"

    # 創建空的日誌檔案
    touch "${workflow_dir}/logs/events.jsonl"
    touch "${workflow_dir}/logs/errors.jsonl"
    log_success "創建日誌檔案"

    # 設置當前 workflow
    cat > "${WORKFLOW_BASE}/current.json" << EOF
{
  "workflow_id": "${workflow_id}",
  "workflow_dir": "${workflow_dir}",
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"
}
EOF
    log_success "設置為當前 workflow"

    echo ""
    echo -e "${GREEN}Workflow 初始化完成${NC}"
    echo "  ID: ${workflow_id}"
    echo "  目錄: ${workflow_dir}"

    echo "${workflow_id}"
}

#######################################
# 註冊 Agent
#######################################

register_agent() {
    local agent_id="${1}"
    local perspective="${2:-unknown}"
    local workflow_id="${3:-}"

    # 如果未指定 workflow_id，使用當前的
    if [ -z "$workflow_id" ] && [ -f "${WORKFLOW_BASE}/current.json" ]; then
        workflow_id=$(jq -r '.workflow_id' "${WORKFLOW_BASE}/current.json")
    fi

    if [ -z "$workflow_id" ]; then
        log_error "無法確定 workflow ID"
        return 1
    fi

    local workflow_dir="${WORKFLOW_BASE}/${workflow_id}"
    local agents_file="${workflow_dir}/state/agents.json"

    if [ ! -f "$agents_file" ]; then
        log_error "Workflow 不存在: ${workflow_id}"
        return 1
    fi

    # 創建 Agent 訊息佇列
    touch "${workflow_dir}/channel/agents/${agent_id}.jsonl"
    touch "${workflow_dir}/channel/agents/${agent_id}.ack"

    # 更新 agents.json
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)
    local tmp_file=$(mktemp)

    jq --arg id "$agent_id" \
       --arg perspective "$perspective" \
       --arg ts "$timestamp" \
       '.agents[$id] = {
         "perspective": $perspective,
         "status": "registered",
         "registered_at": $ts,
         "last_heartbeat": $ts
       }' "$agents_file" > "$tmp_file" && mv "$tmp_file" "$agents_file"

    log_success "Agent 註冊完成: ${agent_id} (${perspective})"
}

#######################################
# 發送訊息
#######################################

send_message() {
    local to="${1}"
    local msg_type="${2}"
    local payload="${3:-{}}"
    local workflow_id="${4:-}"
    local from="${5:-orchestrator}"

    # 確定 workflow
    if [ -z "$workflow_id" ] && [ -f "${WORKFLOW_BASE}/current.json" ]; then
        workflow_id=$(jq -r '.workflow_id' "${WORKFLOW_BASE}/current.json")
    fi

    local workflow_dir="${WORKFLOW_BASE}/${workflow_id}"

    # 生成訊息 ID
    local msg_id=$(generate_id 'msg')
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)

    # 判斷是否需要 ACK
    local requires_ack="false"
    case "$msg_type" in
        task_assign|checkpoint_request|abort)
            requires_ack="true"
            ;;
    esac

    # 構建訊息
    local message=$(jq -n \
        --arg id "$msg_id" \
        --arg ts "$timestamp" \
        --arg from "$from" \
        --arg to "$to" \
        --arg type "$msg_type" \
        --argjson payload "$payload" \
        --argjson ack "$requires_ack" \
        '{
            id: $id,
            timestamp: $ts,
            from: $from,
            to: $to,
            type: $type,
            payload: $payload,
            requires_ack: $ack
        }')

    # 寫入目標佇列
    local target_file
    if [ "$to" = "broadcast" ]; then
        target_file="${workflow_dir}/channel/broadcast.jsonl"
    elif [ "$to" = "orchestrator" ]; then
        target_file="${workflow_dir}/channel/orchestrator.jsonl"
    else
        target_file="${workflow_dir}/channel/agents/${to}.jsonl"
    fi

    echo "$message" >> "$target_file"

    # 記錄事件
    local event=$(jq -n \
        --arg id "evt_$(date +%Y%m%d_%H%M%S)_$(openssl rand -hex 3)" \
        --arg ts "$timestamp" \
        --arg wf "$workflow_id" \
        --arg msg_id "$msg_id" \
        --arg from "$from" \
        --arg to "$to" \
        --arg type "$msg_type" \
        '{
            id: $id,
            timestamp: $ts,
            workflow_id: $wf,
            event_type: "message",
            data: {
                message_id: $msg_id,
                from: $from,
                to: $to,
                type: $type
            },
            status: "sent"
        }')

    echo "$event" >> "${workflow_dir}/logs/events.jsonl"

    echo "$msg_id"
}

#######################################
# 讀取訊息
#######################################

read_messages() {
    local agent_id="${1}"
    local workflow_id="${2:-}"
    local since_line="${3:-0}"

    if [ -z "$workflow_id" ] && [ -f "${WORKFLOW_BASE}/current.json" ]; then
        workflow_id=$(jq -r '.workflow_id' "${WORKFLOW_BASE}/current.json")
    fi

    local workflow_dir="${WORKFLOW_BASE}/${workflow_id}"
    local queue_file="${workflow_dir}/channel/agents/${agent_id}.jsonl"
    local broadcast_file="${workflow_dir}/channel/broadcast.jsonl"

    local messages="[]"

    # 讀取個人佇列
    if [ -f "$queue_file" ]; then
        local queue_msgs=$(tail -n +$((since_line + 1)) "$queue_file" 2>/dev/null | jq -s '.')
        messages=$(echo "$messages" | jq --argjson new "$queue_msgs" '. + $new')
    fi

    # 讀取廣播
    if [ -f "$broadcast_file" ]; then
        local broadcast_msgs=$(tail -n +$((since_line + 1)) "$broadcast_file" 2>/dev/null | jq -s '.')
        messages=$(echo "$messages" | jq --argjson new "$broadcast_msgs" '. + $new')
    fi

    echo "$messages"
}

#######################################
# 發送 ACK
#######################################

send_ack() {
    local agent_id="${1}"
    local msg_id="${2}"
    local status="${3:-received}"
    local workflow_id="${4:-}"

    if [ -z "$workflow_id" ] && [ -f "${WORKFLOW_BASE}/current.json" ]; then
        workflow_id=$(jq -r '.workflow_id' "${WORKFLOW_BASE}/current.json")
    fi

    local workflow_dir="${WORKFLOW_BASE}/${workflow_id}"
    local ack_file="${workflow_dir}/channel/agents/${agent_id}.ack"
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)

    local ack=$(jq -n \
        --arg msg_id "$msg_id" \
        --arg status "$status" \
        --arg ts "$timestamp" \
        '{msg_id: $msg_id, status: $status, at: $ts}')

    echo "$ack" >> "$ack_file"
}

#######################################
# 更新心跳
#######################################

update_heartbeat() {
    local agent_id="${1}"
    local workflow_id="${2:-}"

    if [ -z "$workflow_id" ] && [ -f "${WORKFLOW_BASE}/current.json" ]; then
        workflow_id=$(jq -r '.workflow_id' "${WORKFLOW_BASE}/current.json")
    fi

    local workflow_dir="${WORKFLOW_BASE}/${workflow_id}"
    local heartbeat_file="${workflow_dir}/state/heartbeat/${agent_id}.ts"
    local agents_file="${workflow_dir}/state/agents.json"
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)

    # 更新心跳檔案
    echo "$timestamp" > "$heartbeat_file"

    # 更新 agents.json
    local tmp_file=$(mktemp)
    jq --arg id "$agent_id" \
       --arg ts "$timestamp" \
       '.agents[$id].last_heartbeat = $ts | .agents[$id].status = "active"' \
       "$agents_file" > "$tmp_file" && mv "$tmp_file" "$agents_file"
}

#######################################
# 檢查 Agent 狀態
#######################################

check_agents_health() {
    local workflow_id="${1:-}"
    local timeout_seconds="${2:-30}"

    if [ -z "$workflow_id" ] && [ -f "${WORKFLOW_BASE}/current.json" ]; then
        workflow_id=$(jq -r '.workflow_id' "${WORKFLOW_BASE}/current.json")
    fi

    local workflow_dir="${WORKFLOW_BASE}/${workflow_id}"
    local agents_file="${workflow_dir}/state/agents.json"
    local now=$(date +%s)

    # 讀取所有 agents
    local agents=$(jq -r '.agents | keys[]' "$agents_file")

    local healthy=0
    local unhealthy=0

    for agent_id in $agents; do
        local heartbeat_file="${workflow_dir}/state/heartbeat/${agent_id}.ts"

        if [ -f "$heartbeat_file" ]; then
            local last_heartbeat=$(cat "$heartbeat_file")
            local heartbeat_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${last_heartbeat%.*}" +%s 2>/dev/null || echo 0)
            local diff=$((now - heartbeat_epoch))

            if [ $diff -gt $timeout_seconds ]; then
                log_warn "Agent ${agent_id}: 無回應 (${diff}s)"
                ((unhealthy++))

                # 更新狀態
                local tmp_file=$(mktemp)
                jq --arg id "$agent_id" \
                   '.agents[$id].status = "unresponsive"' \
                   "$agents_file" > "$tmp_file" && mv "$tmp_file" "$agents_file"
            else
                log_success "Agent ${agent_id}: 健康 (${diff}s ago)"
                ((healthy++))
            fi
        else
            log_warn "Agent ${agent_id}: 無心跳記錄"
            ((unhealthy++))
        fi
    done

    echo ""
    echo "健康: ${healthy}, 異常: ${unhealthy}"

    [ $unhealthy -eq 0 ]
}

#######################################
# 清理 Workflow
#######################################

cleanup_workflow() {
    local workflow_id="${1}"
    local archive="${2:-true}"

    local workflow_dir="${WORKFLOW_BASE}/${workflow_id}"

    if [ ! -d "$workflow_dir" ]; then
        log_error "Workflow 不存在: ${workflow_id}"
        return 1
    fi

    if [ "$archive" = "true" ]; then
        local archive_dir="${WORKFLOW_BASE}/archive"
        mkdir -p "$archive_dir"

        local archive_file="${archive_dir}/${workflow_id}.tar.gz"
        tar -czf "$archive_file" -C "${WORKFLOW_BASE}" "${workflow_id}"
        log_success "已歸檔: ${archive_file}"
    fi

    rm -rf "$workflow_dir"
    log_success "已刪除: ${workflow_dir}"

    # 如果是當前 workflow，清除 current.json
    if [ -f "${WORKFLOW_BASE}/current.json" ]; then
        local current=$(jq -r '.workflow_id' "${WORKFLOW_BASE}/current.json")
        if [ "$current" = "$workflow_id" ]; then
            rm "${WORKFLOW_BASE}/current.json"
            log_info "已清除當前 workflow 設定"
        fi
    fi
}

#######################################
# 主函數
#######################################

usage() {
    cat << EOF
Workflow 通訊環境管理工具 v${VERSION}

用法: $(basename "$0") <command> [options]

Commands:
  init [id] [type] [topic]     初始化新的 workflow
  register <agent_id> [perspective]  註冊 Agent
  send <to> <type> [payload]   發送訊息
  read <agent_id>              讀取訊息
  ack <agent_id> <msg_id>      發送 ACK
  heartbeat <agent_id>         更新心跳
  health                       檢查 agents 健康狀態
  cleanup <workflow_id>        清理 workflow

範例:
  $(basename "$0") init research_user-auth research "使用者認證系統"
  $(basename "$0") register agent_arch architecture
  $(basename "$0") send agent_arch task_assign '{"task":"分析架構"}'
  $(basename "$0") health
EOF
}

main() {
    local command="${1:-help}"
    shift || true

    case "$command" in
        init)
            init_workflow "$@"
            ;;
        register)
            register_agent "$@"
            ;;
        send)
            send_message "$@"
            ;;
        read)
            read_messages "$@"
            ;;
        ack)
            send_ack "$@"
            ;;
        heartbeat)
            update_heartbeat "$@"
            ;;
        health)
            check_agents_health "$@"
            ;;
        cleanup)
            cleanup_workflow "$@"
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            log_error "未知命令: ${command}"
            usage
            exit 1
            ;;
    esac
}

main "$@"
