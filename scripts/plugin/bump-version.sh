#!/bin/bash
# bump-version.sh - Bump plugin version
# Usage: ./scripts/plugin/bump-version.sh [major|minor|patch] [--dry-run]

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

# Default options
BUMP_LEVEL="patch"
DRY_RUN=false

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
        --help|-h)
            echo "Usage: $0 [major|minor|patch] [--dry-run]"
            echo ""
            echo "Arguments:"
            echo "  major        Bump major version (breaking changes)"
            echo "  minor        Bump minor version (new features)"
            echo "  patch        Bump patch version (bug fixes, default)"
            echo ""
            echo "Options:"
            echo "  --dry-run, -n   Show what would change without changing"
            echo "  --help, -h      Show this help message"
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

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Read current version
read_current_version() {
    local plugin_json="${PROJECT_DIR}/plugin.json"
    if [[ ! -f "$plugin_json" ]]; then
        echo -e "${RED}plugin.json not found${NC}"
        exit 1
    fi

    CURRENT_VERSION=$(python3 -c "import json; print(json.load(open('${plugin_json}'))['version'])")
    log_info "Current version: ${CURRENT_VERSION}"
}

# Calculate new version
calculate_new_version() {
    local major minor patch
    IFS='.' read -r major minor patch <<< "$CURRENT_VERSION"

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

    log_info "New version: ${NEW_VERSION} (${BUMP_LEVEL} bump)"
}

# Update version files
update_version_files() {
    local plugin_json="${PROJECT_DIR}/plugin.json"
    local marketplace_json="${PROJECT_DIR}/.claude-plugin/marketplace.json"
    local claude_md="${PROJECT_DIR}/CLAUDE.md"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Would update:"
        echo "  - ${plugin_json}"
        [[ -f "$marketplace_json" ]] && echo "  - ${marketplace_json}"
        [[ -f "$claude_md" ]] && echo "  - ${claude_md}"
        return
    fi

    # Update plugin.json
    python3 -c "
import json
with open('${plugin_json}') as f:
    data = json.load(f)
data['version'] = '${NEW_VERSION}'
with open('${plugin_json}', 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
"
    log_success "Updated ${plugin_json}"

    # Update marketplace.json
    if [[ -f "$marketplace_json" ]]; then
        python3 -c "
import json
with open('${marketplace_json}') as f:
    data = json.load(f)
for plugin in data.get('plugins', []):
    plugin['version'] = '${NEW_VERSION}'
with open('${marketplace_json}', 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
"
        log_success "Updated ${marketplace_json}"
    fi

    # Update CLAUDE.md version declaration
    if [[ -f "$claude_md" ]]; then
        # Pattern: > 多視角並行工作流生態系 v2.3.2
        if sed -i.bak -E "s/(> .+) v[0-9]+\.[0-9]+\.[0-9]+/\1 v${NEW_VERSION}/" "$claude_md" 2>/dev/null; then
            rm -f "${claude_md}.bak"
            log_success "Updated ${claude_md}"
        fi
    fi
}

# Suggest git commands
suggest_git_commands() {
    echo ""
    log_info "Suggested git commands:"
    echo ""

    local commit_type
    case $BUMP_LEVEL in
        major) commit_type="release" ;;
        minor) commit_type="feat" ;;
        patch) commit_type="fix" ;;
    esac

    echo "  git add plugin.json .claude-plugin/marketplace.json CLAUDE.md"
    echo "  git commit -m \"${commit_type}(version): bump to v${NEW_VERSION}\""
    echo "  git tag -a v${NEW_VERSION} -m \"Release v${NEW_VERSION}\""
    echo "  git push origin HEAD --tags"
}

# Main
main() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║    Version Bump                    ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════╝${NC}"
    echo ""

    read_current_version
    calculate_new_version

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "Dry run mode - no changes will be made"
    fi

    echo ""
    update_version_files

    if [[ "$DRY_RUN" != "true" ]]; then
        suggest_git_commands
    fi

    echo ""
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry run complete"
    else
        log_success "Version bumped to ${NEW_VERSION}"
    fi
}

main
