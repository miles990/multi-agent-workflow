#!/bin/sh
# Skill 結構驗證工具
# 用途: 驗證 Skills 目錄結構完整性
#
# 使用方式:
#   ./scripts/validate-skills.sh              # 驗證所有 Skills
#   ./scripts/validate-skills.sh research     # 驗證單一 Skill
#   ./scripts/validate-skills.sh --ci         # CI 模式 (嚴格)

set -euo pipefail

# 顏色定義 (POSIX 相容)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# 配置
SKILLS_DIR="$(cd "$(dirname "$0")/.." && pwd)/skills"
CI_MODE=0
TARGET_SKILL=""

# 解析參數
if [ $# -gt 0 ]; then
    case "$1" in
        --ci)
            CI_MODE=1
            ;;
        -*)
            printf "${RED}未知選項: %s${NC}\n" "$1" >&2
            printf "使用方式: %s [skill_name|--ci]\n" "$0" >&2
            exit 1
            ;;
        *)
            TARGET_SKILL="$1"
            ;;
    esac
fi

# 檢查 skills 目錄是否存在
if [ ! -d "$SKILLS_DIR" ]; then
    printf "${RED}錯誤: Skills 目錄不存在: %s${NC}\n" "$SKILLS_DIR" >&2
    exit 1
fi

# 驗證單一 Skill
validate_skill() {
    local skill_name="$1"
    local skill_path="$SKILLS_DIR/$skill_name"
    local has_error=0
    local error_msgs=""

    # 檢查目錄存在
    if [ ! -d "$skill_path" ]; then
        printf "${RED}✗ %s - 目錄不存在${NC}\n" "$skill_name"
        return 1
    fi

    # 1. 檢查 SKILL.md 存在
    if [ ! -f "$skill_path/SKILL.md" ]; then
        has_error=1
        error_msgs="${error_msgs}  ${RED}✗${NC} 缺少 SKILL.md\n"
    fi

    # 2. 檢查 frontmatter 完整性 (name, description, version)
    if [ -f "$skill_path/SKILL.md" ]; then
        # 提取 frontmatter (--- 之間的內容)
        frontmatter=$(awk '/^---$/{flag=!flag;next}flag' "$skill_path/SKILL.md" | head -20)

        if ! echo "$frontmatter" | grep -q "^name:"; then
            has_error=1
            error_msgs="${error_msgs}  ${RED}✗${NC} SKILL.md 缺少 'name' 欄位\n"
        fi

        if ! echo "$frontmatter" | grep -q "^description:"; then
            has_error=1
            error_msgs="${error_msgs}  ${RED}✗${NC} SKILL.md 缺少 'description' 欄位\n"
        fi

        if ! echo "$frontmatter" | grep -q "^version:"; then
            has_error=1
            error_msgs="${error_msgs}  ${RED}✗${NC} SKILL.md 缺少 'version' 欄位\n"
        fi
    fi

    # 3. 檢查 00-quickstart (目錄或 _base/usage.md)
    if [ ! -d "$skill_path/00-quickstart" ]; then
        has_error=1
        error_msgs="${error_msgs}  ${RED}✗${NC} 缺少 00-quickstart 目錄\n"
    elif [ ! -f "$skill_path/00-quickstart/_base/usage.md" ]; then
        has_error=1
        error_msgs="${error_msgs}  ${RED}✗${NC} 缺少 00-quickstart/_base/usage.md\n"
    fi

    # 4. 檢查 01-perspectives (目錄或 _base/default-perspectives.md)
    if [ ! -d "$skill_path/01-perspectives" ]; then
        has_error=1
        error_msgs="${error_msgs}  ${RED}✗${NC} 缺少 01-perspectives 目錄\n"
    elif [ ! -f "$skill_path/01-perspectives/_base/default-perspectives.md" ]; then
        has_error=1
        error_msgs="${error_msgs}  ${RED}✗${NC} 缺少 01-perspectives/_base/default-perspectives.md\n"
    fi

    # 輸出結果
    if [ $has_error -eq 0 ]; then
        printf "${GREEN}✓${NC} %s - 結構正確\n" "$skill_name"
        if [ "$TARGET_SKILL" != "" ]; then
            printf "  ${GREEN}✓${NC} SKILL.md: frontmatter 完整\n"
            printf "  ${GREEN}✓${NC} 00-quickstart: 存在\n"
            printf "  ${GREEN}✓${NC} 01-perspectives: 存在\n"
        fi
        return 0
    else
        printf "${RED}✗${NC} %s - 結構錯誤\n" "$skill_name"
        printf "%b" "$error_msgs"

        # CI 模式下顯示修復指引
        if [ $CI_MODE -eq 1 ] || [ "$TARGET_SKILL" != "" ]; then
            printf "\n${YELLOW}修復指引:${NC}\n"
            printf "  1. 確保存在 SKILL.md，並包含 frontmatter (name, description, version)\n"
            printf "  2. 建立 00-quickstart/_base/usage.md\n"
            printf "  3. 建立 01-perspectives/_base/default-perspectives.md\n"
        fi

        return 1
    fi
}

# 取得所有 Skills
get_all_skills() {
    # 列出所有包含 SKILL.md 的子目錄
    find "$SKILLS_DIR" -maxdepth 2 -name "SKILL.md" -type f | while read -r skill_md; do
        dirname "$skill_md" | xargs basename
    done | sort
}

# 主邏輯
main() {
    local total=0
    local passed=0
    local failed=0

    if [ "$TARGET_SKILL" != "" ]; then
        # 驗證單一 Skill
        if validate_skill "$TARGET_SKILL"; then
            exit 0
        else
            exit 1
        fi
    else
        # 驗證所有 Skills
        if [ $CI_MODE -eq 0 ]; then
            printf "${BLUE}驗證所有 Skills...${NC}\n\n"
        fi

        # 取得所有 Skills
        skills=$(get_all_skills)

        if [ -z "$skills" ]; then
            printf "${YELLOW}警告: 沒有找到任何 Skills${NC}\n"
            exit 0
        fi

        # 逐一驗證
        for skill in $skills; do
            total=$((total + 1))
            if validate_skill "$skill"; then
                passed=$((passed + 1))
            else
                failed=$((failed + 1))
            fi
        done

        # 輸出統計
        printf "\n${BLUE}結果: %d/%d 通過${NC}" "$passed" "$total"

        if [ $failed -gt 0 ]; then
            printf " ${RED}(%d 失敗)${NC}\n" "$failed"
            exit 1
        else
            printf " ${GREEN}(全部通過)${NC}\n"
            exit 0
        fi
    fi
}

main
