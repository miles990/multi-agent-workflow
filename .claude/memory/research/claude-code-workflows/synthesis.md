# Claude Code 工作流程研究

> 研究 Claude Code 官方文檔，提取適用於 multi-agent-workflow 的最佳實踐

## 1. 子代理（Subagent）最佳實踐

### 配置要點

| 欄位 | 用途 | 建議 |
|------|------|------|
| `name` | 唯一識別碼 | 小寫字母和連字號 |
| `description` | **自動委派依據** | 詳細描述，包含 "use proactively" |
| `tools` | 工具限制 | 只授予必要工具 |
| `model` | 模型選擇 | haiku/sonnet/opus/inherit |
| `permissionMode` | 權限模式 | default/plan/acceptEdits |
| `skills` | 預載技能 | 注入完整技能內容 |
| `hooks` | 生命週期掛鉤 | PreToolUse/PostToolUse/Stop |

### 模型選擇策略

| 模型 | 適用場景 |
|------|---------|
| `haiku` | 快速、唯讀任務（探索、搜尋） |
| `sonnet` | 平衡（分析、審查） |
| `opus` | 複雜推理（架構設計） |
| `inherit` | 繼承父級模型 |

### 內建子代理

| 名稱 | 模型 | 用途 |
|------|------|------|
| Explore | Haiku | 快速唯讀探索 |
| Plan | inherit | 計畫模式研究 |
| general-purpose | inherit | 複雜多步驟任務 |

## 2. Hook 事件完整清單

### 工具相關

| 事件 | 觸發時機 | 匹配器 |
|------|---------|--------|
| `PreToolUse` | 工具呼叫前 | 工具名稱 |
| `PostToolUse` | 工具呼叫後 | 工具名稱 |
| `PermissionRequest` | 權限對話框 | 工具名稱 |

### 子代理相關

| 事件 | 觸發時機 | 匹配器 |
|------|---------|--------|
| `SubagentStart` | 子代理開始 | 代理類型名稱 |
| `SubagentStop` | 子代理完成 | 代理類型名稱 |

### 會話相關

| 事件 | 觸發時機 | 用途 |
|------|---------|------|
| `SessionStart` | 會話啟動/恢復 | 載入上下文、設定環境變數 |
| `SessionEnd` | 會話結束 | 清理任務 |
| `Stop` | Claude 完成回應 | 決定是否繼續 |
| `Notification` | 發送通知 | 自訂通知 |
| `UserPromptSubmit` | 使用者提交前 | 驗證/添加上下文 |
| `PreCompact` | 壓縮前 | 自訂壓縮 |

### Hook 輸出控制

| 退出碼 | 效果 |
|--------|------|
| 0 | 成功，繼續執行 |
| 2 | **阻止執行**，stderr 回饋給 Claude |
| 其他 | 非阻止錯誤 |

## 3. 擴展思考（Extended Thinking）

### 啟用方式

1. **關鍵字觸發**：訊息中包含 `ultrathink:`
2. **快捷鍵**：`Option+T` (macOS) / `Alt+T` (Windows/Linux)
3. **全域設定**：`/config` → 啟用思考模式
4. **環境變數**：`MAX_THINKING_TOKENS=31999`

### 適用場景

- 複雜架構決策
- 困難的除錯
- 多步驟實現規劃
- 權衡分析

### Token 預算

- 啟用時：最多 31,999 tokens
- 禁用時：0 tokens
- 按 `Ctrl+O` 查看推理過程

## 4. 檔案/目錄參考

### @ 語法

```
@src/utils/auth.js      # 單個檔案（完整內容）
@src/components         # 目錄（檔案清單）
@github:repos/owner/... # MCP 資源
```

### 特點

- 檔案路徑可相對或絕對
- 自動包含該目錄的 CLAUDE.md
- 可在單個訊息中參考多個檔案

## 5. 計畫模式（Plan Mode）

### 適用場景

- 多步驟實現（編輯多個檔案）
- 程式碼探索（變更前研究）
- 互動式開發（迭代方向）

### 啟用方式

```bash
# 命令行
claude --permission-mode plan

# 會話中
Shift+Tab → 切換模式

# 無頭模式
claude --permission-mode plan -p "分析認證系統"
```

## 6. 適用於 multi-agent-workflow 的改進

### Hook 配置

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Task", "hooks": [...] }
    ],
    "PostToolUse": [
      { "matcher": "Write", "hooks": [...] },
      { "matcher": "Task", "hooks": [...] }
    ],
    "SubagentStart": [
      { "hooks": [...] }
    ],
    "SubagentStop": [
      { "hooks": [...] }
    ]
  }
}
```

### 子代理設計建議

| 視角 | 模型 | 工具 |
|------|------|------|
| 架構分析師 | sonnet | Read, Glob, Grep |
| 認知研究員 | sonnet | Read, Glob, Grep, WebFetch |
| 工作流設計 | haiku | Read, Glob, Grep |
| 業界實踐 | haiku | Read, Glob, WebFetch |

### 擴展思考整合

在複雜分析階段（RESEARCH, PLAN）的 prompt 中加入：
```
ultrathink: 分析 {topic} 的架構設計模式...
```

## 7. 參考連結

- [常見工作流程](https://code.claude.com/docs/zh-TW/common-workflows)
- [子代理文檔](https://code.claude.com/docs/zh-TW/sub-agents)
- [Hooks 指南](https://code.claude.com/docs/zh-TW/hooks-guide)
- [Hooks 參考](https://code.claude.com/docs/zh-TW/hooks)
