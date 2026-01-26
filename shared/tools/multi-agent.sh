#!/bin/bash
# =============================================================================
# multi-agent.sh - Multi-Agent Workflow CLI
#
# 位置: shared/tools/multi-agent.sh
# 用途: CLI 層面的工作流管理，初始化、驗證、記錄
#
# 用法: ./multi-agent.sh <command> <skill> <topic> [options]
# =============================================================================

set -euo pipefail

# 版本
VERSION="1.0.0"

# 顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 路徑
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}/../.."
MEMORY_BASE="${PROJECT_DIR}/.claude/memory"

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
    local topic="$1"
    # 將空格和特殊字元替換為 -
    local sanitized=$(echo "$topic" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//')
    # 截斷過長的 ID
    sanitized="${sanitized:0:30}"
    echo "${sanitized}-$(date +%Y%m%d)"
}

#######################################
# 初始化 Memory 目錄
#######################################

init_memory() {
    local skill="${1:-research}"
    local topic="${2:-default}"
    local id="${3:-$(generate_id "$topic")}"

    local memory_dir="${MEMORY_BASE}/${skill}/${id}"

    log_info "初始化 Memory 目錄"
    log_info "  Skill: ${skill}"
    log_info "  Topic: ${topic}"
    log_info "  ID: ${id}"

    # 建立目錄結構
    mkdir -p "${memory_dir}/perspectives"
    mkdir -p "${memory_dir}/summaries"
    mkdir -p "${memory_dir}/logs"

    log_success "建立目錄結構"

    # 建立 meta.yaml
    cat > "${memory_dir}/meta.yaml" << EOF
id: "${id}"
topic: "${topic}"
skill: "${skill}"
date: $(date +%Y-%m-%d)
created_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)

config:
  mode: normal
  perspectives: []

status: initializing

paths:
  perspectives: perspectives/
  summaries: summaries/
  logs: logs/
  synthesis: synthesis.md
EOF

    log_success "建立 meta.yaml"

    # 初始化日誌檔案
    touch "${memory_dir}/logs/actions.jsonl"
    touch "${memory_dir}/logs/events.jsonl"
    touch "${memory_dir}/logs/errors.jsonl"

    log_success "初始化日誌檔案"

    echo ""
    echo -e "${GREEN}Memory 初始化完成${NC}"
    echo "  路徑: ${memory_dir}"
    echo ""
    echo "接下來："
    echo "  1. 執行 MAP Phase（視角 Agent）"
    echo "  2. 每個 Agent Write → perspectives/{perspective_id}.md"
    echo "  3. 執行 REDUCE Phase（匯總）"
    echo ""

    # 返回路徑
    echo "${memory_dir}"
}

#######################################
# 記錄行動
#######################################

log_action() {
    local memory_dir="${1}"
    local action="${2}"
    local details="${3:-{}}"

    local log_file="${memory_dir}/logs/actions.jsonl"
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    # 構建 JSON
    local entry=$(jq -n \
        --arg ts "$timestamp" \
        --arg action "$action" \
        --argjson details "$details" \
        '{
            timestamp: $ts,
            action: $action,
            details: $details
        }')

    echo "$entry" >> "$log_file"
}

#######################################
# 驗證視角報告
#######################################

verify_perspectives() {
    local skill="${1}"
    local id="${2}"
    local expected="${3:-4}"

    log_info "驗證視角報告"

    "${SCRIPT_DIR}/verify-perspectives.sh" "$skill" "$id" "$expected"
}

#######################################
# 更新狀態
#######################################

update_status() {
    local memory_dir="${1}"
    local status="${2}"

    local meta_file="${memory_dir}/meta.yaml"

    if [ ! -f "$meta_file" ]; then
        log_error "meta.yaml 不存在: ${meta_file}"
        return 1
    fi

    # 使用 sed 更新狀態（簡單方式）
    sed -i '' "s/^status:.*/status: ${status}/" "$meta_file"

    log_success "狀態更新為: ${status}"
}

#######################################
# 更新指標
#######################################

update_metrics() {
    local memory_dir="${1}"
    local perspectives_count="${2:-0}"
    local quality_score="${3:-0}"
    local duration="${4:-0}"

    local metrics_file="${memory_dir}/metrics.yaml"

    cat > "$metrics_file" << EOF
# Workflow 執行指標
generated_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)

execution:
  perspectives_count: ${perspectives_count}
  duration_seconds: ${duration}

quality:
  score: ${quality_score}
  passed_gate: $([ "$quality_score" -ge 70 ] && echo "true" || echo "false")

logs:
  actions: logs/actions.jsonl
  events: logs/events.jsonl
  errors: logs/errors.jsonl
EOF

    log_success "指標已更新: ${metrics_file}"
}

#######################################
# 列出現有 Memory
#######################################

list_memories() {
    local skill="${1:-}"

    echo -e "${BLUE}Memory 列表${NC}"
    echo ""

    if [ -n "$skill" ]; then
        # 列出特定 skill 的 memory
        local skill_dir="${MEMORY_BASE}/${skill}"
        if [ -d "$skill_dir" ]; then
            echo -e "${CYAN}${skill}/${NC}"
            for dir in "${skill_dir}"/*/; do
                if [ -d "$dir" ]; then
                    local id=$(basename "$dir")
                    local meta="${dir}meta.yaml"
                    if [ -f "$meta" ]; then
                        local topic=$(grep "^topic:" "$meta" | cut -d'"' -f2)
                        local status=$(grep "^status:" "$meta" | awk '{print $2}')
                        local date=$(grep "^date:" "$meta" | awk '{print $2}')
                        printf "  %-30s  %s  %s  %s\n" "$id" "$date" "$status" "$topic"
                    else
                        printf "  %-30s  (no meta.yaml)\n" "$id"
                    fi
                fi
            done
        else
            log_warn "Skill 目錄不存在: ${skill}"
        fi
    else
        # 列出所有 skill 的 memory
        for skill_dir in "${MEMORY_BASE}"/*/; do
            if [ -d "$skill_dir" ]; then
                local skill_name=$(basename "$skill_dir")
                echo -e "${CYAN}${skill_name}/${NC}"
                for dir in "${skill_dir}"/*/; do
                    if [ -d "$dir" ]; then
                        local id=$(basename "$dir")
                        printf "  %s\n" "$id"
                    fi
                done
                echo ""
            fi
        done
    fi
}

#######################################
# 清理 Memory
#######################################

cleanup_memory() {
    local skill="${1}"
    local id="${2}"
    local force="${3:-false}"

    local memory_dir="${MEMORY_BASE}/${skill}/${id}"

    if [ ! -d "$memory_dir" ]; then
        log_error "Memory 不存在: ${memory_dir}"
        return 1
    fi

    if [ "$force" != "true" ]; then
        echo -e "${YELLOW}即將刪除: ${memory_dir}${NC}"
        read -p "確認刪除？(y/N) " confirm
        if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
            log_info "已取消"
            return 0
        fi
    fi

    rm -rf "$memory_dir"
    log_success "已刪除: ${memory_dir}"
}

#######################################
# 顯示使用說明
#######################################

usage() {
    cat << EOF
Multi-Agent Workflow CLI v${VERSION}

用法: $(basename "$0") <command> [options]

Commands:
  init <skill> <topic> [id]     初始化 Memory 目錄
  verify <skill> <id> [count]   驗證視角報告完整性
  status <skill> <id> <status>  更新狀態
  metrics <skill> <id>          更新指標
  list [skill]                  列出 Memory
  cleanup <skill> <id> [--force]  刪除 Memory

Skills:
  research, plan, tasks, implement, review, verify

範例:
  $(basename "$0") init research "用戶認證系統"
  $(basename "$0") init plan "Feature X" feature-x-20260126
  $(basename "$0") verify research user-auth-20260126 4
  $(basename "$0") list research
  $(basename "$0") cleanup research user-auth-20260126

目錄結構:
  .claude/memory/{skill}/{id}/
  ├── meta.yaml
  ├── perspectives/
  │   └── {perspective_id}.md
  ├── summaries/
  │   └── {perspective_id}.yaml
  ├── logs/
  │   ├── actions.jsonl
  │   ├── events.jsonl
  │   └── errors.jsonl
  └── synthesis.md
EOF
}

#######################################
# 主函數
#######################################

main() {
    local command="${1:-help}"
    shift || true

    case "$command" in
        init)
            if [ $# -lt 2 ]; then
                log_error "缺少參數: init <skill> <topic> [id]"
                exit 1
            fi
            init_memory "$@"
            ;;
        verify)
            if [ $# -lt 2 ]; then
                log_error "缺少參數: verify <skill> <id> [expected_count]"
                exit 1
            fi
            verify_perspectives "$@"
            ;;
        status)
            if [ $# -lt 3 ]; then
                log_error "缺少參數: status <skill> <id> <status>"
                exit 1
            fi
            local skill="$1"
            local id="$2"
            local status="$3"
            update_status "${MEMORY_BASE}/${skill}/${id}" "$status"
            ;;
        metrics)
            if [ $# -lt 2 ]; then
                log_error "缺少參數: metrics <skill> <id>"
                exit 1
            fi
            local skill="$1"
            local id="$2"
            shift 2
            update_metrics "${MEMORY_BASE}/${skill}/${id}" "$@"
            ;;
        list)
            list_memories "$@"
            ;;
        cleanup)
            if [ $# -lt 2 ]; then
                log_error "缺少參數: cleanup <skill> <id> [--force]"
                exit 1
            fi
            local skill="$1"
            local id="$2"
            local force="false"
            [ "${3:-}" = "--force" ] && force="true"
            cleanup_memory "$skill" "$id" "$force"
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
