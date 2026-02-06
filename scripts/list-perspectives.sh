#!/bin/sh

# Perspective Query Tool
# Query and display perspectives from the centralized catalog
#
# Usage:
#   ./scripts/list-perspectives.sh                    # List all perspectives
#   ./scripts/list-perspectives.sh --category plan    # Filter by category
#   ./scripts/list-perspectives.sh --skill implement  # Filter by skill
#   ./scripts/list-perspectives.sh --show tdd-enforcer # Show details
#   ./scripts/list-perspectives.sh --preset standard  # Show preset

set -euo pipefail

# Get script directory (POSIX compatible)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CATALOG_FILE="$PROJECT_ROOT/shared/perspectives/catalog.yaml"

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
MODE="list"
FILTER_CATEGORY=""
FILTER_SKILL=""
SHOW_ID=""
PRESET_NAME=""
OUTPUT_FORMAT="table"

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

# Model tier color
model_color() {
    case "$1" in
        opus)   printf "${MAGENTA}%s${RESET}" "$1" ;;
        sonnet) printf "${CYAN}%s${RESET}" "$1" ;;
        haiku)  printf "${GREEN}%s${RESET}" "$1" ;;
        *)      printf "%s" "$1" ;;
    esac
}

# Category color
category_color() {
    case "$1" in
        research)      printf "${BLUE}%s${RESET}" "$1" ;;
        plan)          printf "${CYAN}%s${RESET}" "$1" ;;
        tasks)         printf "${GREEN}%s${RESET}" "$1" ;;
        implement)     printf "${YELLOW}%s${RESET}" "$1" ;;
        review)        printf "${MAGENTA}%s${RESET}" "$1" ;;
        verify)        printf "${RED}%s${RESET}" "$1" ;;
        cross-cutting) printf "${BOLD}%s${RESET}" "$1" ;;
        *)             printf "%s" "$1" ;;
    esac
}

# Priority weight bar
priority_bar() {
    weight="$1"
    # Convert to percentage (0-10 scale)
    pct=$(echo "$weight" | awk '{printf "%d", $1 * 10}')
    filled=""
    empty=""
    i=0
    while [ $i -lt 10 ]; do
        if [ $i -lt "$pct" ]; then
            filled="${filled}#"
        else
            empty="${empty}-"
        fi
        i=$((i + 1))
    done
    printf "[${GREEN}%s${DIM}%s${RESET}]" "$filled" "$empty"
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

# Check if catalog exists
check_catalog() {
    if [ ! -f "$CATALOG_FILE" ]; then
        print_error "Catalog file not found: $CATALOG_FILE"
        exit 1
    fi
}

# Parse YAML (simple implementation for this use case)
# Extract perspectives section and parse each perspective
list_perspectives() {
    filter_cat="$1"
    filter_skill="$2"

    # Print header
    print_header "Perspectives Catalog"

    # Table header
    printf "${BOLD}%-25s %-25s %-15s %-8s %-8s %-12s${RESET}\n" \
        "ID" "NAME" "CATEGORY" "MODEL" "METHOD" "PRIORITY"
    printf "%s\n" "$(printf '%.0s-' $(seq 1 95))"

    # Parse perspectives from YAML
    # This is a simplified parser that works for the catalog structure
    in_perspectives=0
    current_id=""
    current_name=""
    current_category=""
    current_model=""
    current_method=""
    current_weight=""
    current_skills=""

    while IFS= read -r line; do
        # Check if we're in perspectives section
        if echo "$line" | grep -q "^perspectives:"; then
            in_perspectives=1
            continue
        fi

        # Check if we've left perspectives section (another top-level key)
        if [ $in_perspectives -eq 1 ] && echo "$line" | grep -qE "^[a-z_]+:"; then
            in_perspectives=0
        fi

        if [ $in_perspectives -eq 1 ]; then
            # New perspective entry
            if echo "$line" | grep -qE "^  - id:"; then
                # Print previous perspective if exists
                if [ -n "$current_id" ]; then
                    print_perspective_row "$current_id" "$current_name" "$current_category" \
                        "$current_model" "$current_method" "$current_weight" "$current_skills" \
                        "$filter_cat" "$filter_skill"
                fi
                current_id=$(echo "$line" | sed 's/.*id: *//' | tr -d '"')
                current_name=""
                current_category=""
                current_model=""
                current_method=""
                current_weight=""
                current_skills=""
            elif echo "$line" | grep -qE "^    name:"; then
                current_name=$(echo "$line" | sed 's/.*name: *//' | tr -d '"')
            elif echo "$line" | grep -qE "^    category:"; then
                current_category=$(echo "$line" | sed 's/.*category: *//' | tr -d '"')
            elif echo "$line" | grep -qE "^    model_tier:"; then
                current_model=$(echo "$line" | sed 's/.*model_tier: *//' | tr -d '"')
            elif echo "$line" | grep -qE "^    method:"; then
                current_method=$(echo "$line" | sed 's/.*method: *//' | tr -d '"')
            elif echo "$line" | grep -qE "^    priority_weight:"; then
                current_weight=$(echo "$line" | sed 's/.*priority_weight: *//' | tr -d '"')
            elif echo "$line" | grep -qE "^    applicable_skills:"; then
                # Start collecting skills
                current_skills="collecting"
            elif [ "$current_skills" = "collecting" ] && echo "$line" | grep -qE "^      -"; then
                skill=$(echo "$line" | sed 's/.*- *//' | tr -d '"')
                if [ "$current_skills" = "collecting" ]; then
                    current_skills="$skill"
                else
                    current_skills="$current_skills,$skill"
                fi
            elif [ "$current_skills" = "collecting" ] && ! echo "$line" | grep -qE "^      -"; then
                # Stop collecting skills
                : # Keep current_skills as is
            fi
        fi
    done < "$CATALOG_FILE"

    # Print last perspective
    if [ -n "$current_id" ]; then
        print_perspective_row "$current_id" "$current_name" "$current_category" \
            "$current_model" "$current_method" "$current_weight" "$current_skills" \
            "$filter_cat" "$filter_skill"
    fi

    printf "\n"
}

print_perspective_row() {
    id="$1"
    name="$2"
    category="$3"
    model="$4"
    method="$5"
    weight="$6"
    skills="$7"
    filter_cat="$8"
    filter_skill="$9"

    # Apply category filter
    if [ -n "$filter_cat" ] && [ "$category" != "$filter_cat" ]; then
        return
    fi

    # Apply skill filter
    if [ -n "$filter_skill" ]; then
        # Check if perspective applies to the skill
        # By default, perspectives apply to their category's skill
        applies=0

        if [ -n "$skills" ] && [ "$skills" != "collecting" ]; then
            # Check explicit applicable_skills
            echo "$skills" | grep -q "$filter_skill" && applies=1
        else
            # Check category default
            case "$category" in
                research)      [ "$filter_skill" = "research" ] && applies=1 ;;
                plan)          [ "$filter_skill" = "plan" ] && applies=1 ;;
                tasks)         [ "$filter_skill" = "tasks" ] && applies=1 ;;
                implement)     [ "$filter_skill" = "implement" ] && applies=1 ;;
                review)        [ "$filter_skill" = "review" ] && applies=1 ;;
                verify)        [ "$filter_skill" = "verify" ] && applies=1 ;;
                cross-cutting) applies=1 ;;  # Cross-cutting applies to all
            esac
        fi

        [ $applies -eq 0 ] && return
    fi

    # Truncate name if too long
    if [ ${#name} -gt 23 ]; then
        name="$(echo "$name" | cut -c1-22)..."
    fi

    # Format priority
    weight_display=""
    if [ -n "$weight" ]; then
        weight_display=$(priority_bar "$weight")
    fi

    # Print row with colors
    printf "%-25s %-25s " "$id" "$name"
    category_color "$category"
    printf "%-7s " ""
    model_color "$model"
    printf "%-6s " ""
    printf "%-8s " "$method"
    printf "%s\n" "$weight_display"
}

# Show detailed information about a specific perspective
show_perspective() {
    perspective_id="$1"

    print_header "Perspective: $perspective_id"

    # Parse the specific perspective
    in_perspectives=0
    in_target=0
    found=0

    current_field=""
    indent_level=0

    while IFS= read -r line; do
        # Check if we're in perspectives section
        if echo "$line" | grep -q "^perspectives:"; then
            in_perspectives=1
            continue
        fi

        # Check if we've left perspectives section
        if [ $in_perspectives -eq 1 ] && echo "$line" | grep -qE "^[a-z_]+:" && ! echo "$line" | grep -q "^  "; then
            in_perspectives=0
            in_target=0
        fi

        if [ $in_perspectives -eq 1 ]; then
            # Check for target perspective
            if echo "$line" | grep -qE "^  - id: *$perspective_id\$"; then
                in_target=1
                found=1
                printf "${BOLD}ID:${RESET} %s\n" "$perspective_id"
                continue
            fi

            # Check for next perspective (end of target)
            if [ $in_target -eq 1 ] && echo "$line" | grep -qE "^  - id:"; then
                in_target=0
                continue
            fi

            # Print fields for target perspective
            if [ $in_target -eq 1 ]; then
                # Parse field
                if echo "$line" | grep -qE "^    [a-z_]+:"; then
                    field_name=$(echo "$line" | sed 's/^    //' | sed 's/:.*//')
                    field_value=$(echo "$line" | sed 's/^[^:]*: *//' | tr -d '"')

                    case "$field_name" in
                        name)
                            printf "${BOLD}Name:${RESET} %s\n" "$field_value"
                            ;;
                        category)
                            printf "${BOLD}Category:${RESET} "
                            category_color "$field_value"
                            printf "\n"
                            ;;
                        focus)
                            printf "${BOLD}Focus:${RESET} %s\n" "$field_value"
                            ;;
                        model_tier)
                            printf "${BOLD}Model:${RESET} "
                            model_color "$field_value"
                            printf "\n"
                            ;;
                        method)
                            printf "${BOLD}Method:${RESET} %s\n" "$field_value"
                            ;;
                        priority_weight)
                            printf "${BOLD}Priority:${RESET} %s " "$field_value"
                            priority_bar "$field_value"
                            printf "\n"
                            ;;
                        responsibilities)
                            printf "\n${BOLD}Responsibilities:${RESET}\n"
                            current_field="responsibilities"
                            ;;
                        tags)
                            printf "\n${BOLD}Tags:${RESET}\n"
                            current_field="tags"
                            ;;
                        triggers)
                            printf "\n${BOLD}Triggers:${RESET}\n"
                            current_field="triggers"
                            ;;
                        applicable_skills)
                            printf "\n${BOLD}Applicable Skills:${RESET}\n"
                            current_field="applicable_skills"
                            ;;
                        output_format)
                            printf "\n${BOLD}Output Format:${RESET}\n"
                            current_field="output_format"
                            ;;
                        expertise_framework)
                            printf "${BOLD}Expertise Framework:${RESET} %s\n" "$field_value"
                            ;;
                        *)
                            current_field=""
                            ;;
                    esac
                elif echo "$line" | grep -qE "^      - "; then
                    # List item
                    item=$(echo "$line" | sed 's/^      - //' | tr -d '"')
                    printf "  - %s\n" "$item"
                elif echo "$line" | grep -qE "^        - name:"; then
                    # Output format section
                    section_name=$(echo "$line" | sed 's/.*name: *//' | tr -d '"')
                    printf "  Section: ${CYAN}%s${RESET}\n" "$section_name"
                elif echo "$line" | grep -qE "^          description:"; then
                    desc=$(echo "$line" | sed 's/.*description: *//' | tr -d '"')
                    printf "    %s\n" "$desc"
                fi
            fi
        fi
    done < "$CATALOG_FILE"

    if [ $found -eq 0 ]; then
        print_error "Perspective not found: $perspective_id"
        printf "\nAvailable perspectives:\n"
        list_perspective_ids
        exit 1
    fi

    printf "\n"
}

# List all perspective IDs
list_perspective_ids() {
    grep -E "^  - id:" "$CATALOG_FILE" | sed 's/.*id: *//' | tr -d '"' | sort
}

# Show preset information
show_preset() {
    preset_name="$1"

    print_header "Preset: $preset_name"

    in_presets=0
    in_target=0
    found=0
    current_skill=""

    while IFS= read -r line; do
        # Check if we're in presets section
        if echo "$line" | grep -q "^presets:"; then
            in_presets=1
            continue
        fi

        # Check if we've left presets section
        if [ $in_presets -eq 1 ] && echo "$line" | grep -qE "^[a-z_]+:" && ! echo "$line" | grep -q "^  "; then
            in_presets=0
            in_target=0
        fi

        if [ $in_presets -eq 1 ]; then
            # Check for target preset
            if echo "$line" | grep -qE "^  $preset_name:"; then
                in_target=1
                found=1
                printf "${BOLD}Preset:${RESET} %s\n" "$preset_name"
                continue
            fi

            # Check for next preset (end of target)
            if [ $in_target -eq 1 ] && echo "$line" | grep -qE "^  [a-z]+:" && ! echo "$line" | grep -q "by_skill"; then
                in_target=0
                continue
            fi

            if [ $in_target -eq 1 ]; then
                if echo "$line" | grep -qE "^    description:"; then
                    desc=$(echo "$line" | sed 's/.*description: *//' | tr -d '"')
                    printf "${BOLD}Description:${RESET} %s\n" "$desc"
                elif echo "$line" | grep -qE "^    perspective_count:"; then
                    count=$(echo "$line" | sed 's/.*perspective_count: *//' | tr -d '"')
                    printf "${BOLD}Perspective Count:${RESET} %s\n" "$count"
                elif echo "$line" | grep -qE "^    selection_strategy:"; then
                    strategy=$(echo "$line" | sed 's/.*selection_strategy: *//' | tr -d '"')
                    printf "${BOLD}Selection Strategy:${RESET} %s\n\n" "$strategy"
                elif echo "$line" | grep -qE "^      [a-z]+:$"; then
                    # Skill name
                    current_skill=$(echo "$line" | sed 's/^ *//' | tr -d ':')
                    printf "${BOLD}%s:${RESET}\n" "$current_skill"
                elif echo "$line" | grep -qE "^        perspectives:"; then
                    # Perspectives list (inline)
                    perspectives=$(echo "$line" | sed 's/.*perspectives: *\[//' | sed 's/\].*//' | tr -d '"' | tr ',' '\n')
                    printf "  Perspectives:\n"
                    echo "$perspectives" | while read -r p; do
                        p=$(echo "$p" | tr -d ' ')
                        [ -n "$p" ] && printf "    - %s\n" "$p"
                    done
                elif echo "$line" | grep -qE "^        rationale:"; then
                    rationale=$(echo "$line" | sed 's/.*rationale: *//' | tr -d '"')
                    printf "  Rationale: ${DIM}%s${RESET}\n\n" "$rationale"
                fi
            fi
        fi
    done < "$CATALOG_FILE"

    if [ $found -eq 0 ]; then
        print_error "Preset not found: $preset_name"
        printf "\nAvailable presets:\n"
        list_presets
        exit 1
    fi
}

# List available presets
list_presets() {
    print_header "Available Presets"

    in_presets=0

    while IFS= read -r line; do
        if echo "$line" | grep -q "^presets:"; then
            in_presets=1
            continue
        fi

        if [ $in_presets -eq 1 ] && echo "$line" | grep -qE "^[a-z_]+:" && ! echo "$line" | grep -q "^  "; then
            in_presets=0
        fi

        if [ $in_presets -eq 1 ]; then
            if echo "$line" | grep -qE "^  [a-z]+:$"; then
                preset=$(echo "$line" | sed 's/^ *//' | tr -d ':')
                printf "  - %s\n" "$preset"
            fi
        fi
    done < "$CATALOG_FILE"

    printf "\n"
}

# List available categories
list_categories() {
    print_header "Available Categories"

    in_categories=0

    while IFS= read -r line; do
        if echo "$line" | grep -q "^categories:"; then
            in_categories=1
            continue
        fi

        if [ $in_categories -eq 1 ] && echo "$line" | grep -qE "^[a-z_]+:" && ! echo "$line" | grep -q "^  "; then
            in_categories=0
        fi

        if [ $in_categories -eq 1 ]; then
            if echo "$line" | grep -qE "^  - id:"; then
                cat_id=$(echo "$line" | sed 's/.*id: *//' | tr -d '"')
            elif echo "$line" | grep -qE "^    name:"; then
                cat_name=$(echo "$line" | sed 's/.*name: *//' | tr -d '"')
            elif echo "$line" | grep -qE "^    description:"; then
                cat_desc=$(echo "$line" | sed 's/.*description: *//' | tr -d '"')
                printf "  "
                category_color "$cat_id"
                printf " - %s\n" "$cat_name"
                printf "    ${DIM}%s${RESET}\n" "$cat_desc"
            fi
        fi
    done < "$CATALOG_FILE"

    printf "\n"
}

# Show help
show_help() {
    cat << EOF
Perspective Query Tool

Usage:
  $0 [options]

Options:
  --category CAT    Filter by category (research, plan, tasks, implement, review, verify)
  --skill SKILL     Filter by applicable skill
  --show ID         Show detailed information about a perspective
  --preset NAME     Show preset configuration (quick, standard, deep, custom)
  --list-presets    List all available presets
  --list-categories List all available categories
  -h, --help        Show this help message

Examples:
  $0                           # List all perspectives
  $0 --category research       # List research perspectives
  $0 --skill implement         # List perspectives for implement skill
  $0 --show tdd-enforcer       # Show TDD enforcer details
  $0 --preset standard         # Show standard preset
  $0 --list-presets            # List all presets
  $0 --list-categories         # List all categories

Categories:
  research      - Information gathering and analysis
  plan          - Architecture and risk assessment
  tasks         - Work decomposition
  implement     - Code quality supervision
  review        - Code review
  verify        - Testing and validation
  cross-cutting - Multi-phase perspectives

EOF
}

# Parse arguments
parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --category)
                MODE="list"
                FILTER_CATEGORY="$2"
                shift 2
                ;;
            --skill)
                MODE="list"
                FILTER_SKILL="$2"
                shift 2
                ;;
            --show)
                MODE="show"
                SHOW_ID="$2"
                shift 2
                ;;
            --preset)
                MODE="preset"
                PRESET_NAME="$2"
                shift 2
                ;;
            --list-presets)
                MODE="list-presets"
                shift
                ;;
            --list-categories)
                MODE="list-categories"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Main
main() {
    check_dependencies
    check_catalog
    parse_args "$@"

    case "$MODE" in
        list)
            list_perspectives "$FILTER_CATEGORY" "$FILTER_SKILL"
            ;;
        show)
            show_perspective "$SHOW_ID"
            ;;
        preset)
            show_preset "$PRESET_NAME"
            ;;
        list-presets)
            list_presets
            ;;
        list-categories)
            list_categories
            ;;
    esac
}

main "$@"
