#!/bin/bash
# publish.sh - Full release workflow
# Usage: ./scripts/plugin/publish.sh [major|minor|patch] [--dry-run] [--skip-tests]

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
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

check_dependency python3
check_dependency git

# Options
BUMP_LEVEL="patch"
DRY_RUN=false
SKIP_TESTS=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        major|minor|patch)
            BUMP_LEVEL="$1"
            shift
            ;;
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [major|minor|patch] [--dry-run] [--skip-tests]"
            echo ""
            echo "Arguments:"
            echo "  major        Bump major version (breaking changes)"
            echo "  minor        Bump minor version (new features)"
            echo "  patch        Bump patch version (bug fixes, default)"
            echo ""
            echo "Options:"
            echo "  --dry-run, -n   Simulate release without making changes"
            echo "  --skip-tests    Skip running tests"
            echo "  --help, -h      Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Step counter
STEP=0
TOTAL_STEPS=8

# Log functions
step() {
    ((STEP++)) || true
    echo ""
    echo -e "${CYAN}[${STEP}/${TOTAL_STEPS}]${NC} ${BLUE}$1${NC}"
    echo "────────────────────────────────────"
}

log_info() {
    echo -e "  ${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "  ${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "  ${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "  ${RED}✗${NC} $1"
}

log_skip() {
    echo -e "  ${YELLOW}→${NC} Skipped (dry-run)"
}

# Step 1: Validate
validate() {
    step "Validating plugin..."

    if "${SCRIPT_DIR}/validate-plugin.sh" --ci 2>/dev/null; then
        log_success "Validation passed"
    else
        # Run again without --ci to show details
        "${SCRIPT_DIR}/validate-plugin.sh" || true
        log_error "Validation failed"
        exit 1
    fi
}

# Step 2: Run tests
run_tests() {
    step "Running tests..."

    if [[ "$SKIP_TESTS" == "true" ]]; then
        log_warning "Tests skipped"
        return
    fi

    if python3 -m pytest "${PROJECT_DIR}/tests/" -q --tb=short 2>/dev/null; then
        log_success "All tests passed"
    else
        log_error "Tests failed"
        exit 1
    fi
}

# Step 3: Check git status
check_git() {
    step "Checking git status..."

    # Check for uncommitted changes (excluding version files we'll update)
    local status
    status=$(git -C "${PROJECT_DIR}" status --porcelain 2>/dev/null | grep -v "plugin.json" | grep -v "marketplace.json" | grep -v "CHANGELOG.md" || true)

    if [[ -n "$status" ]]; then
        log_error "Uncommitted changes detected:"
        echo "$status"
        log_error "Commit or stash changes before releasing"
        exit 1
    fi

    log_success "Working directory clean"

    # Check we're on main branch
    local branch
    branch=$(git -C "${PROJECT_DIR}" rev-parse --abbrev-ref HEAD)
    log_info "Current branch: ${branch}"
}

# Step 4: Bump version
bump_version() {
    step "Bumping version (${BUMP_LEVEL})..."

    # Get current version
    local current_version
    current_version=$(python3 -c "import json; print(json.load(open('${PROJECT_DIR}/plugin.json'))['version'])")
    log_info "Current version: ${current_version}"

    # Calculate new version
    local major minor patch
    IFS='.' read -r major minor patch <<< "$current_version"

    case $BUMP_LEVEL in
        major)
            NEW_VERSION="$((major + 1)).0.0"
            ;;
        minor)
            NEW_VERSION="${major}.$((minor + 1)).0"
            ;;
        patch)
            NEW_VERSION="${major}.${minor}.$((patch + 1))"
            ;;
    esac

    log_info "New version: ${NEW_VERSION}"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_skip
        return
    fi

    # Update files
    "${SCRIPT_DIR}/bump-version.sh" "$BUMP_LEVEL"
    log_success "Version bumped"
}

# Step 5: Generate changelog
generate_changelog() {
    step "Generating changelog..."

    if [[ "$DRY_RUN" == "true" ]]; then
        "${SCRIPT_DIR}/generate-changelog.sh" --version "${NEW_VERSION}" 2>/dev/null || true
        log_skip
        return
    fi

    "${SCRIPT_DIR}/generate-changelog.sh" --version "${NEW_VERSION}"
    log_success "Changelog generated"
}

# Step 6: Git commit
git_commit() {
    step "Creating git commit..."

    local commit_type
    case $BUMP_LEVEL in
        major) commit_type="release" ;;
        minor) commit_type="feat" ;;
        patch) commit_type="fix" ;;
    esac

    local commit_msg="${commit_type}(version): bump to v${NEW_VERSION}"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Would commit: ${commit_msg}"
        log_skip
        return
    fi

    git -C "${PROJECT_DIR}" add plugin.json .claude-plugin/marketplace.json CLAUDE.md CHANGELOG.md 2>/dev/null || true
    git -C "${PROJECT_DIR}" commit -m "$commit_msg" || true
    log_success "Committed: ${commit_msg}"
}

# Step 7: Git tag
git_tag() {
    step "Creating git tag..."

    local tag="v${NEW_VERSION}"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Would create tag: ${tag}"
        log_skip
        return
    fi

    git -C "${PROJECT_DIR}" tag -a "$tag" -m "Release ${tag}"
    log_success "Created tag: ${tag}"
}

# Step 8: Push
git_push() {
    step "Pushing to remote..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Would push to origin"
        log_skip
        return
    fi

    # Check if remote exists
    if ! git -C "${PROJECT_DIR}" remote get-url origin &>/dev/null; then
        log_warning "No remote 'origin' configured"
        log_info "Run manually: git push origin HEAD --tags"
        return
    fi

    git -C "${PROJECT_DIR}" push origin HEAD
    git -C "${PROJECT_DIR}" push origin "v${NEW_VERSION}"
    log_success "Pushed to origin"
}

# Summary
print_summary() {
    echo ""
    echo -e "${GREEN}════════════════════════════════════${NC}"
    echo -e "${GREEN}    Release Complete!               ${NC}"
    echo -e "${GREEN}════════════════════════════════════${NC}"
    echo ""
    echo -e "  Version: ${CYAN}v${NEW_VERSION}${NC}"
    echo -e "  Tag:     ${CYAN}v${NEW_VERSION}${NC}"
    echo ""

    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}This was a dry run. No changes were made.${NC}"
        echo "Run without --dry-run to execute the release."
    else
        echo "Next steps:"
        echo "  1. Verify the release on GitHub"
        echo "  2. Update Claude Code plugin cache: /plugin cache clean"
        echo "  3. Announce the release (if applicable)"
    fi
}

# Main
main() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║    Plugin Release                  ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════╝${NC}"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo ""
        echo -e "${YELLOW}DRY RUN MODE - No changes will be made${NC}"
    fi

    validate
    run_tests
    check_git
    bump_version
    generate_changelog
    git_commit
    git_tag
    git_push

    print_summary
}

main
