#!/bin/bash
# dev-watch.sh - Watch for file changes and auto-sync
# Usage: ./scripts/plugin/dev-watch.sh [--debounce MS]

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
SYNC_SCRIPT="${SCRIPT_DIR}/sync-to-cache.sh"

# Default options
DEBOUNCE_MS="${PLUGIN_WATCH_DEBOUNCE:-500}"
DEBOUNCE_S=$(echo "scale=2; ${DEBOUNCE_MS}/1000" | bc)

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --debounce)
            DEBOUNCE_MS="$2"
            DEBOUNCE_S=$(echo "scale=2; ${DEBOUNCE_MS}/1000" | bc)
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--debounce MS]"
            echo ""
            echo "Options:"
            echo "  --debounce MS   Debounce time in milliseconds (default: 500)"
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

# Directories to watch
WATCH_DIRS=(
    "${PROJECT_DIR}/skills"
    "${PROJECT_DIR}/shared"
    "${PROJECT_DIR}/templates"
)

# Initial sync
initial_sync() {
    log_info "Performing initial sync..."
    "${SYNC_SCRIPT}"
}

# Sync on change
sync_on_change() {
    log_info "$(date '+%H:%M:%S') Syncing..."
    "${SYNC_SCRIPT}" --quiet 2>/dev/null || "${SYNC_SCRIPT}"
    log_success "Synced"
}

# Watch with fswatch (macOS)
watch_with_fswatch() {
    log_info "Using fswatch for file monitoring"

    # Build exclude patterns
    local excludes=(
        "__pycache__"
        ".git"
        ".pytest_cache"
        "*.pyc"
    )

    local exclude_args=""
    for pattern in "${excludes[@]}"; do
        exclude_args="${exclude_args} --exclude=${pattern}"
    done

    # Start watching
    # shellcheck disable=SC2086
    fswatch \
        --recursive \
        --latency "${DEBOUNCE_S}" \
        $exclude_args \
        "${WATCH_DIRS[@]}" | while read -r _; do
            sync_on_change
        done
}

# Watch with inotifywait (Linux)
watch_with_inotifywait() {
    log_info "Using inotifywait for file monitoring"

    local watch_dirs=""
    for dir in "${WATCH_DIRS[@]}"; do
        if [[ -d "$dir" ]]; then
            watch_dirs="${watch_dirs} ${dir}"
        fi
    done

    # Start watching
    # shellcheck disable=SC2086
    inotifywait \
        --recursive \
        --monitor \
        --event modify,create,delete \
        --exclude '__pycache__|\.git|\.pyc$' \
        $watch_dirs 2>/dev/null | while read -r _; do
            # Debounce
            sleep "${DEBOUNCE_S}"
            sync_on_change
        done
}

# Watch with polling (fallback)
watch_with_polling() {
    log_warning "No file watcher found, using polling (every 2s)"

    local last_hash=""

    while true; do
        # Compute hash of watched files
        local current_hash
        current_hash=$(find "${WATCH_DIRS[@]}" -type f -name "*.md" -o -name "*.yaml" -o -name "*.json" 2>/dev/null | xargs md5sum 2>/dev/null | md5sum | cut -d' ' -f1 || echo "")

        if [[ "$current_hash" != "$last_hash" ]] && [[ -n "$last_hash" ]]; then
            sync_on_change
        fi

        last_hash="$current_hash"
        sleep 2
    done
}

# Cleanup on exit
cleanup() {
    log_info "Stopping watch..."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Main
main() {
    echo ""
    echo -e "${GREEN}👀 Plugin Development Watch${NC}"
    echo "   Project: ${PROJECT_DIR}"
    echo "   Debounce: ${DEBOUNCE_MS}ms"
    echo "   Press Ctrl+C to stop"
    echo ""

    # Check watch directories exist
    for dir in "${WATCH_DIRS[@]}"; do
        if [[ ! -d "$dir" ]]; then
            log_warning "Watch directory not found: ${dir}"
        fi
    done

    # Initial sync
    initial_sync

    echo ""
    log_info "Watching for changes..."

    # Choose watcher
    if command -v fswatch &> /dev/null; then
        watch_with_fswatch
    elif command -v inotifywait &> /dev/null; then
        watch_with_inotifywait
    else
        watch_with_polling
    fi
}

main
