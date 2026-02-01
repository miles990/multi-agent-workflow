#!/bin/bash
# validate-plugin.sh - Validate plugin structure and configuration
# Usage: ./scripts/plugin/validate-plugin.sh [--ci]

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# CI mode (stricter, exit codes)
CI_MODE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --ci)
            CI_MODE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--ci]"
            echo ""
            echo "Options:"
            echo "  --ci          CI mode (strict, with exit codes)"
            echo "  --help, -h    Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Log functions
log_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++)) || true
}

log_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++)) || true
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++)) || true
}

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Checks
check_plugin_json() {
    local plugin_json="${PROJECT_DIR}/plugin.json"

    echo ""
    log_info "Checking plugin.json..."

    if [[ ! -f "$plugin_json" ]]; then
        log_fail "plugin.json not found"
        return
    fi

    # Validate JSON
    if ! python3 -c "import json; json.load(open('${plugin_json}'))" 2>/dev/null; then
        log_fail "plugin.json is not valid JSON"
        return
    fi

    # Check required fields
    local name version description
    name=$(python3 -c "import json; print(json.load(open('${plugin_json}')).get('name', ''))")
    version=$(python3 -c "import json; print(json.load(open('${plugin_json}')).get('version', ''))")
    description=$(python3 -c "import json; print(json.load(open('${plugin_json}')).get('description', ''))")

    if [[ -z "$name" ]]; then
        log_fail "plugin.json missing 'name' field"
    else
        log_pass "plugin.json has 'name': ${name}"
    fi

    if [[ -z "$version" ]]; then
        log_fail "plugin.json missing 'version' field"
    else
        # Validate semver format
        if [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+ ]]; then
            log_pass "plugin.json has valid 'version': ${version}"
        else
            log_fail "plugin.json 'version' is not semver: ${version}"
        fi
    fi

    if [[ -z "$description" ]]; then
        log_warn "plugin.json missing 'description' field"
    else
        log_pass "plugin.json has 'description'"
    fi
}

check_marketplace_json() {
    local marketplace_json="${PROJECT_DIR}/.claude-plugin/marketplace.json"

    echo ""
    log_info "Checking marketplace.json..."

    if [[ ! -f "$marketplace_json" ]]; then
        log_warn "marketplace.json not found"
        return
    fi

    # Validate JSON
    if ! python3 -c "import json; json.load(open('${marketplace_json}'))" 2>/dev/null; then
        log_fail "marketplace.json is not valid JSON"
        return
    fi

    log_pass "marketplace.json is valid"
}

check_skills() {
    local skills_dir="${PROJECT_DIR}/skills"

    echo ""
    log_info "Checking skills..."

    if [[ ! -d "$skills_dir" ]]; then
        log_fail "skills/ directory not found"
        return
    fi

    local skill_count=0
    local invalid_skills=()

    for skill_dir in "${skills_dir}"/*; do
        if [[ -d "$skill_dir" ]] && [[ ! "$(basename "$skill_dir")" =~ ^\. ]]; then
            ((skill_count++)) || true
            local skill_name
            skill_name=$(basename "$skill_dir")

            if [[ ! -f "${skill_dir}/SKILL.md" ]]; then
                invalid_skills+=("$skill_name")
                log_fail "Skill '${skill_name}' missing SKILL.md"
            else
                log_pass "Skill '${skill_name}' has SKILL.md"
            fi
        fi
    done

    if [[ $skill_count -eq 0 ]]; then
        log_warn "No skills found"
    else
        log_info "Found ${skill_count} skills"
    fi
}

check_version_consistency() {
    echo ""
    log_info "Checking version consistency..."

    local plugin_version marketplace_version

    plugin_version=$(python3 -c "import json; print(json.load(open('${PROJECT_DIR}/plugin.json')).get('version', 'unknown'))" 2>/dev/null || echo "unknown")

    if [[ -f "${PROJECT_DIR}/.claude-plugin/marketplace.json" ]]; then
        marketplace_version=$(python3 -c "import json; d=json.load(open('${PROJECT_DIR}/.claude-plugin/marketplace.json')); print(d.get('plugins', [{}])[0].get('version', 'unknown'))" 2>/dev/null || echo "unknown")

        if [[ "$plugin_version" == "$marketplace_version" ]]; then
            log_pass "Versions are consistent: ${plugin_version}"
        else
            log_fail "Version mismatch: plugin.json=${plugin_version}, marketplace.json=${marketplace_version}"
        fi
    else
        log_pass "Version: ${plugin_version}"
    fi
}

check_git_status() {
    echo ""
    log_info "Checking git status..."

    if ! git -C "${PROJECT_DIR}" rev-parse --git-dir > /dev/null 2>&1; then
        log_warn "Not a git repository"
        return
    fi

    local status
    status=$(git -C "${PROJECT_DIR}" status --porcelain 2>/dev/null)

    if [[ -z "$status" ]]; then
        log_pass "Working directory is clean"
    else
        local changed_count
        changed_count=$(echo "$status" | wc -l | tr -d ' ')
        log_warn "${changed_count} uncommitted changes"
    fi
}

check_tests() {
    echo ""
    log_info "Checking tests..."

    if [[ ! -d "${PROJECT_DIR}/tests" ]]; then
        log_warn "No tests/ directory found"
        return
    fi

    # Quick test run
    if command -v pytest &> /dev/null; then
        if python3 -m pytest "${PROJECT_DIR}/tests/" -q --tb=no 2>/dev/null; then
            log_pass "Tests pass"
        else
            log_fail "Tests fail"
        fi
    else
        log_warn "pytest not available, skipping tests"
    fi
}

# Summary
print_summary() {
    echo ""
    echo "================================"
    echo -e "${BLUE}Validation Summary${NC}"
    echo "================================"
    echo -e "  ${GREEN}Passed:${NC}   ${PASSED}"
    echo -e "  ${RED}Failed:${NC}   ${FAILED}"
    echo -e "  ${YELLOW}Warnings:${NC} ${WARNINGS}"
    echo ""

    if [[ $FAILED -gt 0 ]]; then
        echo -e "${RED}❌ Validation failed${NC}"
        if [[ "$CI_MODE" == "true" ]]; then
            exit 1
        fi
    elif [[ $WARNINGS -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  Validation passed with warnings${NC}"
    else
        echo -e "${GREEN}✅ Validation passed${NC}"
    fi
}

# Main
main() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║    Plugin Validation               ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════╝${NC}"
    echo ""
    log_info "Project: ${PROJECT_DIR}"

    check_plugin_json
    check_marketplace_json
    check_skills
    check_version_consistency
    check_git_status
    # check_tests  # Uncomment for full validation

    print_summary
}

main
