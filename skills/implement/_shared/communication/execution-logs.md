# 執行記錄系統（Execution Logs）

> Hook-based 攔截與結構化記錄

## 概述

透過 Claude Code Hooks 攔截 Agent 操作，產生結構化的執行記錄，用於：
- **可追溯性**：了解 Agent 做了什麼
- **除錯**：問題發生時回溯
- **審計**：驗證 Agent 行為符合預期
- **效能分析**：識別瓶頸

## Hook 類型

Claude Code 支援的 Hooks：

| Hook | 觸發時機 | 用途 |
|------|----------|------|
| `PreToolUse` | 工具呼叫前 | 記錄意圖、攔截危險操作 |
| `PostToolUse` | 工具呼叫後 | 記錄結果、追蹤變更 |
| `SubagentStart` | Subagent 啟動 | 記錄 Agent 生命週期 |
| `SubagentStop` | Subagent 結束 | 記錄完成狀態 |
| `SessionStart` | Session 開始 | 初始化記錄環境 |
| `Notification` | 通知事件 | 記錄重要通知 |

## 記錄格式

### 事件記錄（JSONL）

```json
{
  "id": "evt_20250125_143022_001",
  "timestamp": "2025-01-25T14:30:22.456Z",
  "session_id": "sess_abc123",
  "workflow_id": "research_user-auth",
  "agent_id": "agent_architecture",
  "event_type": "tool_call",
  "tool_name": "Read",
  "phase": "pre",
  "data": {
    "file_path": "/project/src/auth/login.ts"
  },
  "duration_ms": null,
  "status": "pending"
}
```

### 事件類型

| event_type | 說明 |
|------------|------|
| `agent_start` | Agent 啟動 |
| `agent_stop` | Agent 結束 |
| `tool_call` | 工具呼叫（pre/post） |
| `message` | 訊息傳送/接收 |
| `checkpoint` | 同步檢查點 |
| `error` | 錯誤發生 |
| `state_change` | 狀態變更 |

### 工具呼叫記錄

**Pre-call（呼叫前）**：

```json
{
  "event_type": "tool_call",
  "phase": "pre",
  "tool_name": "Bash",
  "data": {
    "command": "npm test",
    "timeout": 120000
  }
}
```

**Post-call（呼叫後）**：

```json
{
  "event_type": "tool_call",
  "phase": "post",
  "tool_name": "Bash",
  "data": {
    "command": "npm test",
    "exit_code": 0,
    "stdout_lines": 45,
    "stderr_lines": 0
  },
  "duration_ms": 3456,
  "status": "success"
}
```

## Hook 實作

### settings.json 配置

```json
{
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
            "command": "$HOME/.claude/hooks/log-agent-start.sh"
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
            "command": "$HOME/.claude/hooks/log-agent-stop.sh"
          }
        ]
      }
    ]
  }
}
```

### 環境變數

Hooks 可存取的環境變數：

| 變數 | 說明 | 範例 |
|------|------|------|
| `CLAUDE_SESSION_ID` | Session ID | `sess_abc123` |
| `CLAUDE_PROJECT_DIR` | 專案目錄 | `/Users/user/project` |
| `CLAUDE_TOOL_NAME` | 工具名稱 | `Bash` |
| `CLAUDE_TOOL_INPUT` | 工具輸入（JSON） | `{"command":"npm test"}` |
| `CLAUDE_TOOL_OUTPUT` | 工具輸出（PostToolUse） | `...` |
| `CLAUDE_SUBAGENT_ID` | Subagent ID | `subagent_001` |
| `CLAUDE_SUBAGENT_PROMPT` | Subagent prompt | `...` |

## 記錄腳本

### log-tool-pre.sh

```bash
#!/bin/bash
# 位置: ~/.claude/hooks/log-tool-pre.sh
# 用途: 記錄工具呼叫前的狀態

set -euo pipefail

# 配置
WORKFLOW_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude/workflow"
LOG_FILE="${WORKFLOW_DIR}/logs/events.jsonl"

# 確保目錄存在
mkdir -p "$(dirname "$LOG_FILE")"

# 生成事件 ID
EVENT_ID="evt_$(date +%Y%m%d_%H%M%S)_$(openssl rand -hex 3)"

# 解析 workflow ID（如果存在）
WORKFLOW_ID=""
if [ -f "${WORKFLOW_DIR}/current.json" ]; then
    WORKFLOW_ID=$(jq -r '.workflow_id // ""' "${WORKFLOW_DIR}/current.json" 2>/dev/null || echo "")
fi

# 構建事件記錄
cat >> "$LOG_FILE" << EOF
{"id":"${EVENT_ID}","timestamp":"$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)","session_id":"${CLAUDE_SESSION_ID:-unknown}","workflow_id":"${WORKFLOW_ID}","event_type":"tool_call","phase":"pre","tool_name":"${CLAUDE_TOOL_NAME:-unknown}","data":${CLAUDE_TOOL_INPUT:-null},"status":"pending"}
EOF

# 輸出事件 ID（供 post hook 關聯）
echo "EVENT_ID=${EVENT_ID}" > "/tmp/claude_event_${CLAUDE_SESSION_ID:-$$}.tmp"

exit 0
```

### log-tool-post.sh

```bash
#!/bin/bash
# 位置: ~/.claude/hooks/log-tool-post.sh
# 用途: 記錄工具呼叫後的結果

set -euo pipefail

# 配置
WORKFLOW_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude/workflow"
LOG_FILE="${WORKFLOW_DIR}/logs/events.jsonl"

# 確保目錄存在
mkdir -p "$(dirname "$LOG_FILE")"

# 生成事件 ID
EVENT_ID="evt_$(date +%Y%m%d_%H%M%S)_$(openssl rand -hex 3)"

# 解析 workflow ID
WORKFLOW_ID=""
if [ -f "${WORKFLOW_DIR}/current.json" ]; then
    WORKFLOW_ID=$(jq -r '.workflow_id // ""' "${WORKFLOW_DIR}/current.json" 2>/dev/null || echo "")
fi

# 計算輸出摘要（避免記錄過大）
OUTPUT_SUMMARY=""
if [ -n "${CLAUDE_TOOL_OUTPUT:-}" ]; then
    OUTPUT_LENGTH=${#CLAUDE_TOOL_OUTPUT}
    if [ $OUTPUT_LENGTH -gt 500 ]; then
        OUTPUT_SUMMARY="[truncated: ${OUTPUT_LENGTH} chars]"
    else
        OUTPUT_SUMMARY="${CLAUDE_TOOL_OUTPUT}"
    fi
fi

# 判斷狀態
STATUS="success"
if [ "${CLAUDE_TOOL_EXIT_CODE:-0}" != "0" ]; then
    STATUS="failed"
fi

# 構建事件記錄
cat >> "$LOG_FILE" << EOF
{"id":"${EVENT_ID}","timestamp":"$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)","session_id":"${CLAUDE_SESSION_ID:-unknown}","workflow_id":"${WORKFLOW_ID}","event_type":"tool_call","phase":"post","tool_name":"${CLAUDE_TOOL_NAME:-unknown}","data":{"output_summary":"${OUTPUT_SUMMARY}","exit_code":${CLAUDE_TOOL_EXIT_CODE:-0}},"duration_ms":${CLAUDE_TOOL_DURATION_MS:-0},"status":"${STATUS}"}
EOF

exit 0
```

### log-agent-start.sh

```bash
#!/bin/bash
# 位置: ~/.claude/hooks/log-agent-start.sh
# 用途: 記錄 Subagent 啟動

set -euo pipefail

WORKFLOW_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude/workflow"
LOG_FILE="${WORKFLOW_DIR}/logs/events.jsonl"

mkdir -p "$(dirname "$LOG_FILE")"

EVENT_ID="evt_$(date +%Y%m%d_%H%M%S)_$(openssl rand -hex 3)"

# 解析 workflow ID
WORKFLOW_ID=""
if [ -f "${WORKFLOW_DIR}/current.json" ]; then
    WORKFLOW_ID=$(jq -r '.workflow_id // ""' "${WORKFLOW_DIR}/current.json" 2>/dev/null || echo "")
fi

# 提取 prompt 摘要
PROMPT_SUMMARY=""
if [ -n "${CLAUDE_SUBAGENT_PROMPT:-}" ]; then
    PROMPT_SUMMARY=$(echo "${CLAUDE_SUBAGENT_PROMPT}" | head -c 200)
fi

cat >> "$LOG_FILE" << EOF
{"id":"${EVENT_ID}","timestamp":"$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)","session_id":"${CLAUDE_SESSION_ID:-unknown}","workflow_id":"${WORKFLOW_ID}","event_type":"agent_start","agent_id":"${CLAUDE_SUBAGENT_ID:-unknown}","data":{"prompt_summary":"${PROMPT_SUMMARY}"},"status":"started"}
EOF

exit 0
```

### log-agent-stop.sh

```bash
#!/bin/bash
# 位置: ~/.claude/hooks/log-agent-stop.sh
# 用途: 記錄 Subagent 結束

set -euo pipefail

WORKFLOW_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude/workflow"
LOG_FILE="${WORKFLOW_DIR}/logs/events.jsonl"

mkdir -p "$(dirname "$LOG_FILE")"

EVENT_ID="evt_$(date +%Y%m%d_%H%M%S)_$(openssl rand -hex 3)"

# 解析 workflow ID
WORKFLOW_ID=""
if [ -f "${WORKFLOW_DIR}/current.json" ]; then
    WORKFLOW_ID=$(jq -r '.workflow_id // ""' "${WORKFLOW_DIR}/current.json" 2>/dev/null || echo "")
fi

cat >> "$LOG_FILE" << EOF
{"id":"${EVENT_ID}","timestamp":"$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)","session_id":"${CLAUDE_SESSION_ID:-unknown}","workflow_id":"${WORKFLOW_ID}","event_type":"agent_stop","agent_id":"${CLAUDE_SUBAGENT_ID:-unknown}","data":{"exit_code":${CLAUDE_SUBAGENT_EXIT_CODE:-0}},"status":"completed"}
EOF

exit 0
```

## 寫入策略

### 同步 vs 批量

| 策略 | 優點 | 缺點 | 適用場景 |
|------|------|------|----------|
| 同步寫入 | 即時、不遺失 | I/O 開銷大 | 關鍵事件 |
| 批量寫入 | 效能好 | 可能遺失 | 高頻低優先事件 |
| 混合模式 | 平衡 | 複雜度高 | 生產環境 |

### 建議配置

```yaml
write_strategy:
  critical_events:
    # 同步寫入
    types: ["agent_start", "agent_stop", "error", "checkpoint"]
    mode: "sync"
    flush: "immediate"

  normal_events:
    # 批量寫入
    types: ["tool_call", "message", "state_change"]
    mode: "batch"
    buffer_size: 10
    flush_interval_ms: 1000
```

### 批量寫入實作

```bash
#!/bin/bash
# 位置: ~/.claude/hooks/batch-logger.sh
# 用途: 批量記錄器（作為背景服務）

BUFFER_FILE="/tmp/claude_event_buffer_$$.jsonl"
FINAL_FILE="${WORKFLOW_DIR}/logs/events.jsonl"
BUFFER_SIZE=10
FLUSH_INTERVAL=1

# 初始化 buffer
touch "$BUFFER_FILE"

flush_buffer() {
    if [ -s "$BUFFER_FILE" ]; then
        cat "$BUFFER_FILE" >> "$FINAL_FILE"
        > "$BUFFER_FILE"
    fi
}

# 定期刷新
while true; do
    sleep $FLUSH_INTERVAL
    flush_buffer
done &

# 接收事件
while read -r event; do
    echo "$event" >> "$BUFFER_FILE"

    # 達到 buffer size 則立即刷新
    if [ $(wc -l < "$BUFFER_FILE") -ge $BUFFER_SIZE ]; then
        flush_buffer
    fi
done

# 清理
flush_buffer
```

## 效能影響評估

### 基準測試

| 操作 | 無 Hook | 有 Hook (同步) | 有 Hook (批量) |
|------|---------|----------------|----------------|
| Bash 呼叫 | 50ms | 55ms (+10%) | 51ms (+2%) |
| Read 呼叫 | 10ms | 12ms (+20%) | 10.5ms (+5%) |
| Edit 呼叫 | 20ms | 23ms (+15%) | 21ms (+5%) |

### 優化建議

```yaml
performance_optimization:
  # 1. 使用 matcher 過濾不需要記錄的工具
  hook_matcher:
    include: ["Bash", "Edit", "Write", "Task"]
    exclude: ["Read"]  # 讀取操作太頻繁

  # 2. 減少 JSON 序列化開銷
  serialization:
    use_simple_format: true  # 避免複雜巢狀
    truncate_large_values: 500  # 截斷大數據

  # 3. 使用 RAM disk 作為暫存
  temp_storage:
    path: "/dev/shm/claude_logs"  # Linux RAM disk
    # macOS: 使用 /tmp（通常是 memory-backed）

  # 4. 非阻塞寫入
  async_write:
    enabled: true
    queue_size: 100
```

## 記錄查詢

### 基本查詢

```bash
# 查看特定 workflow 的所有事件
jq 'select(.workflow_id == "research_user-auth")' .claude/workflow/logs/events.jsonl

# 查看所有錯誤
jq 'select(.status == "failed" or .event_type == "error")' .claude/workflow/logs/events.jsonl

# 查看特定 Agent 的活動
jq 'select(.agent_id == "agent_architecture")' .claude/workflow/logs/events.jsonl

# 統計工具呼叫次數
jq -s 'group_by(.tool_name) | map({tool: .[0].tool_name, count: length})' .claude/workflow/logs/events.jsonl
```

### 時間範圍查詢

```bash
# 最近 10 分鐘的事件
jq 'select(.timestamp > "2025-01-25T14:20:00Z")' .claude/workflow/logs/events.jsonl

# 特定時間範圍
jq 'select(.timestamp >= "2025-01-25T14:00:00Z" and .timestamp <= "2025-01-25T15:00:00Z")' .claude/workflow/logs/events.jsonl
```

## 清理與歸檔

### 自動清理

```yaml
cleanup:
  # 單檔案大小限制
  max_file_size_mb: 50

  # 輪換策略
  rotation:
    trigger: "size > 10MB"
    action: "gzip and move to archive"
    keep_recent: 5

  # 歸檔
  archive:
    path: ".claude/workflow/archive/"
    compress: true
    retention_days: 30
```

### 清理腳本

```bash
#!/bin/bash
# 位置: ~/.claude/hooks/cleanup-logs.sh
# 用途: 定期清理日誌

LOG_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude/workflow/logs"
ARCHIVE_DIR="${LOG_DIR}/archive"
MAX_SIZE_MB=10

mkdir -p "$ARCHIVE_DIR"

for logfile in "$LOG_DIR"/*.jsonl; do
    [ -f "$logfile" ] || continue

    size=$(du -m "$logfile" | cut -f1)

    if [ "$size" -gt "$MAX_SIZE_MB" ]; then
        timestamp=$(date +%Y%m%d_%H%M%S)
        basename=$(basename "$logfile" .jsonl)

        gzip -c "$logfile" > "${ARCHIVE_DIR}/${basename}_${timestamp}.jsonl.gz"
        > "$logfile"

        echo "Rotated: $logfile -> ${ARCHIVE_DIR}/${basename}_${timestamp}.jsonl.gz"
    fi
done

# 清理超過 30 天的歸檔
find "$ARCHIVE_DIR" -name "*.gz" -mtime +30 -delete
```

## 配置參數

```yaml
execution_logs:
  enabled: true
  base_dir: ".claude/workflow/logs"

  files:
    events: "events.jsonl"
    errors: "errors.jsonl"

  hooks:
    pre_tool_use: true
    post_tool_use: true
    subagent_start: true
    subagent_stop: true

  write_strategy:
    mode: "hybrid"  # sync | batch | hybrid
    batch_size: 10
    flush_interval_ms: 1000

  performance:
    async_write: true
    truncate_output: 500
    exclude_tools: ["Read"]

  cleanup:
    enabled: true
    max_file_size_mb: 50
    rotation: true
    archive_retention_days: 30
```

## 行動級日誌（Action Logs）

### 概述

行動級日誌記錄每個工具調用的詳細資訊，用於：
- **精確定位**：知道具體哪個操作失敗
- **參數追蹤**：查看失敗時的輸入參數
- **錯誤診斷**：獲取完整的錯誤訊息
- **效能分析**：找出執行時間過長的操作

### 日誌位置

```
.claude/workflow/{workflow-id}/logs/
├── events.jsonl      # 現有事件日誌
└── actions.jsonl     # 行動級日誌（新增）
```

### Action Log Schema

```yaml
action_log_schema:
  # === 必填欄位 ===
  required:
    id:
      type: string
      format: "act_{timestamp}_{random}"
      description: "唯一識別碼"
      example: "act_20260126_100000_a1b2c3"

    timestamp:
      type: string
      format: "ISO8601"
      description: "執行時間"
      example: "2026-01-26T10:00:00.123Z"

    workflow_id:
      type: string
      description: "工作流 ID"
      example: "research_user-auth"

    agent_id:
      type: string
      description: "執行的 Agent"
      example: "agent_architecture"

    stage:
      type: string
      enum: [RESEARCH, PLAN, TASKS, IMPLEMENT, REVIEW, VERIFY]
      description: "當前階段"

    tool:
      type: string
      description: "工具名稱"
      example: "Bash"

    status:
      type: string
      enum: [success, failed, timeout, skipped]
      description: "執行狀態"

  # === 選填欄位 ===
  optional:
    input:
      type: object
      description: "工具輸入參數"

    output_preview:
      type: string
      max_length: 500
      description: "輸出預覽（截斷）"

    output_size:
      type: integer
      unit: bytes
      description: "完整輸出大小"

    error:
      type: string
      description: "錯誤訊息"

    stderr:
      type: string
      max_length: 1000
      description: "標準錯誤輸出"

    exit_code:
      type: integer
      description: "退出碼（Bash 專用）"

    duration_ms:
      type: integer
      unit: milliseconds
      description: "執行時間"
```

### 各工具的記錄內容

| 工具 | input 記錄 | output 記錄 | 特殊欄位 |
|------|-----------|-------------|----------|
| **Read** | `file_path` | `output_size`, `output_preview` | - |
| **Edit** | `file_path`, `old_string` (truncated), `new_string` (truncated) | - | - |
| **Write** | `file_path`, `content_size` | - | - |
| **Bash** | `command` | `stdout` (truncated), `stderr` | `exit_code` |
| **Task** | `subagent_type`, `prompt` (truncated) | `agent_id` | - |
| **Glob** | `pattern`, `path` | `match_count` | - |
| **Grep** | `pattern`, `path`, `glob` | `match_count` | - |
| **WebFetch** | `url` | `status_code`, `response_size` | - |

### 日誌格式範例

**成功的 Read 操作**：
```jsonl
{"id":"act_20260126_100000_a1b2c3","timestamp":"2026-01-26T10:00:00.123Z","workflow_id":"research_user-auth","agent_id":"agent_architecture","stage":"RESEARCH","tool":"Read","input":{"file_path":"/src/auth/login.ts"},"output_preview":"export function login(username: string, password: string)...","output_size":2048,"duration_ms":45,"status":"success"}
```

**成功的 Bash 操作**：
```jsonl
{"id":"act_20260126_100001_d4e5f6","timestamp":"2026-01-26T10:00:01.456Z","workflow_id":"research_user-auth","agent_id":"agent_architecture","stage":"IMPLEMENT","tool":"Bash","input":{"command":"npm test"},"output_preview":"PASS src/auth/login.test.ts\n  ✓ should validate credentials...","output_size":1024,"exit_code":0,"duration_ms":3500,"status":"success"}
```

**失敗的 Bash 操作**：
```jsonl
{"id":"act_20260126_100002_g7h8i9","timestamp":"2026-01-26T10:00:02.789Z","workflow_id":"research_user-auth","agent_id":"agent_architecture","stage":"IMPLEMENT","tool":"Bash","input":{"command":"npm test"},"error":"Command failed with exit code 1","stderr":"Error: Cannot find module '@/auth/utils'\n    at Object.<anonymous> (/src/auth/login.test.ts:2:1)","exit_code":1,"duration_ms":2100,"status":"failed"}
```

**成功的 Task 操作**：
```jsonl
{"id":"act_20260126_100003_j0k1l2","timestamp":"2026-01-26T10:00:03.012Z","workflow_id":"research_user-auth","agent_id":"orchestrator","stage":"RESEARCH","tool":"Task","input":{"subagent_type":"Explore","prompt":"分析 /src/auth 目錄的認證實作模式..."},"output_preview":"Found 5 authentication patterns...","duration_ms":15000,"status":"success"}
```

**失敗的 Edit 操作**：
```jsonl
{"id":"act_20260126_100004_m3n4o5","timestamp":"2026-01-26T10:00:04.345Z","workflow_id":"implement_user-auth","agent_id":"main_agent","stage":"IMPLEMENT","tool":"Edit","input":{"file_path":"/src/auth/login.ts","old_string":"function validateUser(","new_string":"async function validateUser("},"error":"old_string not found in file - the content may have changed","duration_ms":12,"status":"failed"}
```

### 日誌寫入腳本

**log-action.sh**（通用行動記錄）：

```bash
#!/bin/bash
# 位置: ~/.claude/hooks/log-action.sh
# 用途: 記錄工具調用到 actions.jsonl

set -euo pipefail

# 配置
WORKFLOW_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude/workflow"
ACTION_LOG="${WORKFLOW_DIR}/logs/actions.jsonl"

# 確保目錄存在
mkdir -p "$(dirname "$ACTION_LOG")"

# 生成 ID
ACTION_ID="act_$(date +%Y%m%d_%H%M%S)_$(openssl rand -hex 3)"

# 讀取工作流狀態
WORKFLOW_ID=""
STAGE=""
AGENT_ID=""
if [ -f "${WORKFLOW_DIR}/current.json" ]; then
    WORKFLOW_ID=$(jq -r '.workflow_id // ""' "${WORKFLOW_DIR}/current.json" 2>/dev/null || echo "")
    STAGE=$(jq -r '.stage // ""' "${WORKFLOW_DIR}/current.json" 2>/dev/null || echo "")
    AGENT_ID=$(jq -r '.agent_id // ""' "${WORKFLOW_DIR}/current.json" 2>/dev/null || echo "")
fi

# 截斷輸出
truncate_output() {
    local text="$1"
    local max_len="${2:-500}"
    if [ ${#text} -gt $max_len ]; then
        echo "${text:0:$max_len}..."
    else
        echo "$text"
    fi
}

# 構建 JSON
TOOL_NAME="${CLAUDE_TOOL_NAME:-unknown}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-null}"
TOOL_OUTPUT="${CLAUDE_TOOL_OUTPUT:-}"
EXIT_CODE="${CLAUDE_TOOL_EXIT_CODE:-0}"
DURATION_MS="${CLAUDE_TOOL_DURATION_MS:-0}"

# 判斷狀態
STATUS="success"
ERROR=""
if [ "$EXIT_CODE" != "0" ]; then
    STATUS="failed"
    ERROR=$(truncate_output "${CLAUDE_TOOL_STDERR:-Command failed}" 1000)
fi

# 輸出預覽
OUTPUT_PREVIEW=""
OUTPUT_SIZE=0
if [ -n "$TOOL_OUTPUT" ]; then
    OUTPUT_SIZE=${#TOOL_OUTPUT}
    OUTPUT_PREVIEW=$(truncate_output "$TOOL_OUTPUT" 500)
fi

# 寫入日誌（使用 jq 確保 JSON 格式正確）
jq -n \
    --arg id "$ACTION_ID" \
    --arg ts "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" \
    --arg wf_id "$WORKFLOW_ID" \
    --arg agent "$AGENT_ID" \
    --arg stage "$STAGE" \
    --arg tool "$TOOL_NAME" \
    --argjson input "$TOOL_INPUT" \
    --arg output_preview "$OUTPUT_PREVIEW" \
    --argjson output_size "$OUTPUT_SIZE" \
    --arg error "$ERROR" \
    --argjson exit_code "$EXIT_CODE" \
    --argjson duration_ms "$DURATION_MS" \
    --arg status "$STATUS" \
    '{
        id: $id,
        timestamp: $ts,
        workflow_id: $wf_id,
        agent_id: $agent,
        stage: $stage,
        tool: $tool,
        input: $input,
        output_preview: (if $output_preview == "" then null else $output_preview end),
        output_size: (if $output_size == 0 then null else $output_size end),
        error: (if $error == "" then null else $error end),
        exit_code: (if $tool == "Bash" then $exit_code else null end),
        duration_ms: $duration_ms,
        status: $status
    } | with_entries(select(.value != null))' >> "$ACTION_LOG"

exit 0
```

### 日誌保留策略

```yaml
retention:
  # 成功的行動
  success_logs:
    keep_days: 7
    compress_after_days: 3

  # 失敗的行動
  failed_logs:
    keep_days: 30
    compress_after_days: 7

  # 檔案大小限制
  max_file_size_mb: 100

  # 輪換策略
  rotation:
    trigger: "size > 50MB"
    action: "gzip and archive"
    keep_recent: 5
```

### 排查問題的常用查詢

**場景 1：找出所有失敗的行動**
```bash
jq 'select(.status == "failed")' .claude/workflow/*/logs/actions.jsonl
```

**場景 2：追蹤特定 Agent 的所有行動**
```bash
jq 'select(.agent_id == "agent_architecture")' actions.jsonl
```

**場景 3：找出執行時間超過 5 秒的行動**
```bash
jq 'select(.duration_ms > 5000)' actions.jsonl
```

**場景 4：查看某個 Bash 命令的完整錯誤**
```bash
grep '"npm test"' actions.jsonl | jq '{command: .input.command, error: .error, stderr: .stderr}'
```

**場景 5：統計各工具的失敗率**
```bash
jq -s 'group_by(.tool) | map({
    tool: .[0].tool,
    total: length,
    failed: [.[] | select(.status == "failed")] | length,
    fail_rate: (([.[] | select(.status == "failed")] | length) / length * 100 | floor)
})' actions.jsonl
```

**場景 6：找出特定階段的所有行動**
```bash
jq 'select(.stage == "IMPLEMENT")' actions.jsonl | jq -s 'sort_by(.timestamp)'
```

## 相關模組

- [Agent 通訊協定](./agent-protocol.md)
- [Memory System](../integration/memory-system.md)
- [Error Codes](../errors/error-codes.md)
- [Action Log Viewer](../tools/action-log-viewer.py)
