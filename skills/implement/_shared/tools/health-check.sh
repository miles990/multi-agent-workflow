#!/bin/bash
# Health Check Tool for multi-agent-workflow Plugin v1.0.0
# 驗證所有 skill 的完整性和結構正確性

set -euo pipefail

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 版本
VERSION="1.0.0"

# 計數器
TOTAL_CHECKS=0
PASSED_CHECKS=0
WARNING_CHECKS=0
ERROR_CHECKS=0

# 結果存儲
declare -a ERRORS=()
declare -a WARNINGS=()

#######################################
# 輔助函數
#######################################

log_pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    ((PASSED_CHECKS++)) || true
    ((TOTAL_CHECKS++)) || true
}

log_warn() {
    echo -e "  ${YELLOW}⚠${NC} $1"
    WARNINGS+=("$1")
    ((WARNING_CHECKS++)) || true
    ((TOTAL_CHECKS++)) || true
}

log_error() {
    echo -e "  ${RED}✗${NC} $1"
    ERRORS+=("$1")
    ((ERROR_CHECKS++)) || true
    ((TOTAL_CHECKS++)) || true
}

log_info() {
    echo -e "  ${BLUE}ℹ${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  Health Check v${VERSION}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

#######################################
# 驗證函數
#######################################

# 驗證 plugin.json
validate_plugin_json() {
    local base_path="$1"
    local plugin_json="${base_path}/plugin.json"

    echo -e "\n${BLUE}[1] Plugin Structure${NC}"

    if [[ -f "$plugin_json" ]]; then
        log_pass "plugin.json exists"

        # 檢查是否為有效 JSON（簡單檢查）
        if grep -q '"name"' "$plugin_json" && grep -q '"version"' "$plugin_json"; then
            log_pass "plugin.json has required fields (name, version)"
        else
            log_error "plugin.json missing required fields"
        fi
    else
        log_error "plugin.json not found"
    fi

    # 檢查目錄結構
    if [[ -d "${base_path}/skills" ]]; then
        log_pass "skills/ directory exists"
    else
        log_error "skills/ directory not found"
    fi

    if [[ -d "${base_path}/shared" ]]; then
        log_pass "shared/ directory exists"
    else
        log_error "shared/ directory not found"
    fi
}

# 掃描並驗證 skills
validate_skills_inventory() {
    local base_path="$1"
    local skills_dir="${base_path}/skills"

    echo -e "\n${BLUE}[2] Skills Inventory${NC}"

    if [[ ! -d "$skills_dir" ]]; then
        log_error "Cannot scan skills - directory not found"
        return
    fi

    local skill_count=0
    local valid_count=0

    for skill_dir in "$skills_dir"/*/; do
        if [[ -d "$skill_dir" ]]; then
            local skill_name=$(basename "$skill_dir")
            ((skill_count++)) || true

            if [[ -f "${skill_dir}SKILL.md" ]]; then
                log_pass "${skill_name}: SKILL.md exists"
                ((valid_count++)) || true
            else
                log_error "${skill_name}: SKILL.md not found"
            fi
        fi
    done

    log_info "Found ${valid_count}/${skill_count} valid skills"
}

# 驗證單個 skill 的內部結構
validate_skill_structure() {
    local base_path="$1"
    local skills_dir="${base_path}/skills"

    echo -e "\n${BLUE}[3] Skill Structure${NC}"

    if [[ ! -d "$skills_dir" ]]; then
        return
    fi

    for skill_dir in "$skills_dir"/*/; do
        if [[ -d "$skill_dir" ]]; then
            local skill_name=$(basename "$skill_dir")

            # 檢查 00-quickstart
            if [[ -d "${skill_dir}00-quickstart" ]]; then
                if [[ -d "${skill_dir}00-quickstart/_base" ]]; then
                    log_pass "${skill_name}: 00-quickstart/_base exists"
                else
                    log_warn "${skill_name}: 00-quickstart/_base not found"
                fi
            else
                log_warn "${skill_name}: 00-quickstart not found"
            fi

            # 檢查 01-perspectives 或 01-stage-detection (orchestrate 特殊處理)
            if [[ "$skill_name" == "orchestrate" ]]; then
                if [[ -d "${skill_dir}01-stage-detection" ]]; then
                    log_pass "${skill_name}: 01-stage-detection exists (orchestrate pattern)"
                else
                    log_warn "${skill_name}: 01-stage-detection not found"
                fi
            else
                if [[ -d "${skill_dir}01-perspectives" ]]; then
                    if [[ -d "${skill_dir}01-perspectives/_base" ]]; then
                        log_pass "${skill_name}: 01-perspectives/_base exists"
                    else
                        log_warn "${skill_name}: 01-perspectives/_base not found"
                    fi
                else
                    log_warn "${skill_name}: 01-perspectives not found"
                fi
            fi
        fi
    done
}

# 驗證 SKILL.md frontmatter
validate_frontmatter() {
    local base_path="$1"
    local skills_dir="${base_path}/skills"

    echo -e "\n${BLUE}[4] SKILL.md Frontmatter${NC}"

    if [[ ! -d "$skills_dir" ]]; then
        return
    fi

    for skill_dir in "$skills_dir"/*/; do
        if [[ -d "$skill_dir" ]] && [[ -f "${skill_dir}SKILL.md" ]]; then
            local skill_name=$(basename "$skill_dir")
            local skill_md="${skill_dir}SKILL.md"

            # 檢查是否有 frontmatter
            if head -1 "$skill_md" | grep -q "^---$"; then
                # 檢查必要欄位
                local has_name=$(grep -c "^name:" "$skill_md" 2>/dev/null || echo 0)
                local has_version=$(grep -c "^version:" "$skill_md" 2>/dev/null || echo 0)
                local has_desc=$(grep -c "^description:" "$skill_md" 2>/dev/null || echo 0)
                local has_triggers=$(grep -c "^triggers:" "$skill_md" 2>/dev/null || echo 0)
                local has_keywords=$(grep -c "^keywords:" "$skill_md" 2>/dev/null || echo 0)

                if [[ $has_name -gt 0 ]] && [[ $has_version -gt 0 ]] && [[ $has_desc -gt 0 ]]; then
                    log_pass "${skill_name}: frontmatter valid (name, version, description)"
                else
                    log_error "${skill_name}: frontmatter missing required fields"
                fi

                if [[ $has_triggers -eq 0 ]]; then
                    log_warn "${skill_name}: triggers field missing"
                fi

                if [[ $has_keywords -eq 0 ]]; then
                    log_warn "${skill_name}: keywords field missing"
                fi
            else
                log_error "${skill_name}: SKILL.md missing frontmatter (should start with ---)"
            fi
        fi
    done
}

# 驗證共用模組
validate_shared_modules() {
    local base_path="$1"
    local shared_dir="${base_path}/shared"

    echo -e "\n${BLUE}[5] Shared Modules${NC}"

    if [[ ! -d "$shared_dir" ]]; then
        log_error "shared/ directory not found"
        return
    fi

    local expected_modules=("coordination" "synthesis" "perspectives" "integration" "isolation")

    for module in "${expected_modules[@]}"; do
        if [[ -d "${shared_dir}/${module}" ]]; then
            log_pass "shared/${module}/ exists"
        else
            log_warn "shared/${module}/ not found"
        fi
    done

    # 檢查 tools 目錄（自我檢查）
    if [[ -d "${shared_dir}/tools" ]]; then
        log_pass "shared/tools/ exists"
    else
        log_info "shared/tools/ not found (will be created)"
    fi
}

# 生成報告
generate_report() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  Summary${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "  Total Checks: ${TOTAL_CHECKS}"
    echo -e "  ${GREEN}Passed${NC}: ${PASSED_CHECKS}"
    echo -e "  ${YELLOW}Warnings${NC}: ${WARNING_CHECKS}"
    echo -e "  ${RED}Errors${NC}: ${ERROR_CHECKS}"
    echo ""

    if [[ ${#ERRORS[@]} -gt 0 ]]; then
        echo -e "${RED}Errors:${NC}"
        for err in "${ERRORS[@]}"; do
            echo "  - $err"
        done
        echo ""
    fi

    if [[ ${#WARNINGS[@]} -gt 0 ]]; then
        echo -e "${YELLOW}Warnings:${NC}"
        for warn in "${WARNINGS[@]}"; do
            echo "  - $warn"
        done
        echo ""
    fi

    # 最終狀態
    if [[ ${ERROR_CHECKS} -gt 0 ]]; then
        echo -e "Overall Status: ${RED}UNHEALTHY${NC}"
        echo "Exit Code: 2"
        return 2
    elif [[ ${WARNING_CHECKS} -gt 0 ]]; then
        echo -e "Overall Status: ${YELLOW}HEALTHY WITH WARNINGS${NC}"
        echo "Exit Code: 1"
        return 1
    else
        echo -e "Overall Status: ${GREEN}HEALTHY${NC}"
        echo "Exit Code: 0"
        return 0
    fi
}

#######################################
# 主函數
#######################################

main() {
    local base_path="${1:-.}"

    # 解析絕對路徑
    base_path=$(cd "$base_path" && pwd)

    print_header
    echo "Checking: ${base_path}"

    # 執行所有驗證
    validate_plugin_json "$base_path"
    validate_skills_inventory "$base_path"
    validate_skill_structure "$base_path"
    validate_frontmatter "$base_path"
    validate_shared_modules "$base_path"

    # 生成報告並返回狀態碼
    generate_report
}

# 執行
main "$@"
