#!/bin/bash

# Skill 腳手架工具
# 用於快速建立新的 Skill 結構
#
# 用法:
#   ./scripts/create-skill.sh                    # 互動模式
#   ./scripts/create-skill.sh --non-interactive  # 非互動模式（CI）

set -euo pipefail

# 顏色定義
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    RESET='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    CYAN=''
    BOLD=''
    RESET=''
fi

# 取得腳本所在目錄（處理符號連結）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 目錄定義
SKILLS_DIR="$PROJECT_ROOT/skills"
TEMPLATES_DIR="$PROJECT_ROOT/shared/skill-structure/templates"

# 預設值
SKILL_NAME=""
SKILL_DESC=""
AUTHOR=""
NON_INTERACTIVE=0

# 輔助函數
log_info() {
    echo -e "${BLUE}ℹ${RESET} $1"
}

log_success() {
    echo -e "${GREEN}✓${RESET} $1"
}

log_error() {
    echo -e "${RED}✗${RESET} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}⚠${RESET} $1"
}

log_section() {
    echo ""
    echo -e "${CYAN}${BOLD}=== $1 ===${RESET}"
    echo ""
}

# 驗證 kebab-case 格式
validate_skill_name() {
    local name="$1"

    # 檢查是否為空
    if [[ -z "$name" ]]; then
        log_error "Skill 名稱不能為空"
        return 1
    fi

    # 檢查格式：只允許小寫字母、數字和連字號，且不能以連字號開頭或結尾
    if [[ ! "$name" =~ ^[a-z][a-z0-9-]*[a-z0-9]$ ]] && [[ ! "$name" =~ ^[a-z]$ ]]; then
        log_error "Skill 名稱必須使用 kebab-case 格式（小寫字母、數字、連字號，不能以連字號開頭或結尾）"
        log_error "範例: my-new-skill, data-processor, ai-agent"
        return 1
    fi

    # 檢查是否已存在
    if [[ -d "$SKILLS_DIR/$name" ]]; then
        log_error "Skill '$name' 已存在於 $SKILLS_DIR/$name"
        return 1
    fi

    return 0
}

# 處理命令列參數
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --name)
                SKILL_NAME="$2"
                shift 2
                ;;
            --desc|--description)
                SKILL_DESC="$2"
                shift 2
                ;;
            --author)
                AUTHOR="$2"
                shift 2
                ;;
            --non-interactive)
                NON_INTERACTIVE=1
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知參數: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 顯示幫助訊息
show_help() {
    cat << EOF
Skill 腳手架工具

用法:
  $0 [選項]

選項:
  --name NAME              Skill 名稱（kebab-case）
  --desc DESCRIPTION       Skill 描述
  --author AUTHOR          作者名稱
  --non-interactive        非互動模式（CI 使用）
  -h, --help              顯示此幫助訊息

互動模式範例:
  $0

非互動模式範例:
  $0 --name my-skill --desc "我的新 Skill" --author "Your Name" --non-interactive

EOF
}

# 互動式輸入
interactive_input() {
    log_section "Skill 腳手架工具"

    # 輸入 Skill 名稱
    while true; do
        read -p "Skill 名稱 (kebab-case): " SKILL_NAME
        if validate_skill_name "$SKILL_NAME"; then
            break
        fi
        echo ""
    done

    # 輸入描述
    read -p "Skill 描述: " SKILL_DESC
    if [[ -z "$SKILL_DESC" ]]; then
        SKILL_DESC="新的 Skill"
    fi

    # 輸入作者
    read -p "作者: " AUTHOR
    if [[ -z "$AUTHOR" ]]; then
        # 嘗試從 git config 取得
        if command -v git &> /dev/null; then
            AUTHOR=$(git config user.name 2>/dev/null || echo "Unknown")
        else
            AUTHOR="Unknown"
        fi
    fi

    echo ""
}

# 驗證非互動模式輸入
validate_non_interactive() {
    local valid=1

    if [[ -z "$SKILL_NAME" ]]; then
        log_error "非互動模式必須提供 --name 參數"
        valid=0
    elif ! validate_skill_name "$SKILL_NAME"; then
        valid=0
    fi

    if [[ -z "$SKILL_DESC" ]]; then
        SKILL_DESC="新的 Skill"
    fi

    if [[ -z "$AUTHOR" ]]; then
        if command -v git &> /dev/null; then
            AUTHOR=$(git config user.name 2>/dev/null || echo "Unknown")
        else
            AUTHOR="Unknown"
        fi
    fi

    if [[ $valid -eq 0 ]]; then
        echo ""
        show_help
        return 1
    fi

    return 0
}

# 替換模板變數
replace_template_vars() {
    local file="$1"
    local skill_name="$2"
    local skill_desc="$3"
    local author="$4"

    # 生成標題格式的 Skill Name（首字母大寫）
    local skill_title
    skill_title=$(echo "$skill_name" | sed 's/-/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2));}1')

    # 替換變數
    sed -i.bak \
        -e "s/{{skill-name}}/$skill_name/g" \
        -e "s/{{Skill Name}}/$skill_title/g" \
        -e "s/{{簡短的一句話描述}}/$skill_desc/g" \
        -e "s/{{作者}}/$author/g" \
        -e "s/{{author}}/$author/g" \
        "$file"

    # 刪除備份檔
    rm -f "${file}.bak"
}

# 建立目錄結構
create_structure() {
    local skill_dir="$SKILLS_DIR/$SKILL_NAME"

    log_section "生成 Skill 結構"

    # 檢查模板目錄是否存在
    if [[ ! -d "$TEMPLATES_DIR" ]]; then
        log_error "模板目錄不存在: $TEMPLATES_DIR"
        return 1
    fi

    # 建立主目錄
    log_info "建立目錄: $skill_dir"
    mkdir -p "$skill_dir"

    # 建立子目錄
    mkdir -p "$skill_dir/00-quickstart/_base"
    mkdir -p "$skill_dir/01-perspectives/_base"
    mkdir -p "$skill_dir/templates"

    # 複製並處理模板
    log_info "處理模板檔案..."

    # SKILL.md
    if [[ -f "$TEMPLATES_DIR/SKILL.md.template" ]]; then
        cp "$TEMPLATES_DIR/SKILL.md.template" "$skill_dir/SKILL.md"
        replace_template_vars "$skill_dir/SKILL.md" "$SKILL_NAME" "$SKILL_DESC" "$AUTHOR"
        log_success "SKILL.md"
    fi

    # quickstart/usage.md
    if [[ -f "$TEMPLATES_DIR/quickstart.md.template" ]]; then
        cp "$TEMPLATES_DIR/quickstart.md.template" "$skill_dir/00-quickstart/_base/usage.md"
        replace_template_vars "$skill_dir/00-quickstart/_base/usage.md" "$SKILL_NAME" "$SKILL_DESC" "$AUTHOR"
        log_success "00-quickstart/_base/usage.md"
    fi

    # perspectives/default-perspectives.md
    if [[ -f "$TEMPLATES_DIR/perspectives.md.template" ]]; then
        cp "$TEMPLATES_DIR/perspectives.md.template" "$skill_dir/01-perspectives/_base/default-perspectives.md"
        replace_template_vars "$skill_dir/01-perspectives/_base/default-perspectives.md" "$SKILL_NAME" "$SKILL_DESC" "$AUTHOR"
        log_success "01-perspectives/_base/default-perspectives.md"
    fi

    # custom-perspectives.md
    if [[ -f "$TEMPLATES_DIR/custom-perspectives.md.template" ]]; then
        cp "$TEMPLATES_DIR/custom-perspectives.md.template" "$skill_dir/01-perspectives/_base/custom-perspectives.md"
        replace_template_vars "$skill_dir/01-perspectives/_base/custom-perspectives.md" "$SKILL_NAME" "$SKILL_DESC" "$AUTHOR"
        log_success "01-perspectives/_base/custom-perspectives.md"
    fi

    echo ""
    log_success "Skill 結構建立完成！"
}

# 顯示後續步驟
show_next_steps() {
    local skill_dir="skills/$SKILL_NAME"

    log_section "下一步"

    cat << EOF
1. 編輯 ${BOLD}$skill_dir/SKILL.md${RESET}
   - 定義執行流程（Phases）
   - 配置角色和視角
   - 設定品質閘門
   - 填寫實際的指令和參數

2. 配置視角
   - 編輯 ${BOLD}$skill_dir/01-perspectives/_base/default-perspectives.md${RESET}
   - 定義預設視角的角色、重點和 Prompt 模板

3. 編輯快速入門
   - 更新 ${BOLD}$skill_dir/00-quickstart/_base/usage.md${RESET}
   - 提供實用的使用範例

4. 執行驗證（可選）
   ${CYAN}cd $PROJECT_ROOT && ./shared/skill-structure/validate.sh $skill_dir${RESET}

5. 測試 Skill
   - 在 Claude Code 中測試新 Skill
   - 確認所有流程運作正常

6. 提交變更
   ${CYAN}git add $skill_dir${RESET}
   ${CYAN}git commit -m "feat(skill): add $SKILL_NAME skill"${RESET}

EOF
}

# 主函數
main() {
    # 解析參數
    parse_args "$@"

    # 互動或驗證輸入
    if [[ $NON_INTERACTIVE -eq 0 ]]; then
        interactive_input
    else
        if ! validate_non_interactive; then
            exit 1
        fi
        log_info "非互動模式"
        log_info "Skill: $SKILL_NAME"
        log_info "描述: $SKILL_DESC"
        log_info "作者: $AUTHOR"
        echo ""
    fi

    # 建立結構
    if ! create_structure; then
        exit 1
    fi

    # 顯示後續步驟
    show_next_steps
}

# 執行
main "$@"
