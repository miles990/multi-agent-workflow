#!/bin/bash
# generate-changelog.sh - Generate changelog from git commits
# Usage: ./scripts/plugin/generate-changelog.sh [--since TAG] [--version VERSION]

set -euo pipefail

# 依賴檢查
check_dependency() {
  if ! command -v "$1" &> /dev/null; then
    echo -e "${RED:-}[ERROR] 未找到 '$1'，請先安裝${NC:-}" >&2
    exit 1
  fi
}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CHANGELOG_FILE="${PROJECT_DIR}/CHANGELOG.md"

check_dependency python3
check_dependency git

# Options
SINCE_TAG=""
VERSION=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --since)
            SINCE_TAG="$2"
            shift 2
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--since TAG] [--version VERSION]"
            echo ""
            echo "Options:"
            echo "  --since TAG       Start from this git tag (default: latest tag)"
            echo "  --version VERSION Version for the changelog entry (default: from plugin.json)"
            echo "  --help, -h        Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

# Get version
get_version() {
    if [[ -n "$VERSION" ]]; then
        return
    fi

    VERSION=$(python3 -c "import json; print(json.load(open('${PROJECT_DIR}/plugin.json'))['version'])")
    log_info "Version: ${VERSION}"
}

# Get since tag
get_since_tag() {
    if [[ -n "$SINCE_TAG" ]]; then
        log_info "Since tag: ${SINCE_TAG}"
        return
    fi

    SINCE_TAG=$(git -C "${PROJECT_DIR}" describe --tags --abbrev=0 2>/dev/null || echo "")
    if [[ -n "$SINCE_TAG" ]]; then
        log_info "Since tag: ${SINCE_TAG}"
    else
        log_info "No previous tags found, using all commits"
    fi
}

# Get commits
get_commits() {
    local range_spec
    if [[ -n "$SINCE_TAG" ]]; then
        range_spec="${SINCE_TAG}..HEAD"
    else
        range_spec="HEAD"
    fi

    git -C "${PROJECT_DIR}" log "$range_spec" \
        --pretty=format:"%h|%s|%an" \
        2>/dev/null || echo ""
}

# Parse and categorize commits
parse_commits() {
    local commits="$1"

    BREAKING=()
    FEATURES=()
    FIXES=()
    DOCS=()
    REFACTOR=()
    OTHER=()

    while IFS= read -r line; do
        [[ -z "$line" ]] && continue

        local hash subject author
        IFS='|' read -r hash subject author <<< "$line"

        # Check for breaking changes
        if [[ "$subject" == *"BREAKING CHANGE"* ]] || [[ "$subject" == *"[BREAKING]"* ]]; then
            BREAKING+=("- ${subject} (${hash})")
            continue
        fi

        # Parse conventional commit
        if [[ "$subject" =~ ^(feat|fix|docs|refactor|test|chore|perf)(\([^)]+\))?:\ (.+) ]]; then
            local type="${BASH_REMATCH[1]}"
            local scope="${BASH_REMATCH[2]}"
            local desc="${BASH_REMATCH[3]}"

            local entry
            if [[ -n "$scope" ]]; then
                entry="- **${scope}**: ${desc} (${hash})"
            else
                entry="- ${desc} (${hash})"
            fi

            case $type in
                feat) FEATURES+=("$entry") ;;
                fix) FIXES+=("$entry") ;;
                docs) DOCS+=("$entry") ;;
                refactor) REFACTOR+=("$entry") ;;
                *) OTHER+=("$entry") ;;
            esac
        else
            OTHER+=("- ${subject} (${hash})")
        fi
    done <<< "$commits"
}

# Generate markdown
generate_markdown() {
    local date
    date=$(date +%Y-%m-%d)

    echo "## [${VERSION}] - ${date}"
    echo ""

    if [[ ${#BREAKING[@]} -gt 0 ]]; then
        echo "### ⚠️ BREAKING CHANGES"
        echo ""
        printf '%s\n' "${BREAKING[@]}"
        echo ""
    fi

    if [[ ${#FEATURES[@]} -gt 0 ]]; then
        echo "### ✨ Features"
        echo ""
        printf '%s\n' "${FEATURES[@]}"
        echo ""
    fi

    if [[ ${#FIXES[@]} -gt 0 ]]; then
        echo "### 🐛 Bug Fixes"
        echo ""
        printf '%s\n' "${FIXES[@]}"
        echo ""
    fi

    if [[ ${#DOCS[@]} -gt 0 ]]; then
        echo "### 📚 Documentation"
        echo ""
        printf '%s\n' "${DOCS[@]}"
        echo ""
    fi

    if [[ ${#REFACTOR[@]} -gt 0 ]]; then
        echo "### ♻️ Refactoring"
        echo ""
        printf '%s\n' "${REFACTOR[@]}"
        echo ""
    fi

    if [[ ${#OTHER[@]} -gt 0 ]]; then
        echo "### 🔧 Other"
        echo ""
        printf '%s\n' "${OTHER[@]}"
        echo ""
    fi
}

# Update changelog file
update_changelog() {
    local new_content
    new_content=$(generate_markdown)

    if [[ ! -f "$CHANGELOG_FILE" ]]; then
        # Create new file
        {
            echo "# Changelog"
            echo ""
            echo "All notable changes to this project will be documented in this file."
            echo ""
            echo "$new_content"
        } > "$CHANGELOG_FILE"
    else
        # Prepend to existing file
        local temp_file
        temp_file=$(mktemp)

        # Get header (up to first version)
        head -n 4 "$CHANGELOG_FILE" > "$temp_file"
        echo "" >> "$temp_file"
        echo "$new_content" >> "$temp_file"

        # Append rest of file (skip header)
        tail -n +5 "$CHANGELOG_FILE" >> "$temp_file"

        mv "$temp_file" "$CHANGELOG_FILE"
    fi

    log_success "Updated ${CHANGELOG_FILE}"
}

# Main
main() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║    Changelog Generator             ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════╝${NC}"
    echo ""

    get_version
    get_since_tag

    local commits
    commits=$(get_commits)

    if [[ -z "$commits" ]]; then
        log_info "No commits found since ${SINCE_TAG:-beginning}"
        exit 0
    fi

    local commit_count
    commit_count=$(echo "$commits" | wc -l | tr -d ' ')
    log_info "Found ${commit_count} commits"

    parse_commits "$commits"
    update_changelog

    echo ""
    echo -e "${GREEN}Changelog preview:${NC}"
    echo "─────────────────────"
    generate_markdown
    echo "─────────────────────"
}

main
