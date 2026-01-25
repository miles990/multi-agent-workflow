#!/bin/bash
# =============================================================================
# install-hooks.sh - 安裝 Hooks 到 Claude Code
#
# 位置: shared/tools/hooks/install-hooks.sh
# 用途: 將 hook 腳本安裝到 ~/.claude/hooks/ 並更新 settings.json
# =============================================================================

set -euo pipefail

# 顏色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 路徑
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
HOOKS_DIR="$CLAUDE_DIR/hooks"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"

echo -e "${BLUE}安裝 Multi-Agent Workflow Hooks${NC}"
echo ""

# 創建 hooks 目錄
mkdir -p "$HOOKS_DIR"

# 複製 hook 腳本
echo -e "${BLUE}[1/3] 複製 hook 腳本...${NC}"

cp "$SCRIPT_DIR/log-tool-pre.sh" "$HOOKS_DIR/"
cp "$SCRIPT_DIR/log-tool-post.sh" "$HOOKS_DIR/"
cp "$SCRIPT_DIR/log-agent-lifecycle.sh" "$HOOKS_DIR/"

chmod +x "$HOOKS_DIR/log-tool-pre.sh"
chmod +x "$HOOKS_DIR/log-tool-post.sh"
chmod +x "$HOOKS_DIR/log-agent-lifecycle.sh"

echo -e "${GREEN}  已複製 3 個 hook 腳本${NC}"

# 備份現有 settings
echo -e "${BLUE}[2/3] 更新 settings.json...${NC}"

if [ -f "$SETTINGS_FILE" ]; then
    cp "$SETTINGS_FILE" "${SETTINGS_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${YELLOW}  已備份現有 settings.json${NC}"
fi

# 更新 settings.json
# 使用 jq 合併 hooks 配置
HOOKS_CONFIG='{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/log-tool-pre.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/log-tool-post.sh"
          }
        ]
      }
    ],
    "SubagentStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "LIFECYCLE_EVENT=start $HOME/.claude/hooks/log-agent-lifecycle.sh"
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "LIFECYCLE_EVENT=stop $HOME/.claude/hooks/log-agent-lifecycle.sh"
          }
        ]
      }
    ]
  }
}'

if [ -f "$SETTINGS_FILE" ]; then
    # 合併現有設定
    TMP_FILE=$(mktemp)
    jq --argjson new_hooks "$(echo "$HOOKS_CONFIG" | jq '.hooks')" \
       '.hooks = (.hooks // {}) * $new_hooks' \
       "$SETTINGS_FILE" > "$TMP_FILE" && mv "$TMP_FILE" "$SETTINGS_FILE"
else
    # 創建新的 settings.json
    echo "$HOOKS_CONFIG" > "$SETTINGS_FILE"
fi

echo -e "${GREEN}  已更新 hooks 配置${NC}"

# 驗證
echo -e "${BLUE}[3/3] 驗證安裝...${NC}"

ERRORS=0

for hook in "log-tool-pre.sh" "log-tool-post.sh" "log-agent-lifecycle.sh"; do
    if [ -x "$HOOKS_DIR/$hook" ]; then
        echo -e "${GREEN}  ✓ $hook${NC}"
    else
        echo -e "${YELLOW}  ✗ $hook (未找到或不可執行)${NC}"
        ((ERRORS++))
    fi
done

if jq -e '.hooks.PreToolUse' "$SETTINGS_FILE" > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ PreToolUse hook 已配置${NC}"
else
    echo -e "${YELLOW}  ✗ PreToolUse hook 未配置${NC}"
    ((ERRORS++))
fi

if jq -e '.hooks.PostToolUse' "$SETTINGS_FILE" > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ PostToolUse hook 已配置${NC}"
else
    echo -e "${YELLOW}  ✗ PostToolUse hook 未配置${NC}"
    ((ERRORS++))
fi

if jq -e '.hooks.SubagentStart' "$SETTINGS_FILE" > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ SubagentStart hook 已配置${NC}"
else
    echo -e "${YELLOW}  ✗ SubagentStart hook 未配置${NC}"
    ((ERRORS++))
fi

if jq -e '.hooks.SubagentStop' "$SETTINGS_FILE" > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ SubagentStop hook 已配置${NC}"
else
    echo -e "${YELLOW}  ✗ SubagentStop hook 未配置${NC}"
    ((ERRORS++))
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}安裝完成！${NC}"
    echo ""
    echo "Hook 腳本位置: $HOOKS_DIR/"
    echo "設定檔位置: $SETTINGS_FILE"
    echo ""
    echo "要啟用記錄，請在專案中執行："
    echo "  ./shared/tools/workflow-init.sh init <workflow_id> <type> <topic>"
else
    echo -e "${YELLOW}安裝完成，但有 $ERRORS 個警告${NC}"
fi
