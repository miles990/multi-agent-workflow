#!/bin/sh

# Configuration Query Tool
# Query and display configurations from the centralized INDEX.yaml
#
# Usage:
#   ./scripts/get-config.sh --list-categories       # List all configuration categories
#   ./scripts/get-config.sh --category skill-config # List configs in a category
#   ./scripts/get-config.sh --search "tdd"          # Search for configs
#   ./scripts/get-config.sh --show skills/implement/SKILL.md  # Show config details
#   ./scripts/get-config.sh --relations             # Show configuration relations

set -e

# Get script directory (POSIX compatible)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INDEX_FILE="$PROJECT_ROOT/shared/config/INDEX.yaml"

# Color definitions (check if terminal supports colors)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    MAGENTA='\033[0;35m'
    BOLD='\033[1m'
    DIM='\033[2m'
    RESET='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    CYAN=''
    MAGENTA=''
    BOLD=''
    DIM=''
    RESET=''
fi

# Command line options
MODE="help"
SEARCH_TERM=""
CATEGORY_FILTER=""
SHOW_PATH=""

# Helper functions
print_header() {
    printf "\n${CYAN}${BOLD}%s${RESET}\n" "$1"
    printf "${CYAN}%s${RESET}\n\n" "$(echo "$1" | sed 's/./-/g')"
}

print_error() {
    printf "${RED}Error:${RESET} %s\n" "$1" >&2
}

print_info() {
    printf "${BLUE}Info:${RESET} %s\n" "$1"
}

print_success() {
    printf "${GREEN}OK:${RESET} %s\n" "$1"
}

# Category type color
type_color() {
    case "$1" in
        skill-config)       printf "${MAGENTA}%s${RESET}" "$1" ;;
        perspective-config) printf "${CYAN}%s${RESET}" "$1" ;;
        quality-config)     printf "${GREEN}%s${RESET}" "$1" ;;
        coordination-config) printf "${YELLOW}%s${RESET}" "$1" ;;
        integration-config) printf "${BLUE}%s${RESET}" "$1" ;;
        metrics-config)     printf "${RED}%s${RESET}" "$1" ;;
        schema-config)      printf "${DIM}%s${RESET}" "$1" ;;
        expertise-config)   printf "${BOLD}%s${RESET}" "$1" ;;
        plugin-config)      printf "${MAGENTA}${DIM}plugin-config${RESET}" ;;
        *)                  printf "%s" "$1" ;;
    esac
}

# Icon mapping
get_icon() {
    case "$1" in
        lightning) printf "+" ;;
        eye)       printf "o" ;;
        shield)    printf "#" ;;
        arrows)    printf ">" ;;
        plug)      printf "@" ;;
        chart)     printf "~" ;;
        file)      printf "=" ;;
        brain)     printf "*" ;;
        puzzle)    printf "P" ;;
        *)         printf "-" ;;
    esac
}

# Check for required tools
check_dependencies() {
    if ! command -v grep >/dev/null 2>&1; then
        print_error "grep is required but not installed"
        exit 1
    fi
    if ! command -v awk >/dev/null 2>&1; then
        print_error "awk is required but not installed"
        exit 1
    fi
    if ! command -v sed >/dev/null 2>&1; then
        print_error "sed is required but not installed"
        exit 1
    fi
}

# Check if INDEX exists
check_index() {
    if [ ! -f "$INDEX_FILE" ]; then
        print_error "INDEX.yaml not found: $INDEX_FILE"
        print_info "Run the configuration indexing task first to generate INDEX.yaml"
        exit 1
    fi
}

# List all categories
list_categories() {
    print_header "Configuration Categories"

    # Table header
    printf "${BOLD}%-5s %-22s %-6s %s${RESET}\n" \
        "ICON" "ID" "COUNT" "DESCRIPTION"
    printf "%s\n" "$(printf '%.0s-' $(seq 1 90))"

    in_categories=0

    current_id=""
    current_desc=""
    current_icon=""
    current_count=""

    while IFS= read -r line; do
        # Check if we're in categories section
        if echo "$line" | grep -q "^categories:"; then
            in_categories=1
            continue
        fi

        # Check if we've left categories section
        if [ $in_categories -eq 1 ] && echo "$line" | grep -qE "^[a-z_]+:" && ! echo "$line" | grep -q "^  "; then
            # Print last category before leaving
            if [ -n "$current_id" ]; then
                printf " [%s]  " "$(get_icon "$current_icon")"
                type_color "$current_id"
                printf "%-14s " ""
                printf "%-6s " "$current_count"
                printf "%s\n" "$current_desc"
            fi
            in_categories=0
        fi

        if [ $in_categories -eq 1 ]; then
            if echo "$line" | grep -qE "^  - id:"; then
                # Print previous category if exists
                if [ -n "$current_id" ]; then
                    printf " [%s]  " "$(get_icon "$current_icon")"
                    type_color "$current_id"
                    printf "%-14s " ""
                    printf "%-6s " "$current_count"
                    printf "%s\n" "$current_desc"
                fi
                current_id=$(echo "$line" | sed 's/.*id: *//' | tr -d '"')
                current_desc=""
                current_icon=""
                current_count=""
            elif echo "$line" | grep -qE "^    description:"; then
                current_desc=$(echo "$line" | sed 's/.*description: *//' | tr -d '"')
            elif echo "$line" | grep -qE "^    icon:"; then
                current_icon=$(echo "$line" | sed 's/.*icon: *//' | tr -d '"')
            elif echo "$line" | grep -qE "^    count:"; then
                current_count=$(echo "$line" | sed 's/.*count: *//' | tr -d '"')
            fi
        fi
    done < "$INDEX_FILE"

    printf "\n"
    printf "${DIM}Use --category <id> to list configurations in a specific category${RESET}\n"
    printf "\n"
}

# List entries by category
list_by_category() {
    category="$1"

    print_header "Configurations: $category"

    # Table header
    printf "${BOLD}%-50s %s${RESET}\n" "PATH" "DESCRIPTION"
    printf "%s\n" "$(printf '%.0s-' $(seq 1 90))"

    in_entries=0
    match_found=0

    current_path=""
    current_type=""
    current_desc=""

    while IFS= read -r line; do
        # Check if we're in entries section
        if echo "$line" | grep -q "^entries:"; then
            in_entries=1
            continue
        fi

        # Check if we've left entries section (end of file or new top-level key)
        if [ $in_entries -eq 1 ] && echo "$line" | grep -qE "^[a-z#]" && ! echo "$line" | grep -q "^  "; then
            # Print last entry if matches
            if [ -n "$current_path" ] && [ "$current_type" = "$category" ]; then
                print_entry_row "$current_path" "$current_desc"
                match_found=1
            fi
            in_entries=0
        fi

        if [ $in_entries -eq 1 ]; then
            if echo "$line" | grep -qE "^  - path:"; then
                # Print previous entry if matches
                if [ -n "$current_path" ] && [ "$current_type" = "$category" ]; then
                    print_entry_row "$current_path" "$current_desc"
                    match_found=1
                fi
                current_path=$(echo "$line" | sed 's/.*path: *//' | tr -d '"')
                current_type=""
                current_desc=""
            elif echo "$line" | grep -qE "^    type:"; then
                current_type=$(echo "$line" | sed 's/.*type: *//' | tr -d '"')
            elif echo "$line" | grep -qE "^    description:"; then
                current_desc=$(echo "$line" | sed 's/.*description: *//' | tr -d '"')
            fi
        fi
    done < "$INDEX_FILE"

    if [ $match_found -eq 0 ]; then
        printf "${DIM}No configurations found for category: %s${RESET}\n" "$category"
        printf "\nAvailable categories:\n"
        list_category_ids
    fi

    printf "\n"
}

print_entry_row() {
    path="$1"
    desc="$2"

    # Truncate description if too long
    if [ ${#desc} -gt 38 ]; then
        desc="$(echo "$desc" | cut -c1-37)..."
    fi

    printf "%-50s %s\n" "$path" "$desc"
}

# List category IDs
list_category_ids() {
    grep -E "^  - id:" "$INDEX_FILE" | sed 's/.*id: *//' | tr -d '"' | head -20
}

# Search configurations
search_configs() {
    term="$1"
    term_lower=$(echo "$term" | tr '[:upper:]' '[:lower:]')

    print_header "Search Results: $term"

    # Table header
    printf "${BOLD}%-50s %-20s %s${RESET}\n" "PATH" "TYPE" "MATCH"
    printf "%s\n" "$(printf '%.0s-' $(seq 1 95))"

    in_entries=0
    match_count=0

    current_path=""
    current_type=""
    current_desc=""
    current_keys=""

    while IFS= read -r line; do
        # Check if we're in entries section
        if echo "$line" | grep -q "^entries:"; then
            in_entries=1
            continue
        fi

        # Check if we've left entries section
        if [ $in_entries -eq 1 ] && echo "$line" | grep -qE "^[a-z#]" && ! echo "$line" | grep -q "^  "; then
            # Check last entry
            if [ -n "$current_path" ]; then
                check_and_print_match "$current_path" "$current_type" "$current_desc" "$current_keys" "$term_lower"
            fi
            in_entries=0
        fi

        if [ $in_entries -eq 1 ]; then
            if echo "$line" | grep -qE "^  - path:"; then
                # Check previous entry
                if [ -n "$current_path" ]; then
                    check_and_print_match "$current_path" "$current_type" "$current_desc" "$current_keys" "$term_lower"
                fi
                current_path=$(echo "$line" | sed 's/.*path: *//' | tr -d '"')
                current_type=""
                current_desc=""
                current_keys=""
            elif echo "$line" | grep -qE "^    type:"; then
                current_type=$(echo "$line" | sed 's/.*type: *//' | tr -d '"')
            elif echo "$line" | grep -qE "^    description:"; then
                current_desc=$(echo "$line" | sed 's/.*description: *//' | tr -d '"')
            elif echo "$line" | grep -qE "^    keys:" || echo "$line" | grep -qE "^      -"; then
                # Collect keys
                if echo "$line" | grep -qE "^      -"; then
                    key_value=$(echo "$line" | sed 's/^      - *//')
                    current_keys="$current_keys $key_value"
                fi
            fi
        fi
    done < "$INDEX_FILE"

    if [ $match_count -eq 0 ]; then
        printf "${DIM}No configurations found matching: %s${RESET}\n" "$term"
    fi

    printf "\n"
    printf "${DIM}Found %d matching configuration(s)${RESET}\n" "$match_count"
    printf "\n"
}

check_and_print_match() {
    path="$1"
    type="$2"
    desc="$3"
    keys="$4"
    term="$5"

    # Convert to lowercase for case-insensitive search
    path_lower=$(echo "$path" | tr '[:upper:]' '[:lower:]')
    desc_lower=$(echo "$desc" | tr '[:upper:]' '[:lower:]')
    keys_lower=$(echo "$keys" | tr '[:upper:]' '[:lower:]')
    type_lower=$(echo "$type" | tr '[:upper:]' '[:lower:]')

    match_where=""

    # Check path
    if echo "$path_lower" | grep -qi "$term"; then
        match_where="path"
    # Check description
    elif echo "$desc_lower" | grep -qi "$term"; then
        match_where="description"
    # Check keys
    elif echo "$keys_lower" | grep -qi "$term"; then
        match_where="keys"
    # Check type
    elif echo "$type_lower" | grep -qi "$term"; then
        match_where="type"
    fi

    if [ -n "$match_where" ]; then
        printf "%-50s " "$path"
        type_color "$type"
        printf "%-12s " ""
        printf "${GREEN}%s${RESET}\n" "$match_where"
        match_count=$((match_count + 1))
    fi
}

# Show specific configuration details
show_config() {
    config_path="$1"

    print_header "Configuration: $config_path"

    in_entries=0
    found=0

    current_path=""
    current_type=""
    current_desc=""
    in_keys=0
    in_refs=0

    while IFS= read -r line; do
        # Check if we're in entries section
        if echo "$line" | grep -q "^entries:"; then
            in_entries=1
            continue
        fi

        if [ $in_entries -eq 1 ]; then
            if echo "$line" | grep -qE "^  - path:"; then
                path=$(echo "$line" | sed 's/.*path: *//' | tr -d '"')
                if [ "$path" = "$config_path" ]; then
                    found=1
                    printf "${BOLD}Path:${RESET} %s\n" "$path"
                    in_keys=0
                    in_refs=0
                elif [ $found -eq 1 ]; then
                    # We've moved past the target entry
                    break
                fi
            elif [ $found -eq 1 ]; then
                if echo "$line" | grep -qE "^    type:"; then
                    type=$(echo "$line" | sed 's/.*type: *//' | tr -d '"')
                    printf "${BOLD}Type:${RESET} "
                    type_color "$type"
                    printf "\n"
                    in_keys=0
                    in_refs=0
                elif echo "$line" | grep -qE "^    description:"; then
                    desc=$(echo "$line" | sed 's/.*description: *//' | tr -d '"')
                    printf "${BOLD}Description:${RESET} %s\n" "$desc"
                    in_keys=0
                    in_refs=0
                elif echo "$line" | grep -qE "^    keys:"; then
                    printf "\n${BOLD}Keys:${RESET}\n"
                    in_keys=1
                    in_refs=0
                elif echo "$line" | grep -qE "^    references:"; then
                    printf "\n${BOLD}References:${RESET}\n"
                    in_refs=1
                    in_keys=0
                elif [ $in_keys -eq 1 ] && echo "$line" | grep -qE "^      -"; then
                    key=$(echo "$line" | sed 's/^      - *//')
                    # Parse key-value
                    key_name=$(echo "$key" | sed 's/:.*$//')
                    key_value=$(echo "$key" | sed 's/^[^:]*: *//')
                    if [ "$key_name" != "$key_value" ]; then
                        printf "  ${CYAN}%s${RESET}: %s\n" "$key_name" "$key_value"
                    else
                        printf "  - %s\n" "$key"
                    fi
                elif [ $in_refs -eq 1 ] && echo "$line" | grep -qE "^      -"; then
                    ref=$(echo "$line" | sed 's/^      - *//')
                    printf "  ${DIM}->%s${RESET}\n" " $ref"
                fi
            fi
        fi
    done < "$INDEX_FILE"

    if [ $found -eq 0 ]; then
        printf "${RED}Error:${RESET} Configuration not found: %s\n" "$config_path" >&2
        # Try fuzzy search
        base_name=$(basename "$config_path")
        similar=$(grep -E "^  - path:.*$base_name" "$INDEX_FILE" 2>/dev/null | sed 's/.*path: *//' | tr -d '"' | head -5)
        if [ -n "$similar" ]; then
            printf "\n${DIM}Similar configurations:${RESET}\n"
            printf "%s\n" "$similar" | while IFS= read -r p; do
                [ -n "$p" ] && printf "  - %s\n" "$p"
            done
        fi
        return 1
    fi

    # Check if file exists
    if [ $found -eq 1 ]; then
        full_path="$PROJECT_ROOT/$config_path"
        printf "\n${BOLD}File Status:${RESET} "
        if [ -f "$full_path" ]; then
            printf "${GREEN}Exists${RESET}\n"
            # Show file size
            if command -v stat >/dev/null 2>&1; then
                # Use portable stat
                size=$(wc -c < "$full_path" | tr -d ' ')
                printf "${BOLD}Size:${RESET} %s bytes\n" "$size"
            fi
        else
            printf "${RED}Not Found${RESET}\n"
        fi
    fi

    printf "\n"
}

# Show configuration relations graph
show_relations() {
    print_header "Configuration Relations"

    printf "This view shows how configurations reference each other.\n\n"

    # Find entries with references
    in_entries=0
    current_path=""
    current_refs=""
    in_refs=0

    printf "${BOLD}Configurations with References:${RESET}\n"
    printf "%s\n" "$(printf '%.0s-' $(seq 1 60))"

    while IFS= read -r line; do
        # Check if we're in entries section
        if echo "$line" | grep -q "^entries:"; then
            in_entries=1
            continue
        fi

        # Check if we've left entries section
        if [ $in_entries -eq 1 ] && echo "$line" | grep -qE "^[a-z#]" && ! echo "$line" | grep -q "^  "; then
            # Print last entry
            if [ -n "$current_path" ] && [ -n "$current_refs" ]; then
                print_relation "$current_path" "$current_refs"
            fi
            in_entries=0
        fi

        if [ $in_entries -eq 1 ]; then
            if echo "$line" | grep -qE "^  - path:"; then
                # Print previous entry
                if [ -n "$current_path" ] && [ -n "$current_refs" ]; then
                    print_relation "$current_path" "$current_refs"
                fi
                current_path=$(echo "$line" | sed 's/.*path: *//' | tr -d '"')
                current_refs=""
                in_refs=0
            elif echo "$line" | grep -qE "^    references:"; then
                in_refs=1
            elif [ $in_refs -eq 1 ] && echo "$line" | grep -qE "^      -"; then
                ref=$(echo "$line" | sed 's/^      - *//' | tr -d '"')
                if [ -n "$ref" ]; then
                    if [ -n "$current_refs" ]; then
                        current_refs="$current_refs|$ref"
                    else
                        current_refs="$ref"
                    fi
                fi
            elif [ $in_refs -eq 1 ] && ! echo "$line" | grep -qE "^      -" && ! echo "$line" | grep -qE "^    references:"; then
                in_refs=0
            fi
        fi
    done < "$INDEX_FILE"

    printf "\n"

    # Summary of most referenced configs
    printf "${BOLD}Most Referenced Configurations:${RESET}\n"
    printf "%s\n" "$(printf '%.0s-' $(seq 1 60))"

    # Count references - only paths (containing /)
    grep -E "^      - " "$INDEX_FILE" | sed 's/^      - *//' | tr -d '"' | grep "/" | sort | uniq -c | sort -rn | head -10 | while read -r count ref; do
        if [ -n "$ref" ]; then
            printf "  %3d refs  %s\n" "$count" "$ref"
        fi
    done

    printf "\n"
}

print_relation() {
    path="$1"
    refs="$2"

    printf "\n${CYAN}%s${RESET}\n" "$path"

    # Split refs by |
    echo "$refs" | tr '|' '\n' | while read -r ref; do
        if [ -n "$ref" ]; then
            printf "  ${DIM}->%s${RESET}\n" " $ref"
        fi
    done
}

# Show help
show_help() {
    cat << EOF
Configuration Query Tool

Query and display configurations from the centralized INDEX.yaml.

Usage:
  $0 [options]

Options:
  --list-categories     List all configuration categories
  --category TYPE       List configurations of a specific type
  --search TERM         Search configurations by keyword (fuzzy match)
  --show PATH           Show detailed information about a configuration
  --relations           Show configuration reference relationships
  -h, --help            Show this help message

Examples:
  $0 --list-categories
    List all available configuration categories with counts

  $0 --category skill-config
    List all skill configuration files

  $0 --search "tdd"
    Search for configurations related to TDD

  $0 --show skills/implement/SKILL.md
    Show detailed information about a specific configuration

  $0 --relations
    Display configuration dependency graph

Categories:
  skill-config        - Skill definitions and frontmatter
  perspective-config  - Perspective configurations
  quality-config      - Quality control configurations
  coordination-config - Coordination and execution configs
  integration-config  - External tool integration configs
  metrics-config      - Metrics definitions
  schema-config       - Schema definitions
  expertise-config    - Expertise framework configs
  plugin-config       - Plugin configurations

EOF
}

# Parse arguments
parse_args() {
    if [ $# -eq 0 ]; then
        MODE="help"
        return
    fi

    while [ $# -gt 0 ]; do
        case "$1" in
            --list-categories)
                MODE="list-categories"
                shift
                ;;
            --category)
                MODE="category"
                if [ -z "$2" ] || echo "$2" | grep -q "^-"; then
                    print_error "--category requires a category ID"
                    exit 1
                fi
                CATEGORY_FILTER="$2"
                shift 2
                ;;
            --search)
                MODE="search"
                if [ -z "$2" ] || echo "$2" | grep -q "^-"; then
                    print_error "--search requires a search term"
                    exit 1
                fi
                SEARCH_TERM="$2"
                shift 2
                ;;
            --show)
                MODE="show"
                if [ -z "$2" ] || echo "$2" | grep -q "^-"; then
                    print_error "--show requires a configuration path"
                    exit 1
                fi
                SHOW_PATH="$2"
                shift 2
                ;;
            --relations)
                MODE="relations"
                shift
                ;;
            -h|--help)
                MODE="help"
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                printf "\n"
                show_help
                exit 1
                ;;
        esac
    done
}

# Main
main() {
    check_dependencies
    parse_args "$@"

    case "$MODE" in
        list-categories)
            check_index
            list_categories
            ;;
        category)
            check_index
            list_by_category "$CATEGORY_FILTER"
            ;;
        search)
            check_index
            search_configs "$SEARCH_TERM"
            ;;
        show)
            check_index
            show_config "$SHOW_PATH"
            ;;
        relations)
            check_index
            show_relations
            ;;
        help)
            show_help
            ;;
    esac
}

main "$@"
