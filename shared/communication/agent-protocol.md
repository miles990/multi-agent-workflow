# Agent 通訊協定（Communication Protocol）

> 檔案型訊息佇列與 ACK 機制的完整實作

## 概述

本模組定義 Agent 間的通訊機制，基於：
- **檔案系統**：作為訊息佇列的持久化層
- **輪詢機制**：Agent 定期檢查訊息
- **ACK 機制**：確保訊息可靠送達

## 目錄結構

```
.claude/workflow/{workflow-id}/
├── channel/                      # 通訊頻道
│   ├── broadcast.jsonl           # 廣播訊息（所有 Agent）
│   ├── orchestrator.jsonl        # 給 Orchestrator 的訊息
│   └── agents/
│       ├── {agent-id}.jsonl      # 個別 Agent 的訊息佇列
│       └── {agent-id}.ack        # ACK 記錄
├── state/                        # 狀態追蹤
│   ├── agents.json               # Agent 註冊表
│   └── heartbeat/
│       └── {agent-id}.ts         # 心跳時間戳
└── logs/                         # 執行記錄
    ├── events.jsonl              # 事件日誌
    └── errors.jsonl              # 錯誤日誌
```

## 訊息格式

### 基本訊息結構

```json
{
  "id": "msg_20250125_143022_abc123",
  "timestamp": "2025-01-25T14:30:22.456Z",
  "from": "orchestrator",
  "to": "agent_architecture",
  "type": "task_assign",
  "payload": {
    "task_id": "task_001",
    "perspective": "architecture",
    "topic": "user-auth-system"
  },
  "requires_ack": true,
  "ttl_seconds": 300
}
```

### 訊息類型

| type | 用途 | requires_ack |
|------|------|--------------|
| `task_assign` | 指派任務給 Agent | true |
| `task_complete` | Agent 回報任務完成 | true |
| `progress_update` | 進度更新 | false |
| `checkpoint_request` | 請求同步檢查 | true |
| `checkpoint_response` | 回應同步檢查 | true |
| `broadcast` | 廣播訊息 | false |
| `heartbeat` | 心跳（存活確認） | false |
| `abort` | 中止任務 | true |

### ACK 訊息

```json
{
  "id": "ack_20250125_143025_def456",
  "timestamp": "2025-01-25T14:30:25.123Z",
  "ack_for": "msg_20250125_143022_abc123",
  "from": "agent_architecture",
  "status": "received"
}
```

## 通訊流程

### 1. Agent 註冊

```
Orchestrator 啟動
    ↓
創建 workflow 目錄結構
    ↓
為每個視角創建 Agent 訊息佇列
    ↓
記錄到 state/agents.json
```

**agents.json 格式**：

```json
{
  "workflow_id": "research_user-auth_20250125",
  "created_at": "2025-01-25T14:30:00.000Z",
  "agents": {
    "agent_architecture": {
      "perspective": "architecture",
      "status": "active",
      "started_at": "2025-01-25T14:30:01.000Z",
      "last_heartbeat": "2025-01-25T14:35:22.000Z"
    },
    "agent_cognitive": {
      "perspective": "cognitive",
      "status": "active",
      "started_at": "2025-01-25T14:30:02.000Z",
      "last_heartbeat": "2025-01-25T14:35:20.000Z"
    }
  }
}
```

### 2. 任務分派

```
Orchestrator
    ↓
寫入訊息到 agents/{agent-id}.jsonl
    ↓
Agent 輪詢發現新訊息
    ↓
Agent 處理訊息
    ↓
Agent 寫入 ACK 到 agents/{agent-id}.ack
    ↓
Orchestrator 確認 ACK
```

### 3. 進度回報

```
Agent 處理中
    ↓
定期寫入 heartbeat/{agent-id}.ts
    ↓
完成時寫入 task_complete 到 orchestrator.jsonl
    ↓
Orchestrator 收到完成通知
```

### 4. 同步檢查點

```
Orchestrator 發起檢查點
    ↓
廣播 checkpoint_request 到 broadcast.jsonl
    ↓
各 Agent 讀取並回應
    ↓
Orchestrator 收集所有 checkpoint_response
    ↓
決定繼續或調整
```

## 輪詢機制

### 輪詢參數

```yaml
polling:
  interval_ms: 500          # 輪詢間隔
  max_wait_ms: 5000         # 最大等待時間
  backoff_multiplier: 1.5   # 退避倍數
  max_interval_ms: 3000     # 最大間隔

heartbeat:
  interval_ms: 10000        # 心跳間隔
  timeout_ms: 30000         # 超時判定
```

### 輪詢實作（概念）

```javascript
// Agent 輪詢邏輯
async function pollMessages(agentId, workflowDir) {
  const queueFile = `${workflowDir}/channel/agents/${agentId}.jsonl`
  const broadcastFile = `${workflowDir}/channel/broadcast.jsonl`

  let interval = 500
  let lastProcessed = { queue: 0, broadcast: 0 }

  while (running) {
    // 檢查個人佇列
    const queueMessages = await readNewLines(queueFile, lastProcessed.queue)
    for (const msg of queueMessages) {
      await processMessage(msg)
      if (msg.requires_ack) {
        await sendAck(agentId, msg.id, workflowDir)
      }
    }

    // 檢查廣播
    const broadcastMessages = await readNewLines(broadcastFile, lastProcessed.broadcast)
    for (const msg of broadcastMessages) {
      await processMessage(msg)
    }

    // 發送心跳
    await updateHeartbeat(agentId, workflowDir)

    await sleep(interval)
  }
}
```

## ACK 機制

### ACK 狀態追蹤

```json
// agents/{agent-id}.ack
{"msg_id": "msg_001", "status": "received", "at": "2025-01-25T14:30:25.123Z"}
{"msg_id": "msg_002", "status": "received", "at": "2025-01-25T14:30:55.456Z"}
{"msg_id": "msg_003", "status": "processed", "at": "2025-01-25T14:31:22.789Z"}
```

### 重試邏輯

```yaml
ack_retry:
  max_attempts: 3
  retry_delay_ms: 2000

  on_no_ack:
    1st_attempt: "重發訊息"
    2nd_attempt: "重發訊息 + 警告"
    3rd_attempt: "標記 Agent 為 unresponsive"
```

### Orchestrator 追蹤

```javascript
// Orchestrator ACK 追蹤
async function waitForAck(messageId, agentId, workflowDir, timeout = 5000) {
  const ackFile = `${workflowDir}/channel/agents/${agentId}.ack`
  const startTime = Date.now()

  while (Date.now() - startTime < timeout) {
    const acks = await readJsonLines(ackFile)
    const ack = acks.find(a => a.msg_id === messageId)

    if (ack) {
      return { success: true, ack }
    }

    await sleep(200)
  }

  return { success: false, error: 'timeout' }
}
```

## 錯誤處理

### Agent 無回應

```yaml
unresponsive_agent:
  detection:
    - "heartbeat 超過 30 秒未更新"
    - "ACK 重試 3 次仍失敗"

  actions:
    1: "記錄到 errors.jsonl"
    2: "標記 Agent 狀態為 'unresponsive'"
    3: "通知 Orchestrator"
    4: "Orchestrator 決定：重啟 / 跳過 / 中止"
```

### 訊息遺失

```yaml
message_loss_prevention:
  - "使用 JSONL 追加寫入（原子操作）"
  - "訊息帶有唯一 ID"
  - "ACK 確認機制"
  - "定期檢查 pending ACK"
```

### 衝突處理

```yaml
conflict_resolution:
  concurrent_write:
    strategy: "append-only"
    format: "JSONL"
    guarantee: "每行獨立，原子追加"

  duplicate_messages:
    detection: "檢查 message ID"
    action: "忽略重複"
```

## 效能考量

### 檔案操作優化

```yaml
file_operations:
  write:
    mode: "append"           # 追加而非覆寫
    flush: "immediate"       # 立即刷新

  read:
    strategy: "tail"         # 只讀取新增部分
    cache_offset: true       # 快取已讀位置

  cleanup:
    trigger: "messages > 1000"
    action: "rotate to archive"
```

### 記憶體使用

```yaml
memory_management:
  message_buffer: 100        # 最多緩衝 100 條訊息
  ack_cache_ttl: 60          # ACK 快取 60 秒
  heartbeat_cache: true      # 快取心跳以減少 I/O
```

## 配置參數

```yaml
communication:
  base_dir: ".claude/workflow"

  channels:
    broadcast: "channel/broadcast.jsonl"
    orchestrator: "channel/orchestrator.jsonl"
    agents: "channel/agents/"

  state:
    agents_registry: "state/agents.json"
    heartbeat_dir: "state/heartbeat/"

  logs:
    events: "logs/events.jsonl"
    errors: "logs/errors.jsonl"

  polling:
    interval_ms: 500
    max_interval_ms: 3000

  heartbeat:
    interval_ms: 10000
    timeout_ms: 30000

  ack:
    required_types: ["task_assign", "checkpoint_request", "abort"]
    timeout_ms: 5000
    max_retries: 3

  cleanup:
    enabled: true
    max_messages: 1000
    archive_after_workflow: true
```

## 相關模組

- [執行記錄系統](./execution-logs.md)
- [Map Phase](../coordination/map-phase.md)
- [Reduce Phase](../coordination/reduce-phase.md)
