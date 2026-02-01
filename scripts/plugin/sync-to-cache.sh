#!/bin/bash
# sync-to-cache.sh - Sync plugin to Claude Code cache
# Usage: ./scripts/plugin/sync-to-cache.sh [--force] [--dry-run] [--verbose]

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
FORCE=false
DRY_RUN=false
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force|-f)
            FORCE=true
            shift
            ;;
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--force] [--dry-run] [--verbose]"
            echo ""
            echo "Options:"
            echo "  --force, -f     Force full sync (ignore incremental)"
            echo "  --dry-run, -n   Show what would be synced without syncing"
            echo "  --verbose, -v   Show detailed output"
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

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_verbose() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${NC}       $1"
    fi
}

# Read plugin.json
read_plugin_json() {
    local plugin_json="${PROJECT_DIR}/plugin.json"
    if [[ ! -f "$plugin_json" ]]; then
        log_error "plugin.json not found at ${plugin_json}"
        exit 1
    fi

    PLUGIN_NAME=$(python3 -c "import json; print(json.load(open('${plugin_json}'))['name'])")
    PLUGIN_VERSION=$(python3 -c "import json; print(json.load(open('${plugin_json}'))['version'])")

    log_verbose "Plugin: ${PLUGIN_NAME} v${PLUGIN_VERSION}"
}

# Get cache directory
get_cache_dir() {
    local cache_base="${PLUGIN_CACHE_BASE:-${HOME}/.claude/plugins/cache}"
    CACHE_DIR="${cache_base}/${PLUGIN_NAME}/${PLUGIN_NAME}/${PLUGIN_VERSION}"
    log_verbose "Cache: ${CACHE_DIR}"
}

# Sync using rsync
sync_with_rsync() {
    local rsync_opts="-av --delete"

    if [[ "$DRY_RUN" == "true" ]]; then
        rsync_opts="${rsync_opts} --dry-run"
    fi

    if [[ "$VERBOSE" != "true" ]]; then
        rsync_opts="${rsync_opts} --quiet"
    fi

    # Exclude patterns
    local excludes=(
        "__pycache__"
        "*.pyc"
        "*.pyo"
        ".git"
        ".gitignore"
        ".pytest_cache"
        ".coverage"
        "*.egg-info"
        "tests"
        ".plugin-dev"
        ".claude/workflow"
        ".claude/memory"
        "cli"
        "scripts"
        "docs"
        "agents"
    )

    # Build exclude arguments
    local exclude_args=""
    for pattern in "${excludes[@]}"; do
        exclude_args="${exclude_args} --exclude=${pattern}"
    done

    # Include patterns (only sync these)
    local include_dirs=(
        "skills"
        "shared"
        "templates"
        ".claude-plugin"
    )

    local include_files=(
        "plugin.json"
        "CLAUDE.md"
        "LICENSE"
    )

    # Create cache directory
    if [[ "$DRY_RUN" != "true" ]]; then
        mkdir -p "$CACHE_DIR"
    fi

    # Sync directories
    for dir in "${include_dirs[@]}"; do
        local src="${PROJECT_DIR}/${dir}/"
        local dest="${CACHE_DIR}/${dir}/"

        if [[ -d "$src" ]]; then
            log_verbose "Syncing ${dir}/"

            if [[ "$DRY_RUN" != "true" ]]; then
                mkdir -p "$dest"
            fi

            # shellcheck disable=SC2086
            rsync $rsync_opts $exclude_args "$src" "$dest" || true
        fi
    done

    # Sync individual files
    for file in "${include_files[@]}"; do
        local src="${PROJECT_DIR}/${file}"
        local dest="${CACHE_DIR}/${file}"

        if [[ -f "$src" ]]; then
            log_verbose "Syncing ${file}"

            if [[ "$DRY_RUN" != "true" ]]; then
                cp "$src" "$dest"
            fi
        fi
    done
}

# Fallback sync using cp
sync_with_cp() {
    log_warning "rsync not found, using cp fallback"

    # Create cache directory
    if [[ "$DRY_RUN" != "true" ]]; then
        mkdir -p "$CACHE_DIR"
    fi

    # Directories to sync
    local dirs=("skills" "shared" "templates" ".claude-plugin")

    for dir in "${dirs[@]}"; do
        local src="${PROJECT_DIR}/${dir}"
        local dest="${CACHE_DIR}/${dir}"

        if [[ -d "$src" ]]; then
            log_verbose "Syncing ${dir}/"

            if [[ "$DRY_RUN" != "true" ]]; then
                rm -rf "$dest"
                cp -R "$src" "$dest"
            fi
        fi
    done

    # Files to sync
    local files=("plugin.json" "CLAUDE.md" "LICENSE")

    for file in "${files[@]}"; do
        local src="${PROJECT_DIR}/${file}"
        local dest="${CACHE_DIR}/${file}"

        if [[ -f "$src" ]]; then
            log_verbose "Syncing ${file}"

            if [[ "$DRY_RUN" != "true" ]]; then
                cp "$src" "$dest"
            fi
        fi
    done
}

# Main
main() {
    log_info "Syncing plugin to cache..."

    # Read plugin info
    read_plugin_json

    # Get cache directory
    get_cache_dir

    # Check if force or first sync
    if [[ "$FORCE" == "true" ]] || [[ ! -d "$CACHE_DIR" ]]; then
        log_info "Performing full sync"
    fi

    # Sync
    if command -v rsync &> /dev/null; then
        sync_with_rsync
    else
        sync_with_cp
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry run complete (no changes made)"
    else
        log_success "Synced to ${CACHE_DIR}"
    fi
}

main
