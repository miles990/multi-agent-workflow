# Agent 通訊與記錄系統

> Claude Code 環境下的 Agent 通訊與執行記錄完整實作

## 快速開始

### 1. 安裝 Hooks

```bash
# 執行安裝腳本
./shared/tools/hooks/install-hooks.sh

# 或手動複製
cp shared/tools/hooks/*.sh ~/.claude/hooks/
```

### 2. 初始化 Workflow

```bash
# 使用 shell 腳本
./shared/tools/workflow-init.sh init my-research research "研究主題"

# 或使用 Node.js
node shared/communication/message-queue.js init my-research research "研究主題"
```

### 3. 註冊 Agent

```bash
./shared/tools/workflow-init.sh register agent_arch architecture
./shared/tools/workflow-init.sh register agent_cog cognitive
```

### 4. 發送訊息

```bash
./shared/tools/workflow-init.sh send agent_arch task_assign '{"task":"分析系統架構"}'
```

## 目錄結構

```
.claude/workflow/{workflow-id}/
├── channel/                      # 通訊頻道
│   ├── broadcast.jsonl           # 廣播訊息
│   ├── orchestrator.jsonl        # Orchestrator 訊息
│   └── agents/
│       ├── {agent-id}.jsonl      # Agent 訊息佇列
│       └── {agent-id}.ack        # ACK 記錄
├── state/
│   ├── agents.json               # Agent 註冊表
│   └── heartbeat/
│       └── {agent-id}.ts         # 心跳時間戳
└── logs/
    ├── events.jsonl              # 事件日誌
    └── errors.jsonl              # 錯誤日誌
```

## 核心組件

### 1. Agent 通訊協定 (`agent-protocol.md`)

- 訊息格式定義
- ACK 機制
- 輪詢策略
- 錯誤處理

### 2. 執行記錄系統 (`execution-logs.md`)

- Hook-based 攔截
- 事件格式
- 寫入策略
- 效能優化

### 3. 工具腳本

| 腳本 | 用途 |
|------|------|
| `workflow-init.sh` | Workflow 管理 CLI |
| `message-queue.js` | Node.js 訊息佇列 |
| `log-tool-pre.sh` | PreToolUse Hook |
| `log-tool-post.sh` | PostToolUse Hook |
| `log-agent-lifecycle.sh` | Agent 生命週期 Hook |

## Hook 配置

將以下內容加入 `~/.claude/settings.json`：

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "$HOME/.claude/hooks/log-tool-pre.sh"
      }]
    }],
    "PostToolUse": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "$HOME/.claude/hooks/log-tool-post.sh"
      }]
    }],
    "SubagentStart": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "LIFECYCLE_EVENT=start $HOME/.claude/hooks/log-agent-lifecycle.sh"
      }]
    }],
    "SubagentStop": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "LIFECYCLE_EVENT=stop $HOME/.claude/hooks/log-agent-lifecycle.sh"
      }]
    }]
  }
}
```

## 訊息類型

| Type | 用途 | Requires ACK |
|------|------|--------------|
| `task_assign` | 指派任務 | Yes |
| `task_complete` | 任務完成 | Yes |
| `progress_update` | 進度更新 | No |
| `checkpoint_request` | 同步檢查 | Yes |
| `broadcast` | 廣播訊息 | No |
| `heartbeat` | 心跳確認 | No |
| `abort` | 中止任務 | Yes |

## 效能建議

### 1. 過濾高頻工具

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash|Edit|Write|Task",
      "hooks": [...]
    }]
  }
}
```

### 2. 批量寫入

對於非關鍵事件，使用批量寫入減少 I/O：

```yaml
write_strategy:
  critical_events:
    mode: sync
  normal_events:
    mode: batch
    buffer_size: 10
```

### 3. 日誌輪換

```bash
# 手動清理
./shared/tools/workflow-init.sh cleanup old_workflow

# 或設置自動歸檔
```

## 查詢日誌

```bash
# 查看所有事件
jq '.' .claude/workflow/*/logs/events.jsonl

# 查看錯誤
jq 'select(.status == "failed")' .claude/workflow/*/logs/events.jsonl

# 統計工具呼叫
jq -s 'group_by(.tool_name) | map({tool: .[0].tool_name, count: length})' \
  .claude/workflow/*/logs/events.jsonl

# 查看特定 Agent
jq 'select(.agent_id == "agent_arch")' .claude/workflow/*/logs/events.jsonl
```

## 整合到現有 Skill

在 Map Phase 啟動前初始化 workflow：

```markdown
## 執行流程

1. 初始化 workflow
   ```bash
   ./shared/tools/workflow-init.sh init {id} {type} {topic}
   ```

2. 為每個視角註冊 Agent
   ```bash
   ./shared/tools/workflow-init.sh register agent_{perspective} {perspective}
   ```

3. 啟動並行 Task（已有的 Task tool 呼叫）

4. Hooks 自動記錄所有操作

5. Reduce Phase 讀取結果時可參考日誌
```

## 相關文件

- [Agent 通訊協定](./agent-protocol.md)
- [執行記錄系統](./execution-logs.md)
- [Map Phase](../coordination/map-phase.md)
- [Reduce Phase](../coordination/reduce-phase.md)
