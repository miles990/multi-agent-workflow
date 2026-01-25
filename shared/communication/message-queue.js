/**
 * message-queue.js - 檔案型訊息佇列 Node.js 實作
 *
 * 用途：提供 Agent 間的訊息佇列功能
 * 可作為 MCP 工具或獨立服務使用
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// 配置
const DEFAULT_CONFIG = {
  baseDir: '.claude/workflow',
  pollingInterval: 500,
  heartbeatInterval: 10000,
  ackTimeout: 5000,
  maxRetries: 3
};

/**
 * 生成唯一 ID
 */
function generateId(prefix = 'msg') {
  const timestamp = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
  const random = crypto.randomBytes(4).toString('hex');
  return `${prefix}_${timestamp}_${random}`;
}

/**
 * 取得當前時間戳
 */
function timestamp() {
  return new Date().toISOString();
}

/**
 * 確保目錄存在
 */
function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

/**
 * 追加 JSON 行到檔案
 */
function appendJsonLine(filePath, data) {
  ensureDir(path.dirname(filePath));
  const line = JSON.stringify(data) + '\n';
  fs.appendFileSync(filePath, line);
}

/**
 * 讀取 JSON Lines 檔案
 */
function readJsonLines(filePath, fromLine = 0) {
  if (!fs.existsSync(filePath)) return [];

  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.trim().split('\n').filter(Boolean);

  return lines.slice(fromLine).map((line, idx) => {
    try {
      return { ...JSON.parse(line), _line: fromLine + idx };
    } catch (e) {
      return null;
    }
  }).filter(Boolean);
}

/**
 * MessageQueue 類別
 */
class MessageQueue {
  constructor(projectDir, config = {}) {
    this.projectDir = projectDir;
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.baseDir = path.join(projectDir, this.config.baseDir);
    this.currentWorkflow = null;
    this.processedLines = {};
  }

  /**
   * 初始化 Workflow
   */
  initWorkflow(workflowId, type = 'research', topic = 'default') {
    const workflowDir = path.join(this.baseDir, workflowId);

    // 創建目錄結構
    ensureDir(path.join(workflowDir, 'channel', 'agents'));
    ensureDir(path.join(workflowDir, 'state', 'heartbeat'));
    ensureDir(path.join(workflowDir, 'logs'));

    // 初始化 agents.json
    const agentsFile = path.join(workflowDir, 'state', 'agents.json');
    fs.writeFileSync(agentsFile, JSON.stringify({
      workflow_id: workflowId,
      workflow_type: type,
      topic: topic,
      created_at: timestamp(),
      status: 'initializing',
      agents: {}
    }, null, 2));

    // 創建空的通訊頻道
    fs.writeFileSync(path.join(workflowDir, 'channel', 'broadcast.jsonl'), '');
    fs.writeFileSync(path.join(workflowDir, 'channel', 'orchestrator.jsonl'), '');

    // 創建空的日誌檔案
    fs.writeFileSync(path.join(workflowDir, 'logs', 'events.jsonl'), '');
    fs.writeFileSync(path.join(workflowDir, 'logs', 'errors.jsonl'), '');

    // 設置當前 workflow
    fs.writeFileSync(path.join(this.baseDir, 'current.json'), JSON.stringify({
      workflow_id: workflowId,
      workflow_dir: workflowDir,
      started_at: timestamp()
    }, null, 2));

    this.currentWorkflow = workflowId;
    return workflowId;
  }

  /**
   * 載入當前 Workflow
   */
  loadCurrentWorkflow() {
    const currentFile = path.join(this.baseDir, 'current.json');
    if (fs.existsSync(currentFile)) {
      const data = JSON.parse(fs.readFileSync(currentFile, 'utf8'));
      this.currentWorkflow = data.workflow_id;
      return data.workflow_id;
    }
    return null;
  }

  /**
   * 取得 Workflow 目錄
   */
  getWorkflowDir(workflowId = null) {
    const wfId = workflowId || this.currentWorkflow || this.loadCurrentWorkflow();
    if (!wfId) throw new Error('No workflow specified or active');
    return path.join(this.baseDir, wfId);
  }

  /**
   * 註冊 Agent
   */
  registerAgent(agentId, perspective = 'unknown', workflowId = null) {
    const workflowDir = this.getWorkflowDir(workflowId);
    const agentsFile = path.join(workflowDir, 'state', 'agents.json');

    // 創建 Agent 訊息佇列
    fs.writeFileSync(path.join(workflowDir, 'channel', 'agents', `${agentId}.jsonl`), '');
    fs.writeFileSync(path.join(workflowDir, 'channel', 'agents', `${agentId}.ack`), '');

    // 更新 agents.json
    const agents = JSON.parse(fs.readFileSync(agentsFile, 'utf8'));
    agents.agents[agentId] = {
      perspective,
      status: 'registered',
      registered_at: timestamp(),
      last_heartbeat: timestamp()
    };
    fs.writeFileSync(agentsFile, JSON.stringify(agents, null, 2));

    return agentId;
  }

  /**
   * 發送訊息
   */
  sendMessage(to, type, payload = {}, workflowId = null, from = 'orchestrator') {
    const workflowDir = this.getWorkflowDir(workflowId);

    const msgId = generateId('msg');
    const requiresAck = ['task_assign', 'checkpoint_request', 'abort'].includes(type);

    const message = {
      id: msgId,
      timestamp: timestamp(),
      from,
      to,
      type,
      payload,
      requires_ack: requiresAck
    };

    // 決定目標檔案
    let targetFile;
    if (to === 'broadcast') {
      targetFile = path.join(workflowDir, 'channel', 'broadcast.jsonl');
    } else if (to === 'orchestrator') {
      targetFile = path.join(workflowDir, 'channel', 'orchestrator.jsonl');
    } else {
      targetFile = path.join(workflowDir, 'channel', 'agents', `${to}.jsonl`);
    }

    appendJsonLine(targetFile, message);

    // 記錄事件
    this.logEvent('message', {
      message_id: msgId,
      from,
      to,
      type
    }, 'sent', workflowId);

    return msgId;
  }

  /**
   * 讀取訊息
   */
  readMessages(agentId, workflowId = null) {
    const workflowDir = this.getWorkflowDir(workflowId);
    const queueKey = `${workflowDir}:${agentId}`;

    // 取得已處理的行數
    const lastLine = this.processedLines[queueKey] || 0;

    // 讀取個人佇列
    const queueFile = path.join(workflowDir, 'channel', 'agents', `${agentId}.jsonl`);
    const queueMessages = readJsonLines(queueFile, lastLine);

    // 讀取廣播
    const broadcastKey = `${workflowDir}:broadcast`;
    const broadcastLastLine = this.processedLines[broadcastKey] || 0;
    const broadcastFile = path.join(workflowDir, 'channel', 'broadcast.jsonl');
    const broadcastMessages = readJsonLines(broadcastFile, broadcastLastLine);

    // 更新已處理行數
    if (queueMessages.length > 0) {
      this.processedLines[queueKey] = queueMessages[queueMessages.length - 1]._line + 1;
    }
    if (broadcastMessages.length > 0) {
      this.processedLines[broadcastKey] = broadcastMessages[broadcastMessages.length - 1]._line + 1;
    }

    return [...queueMessages, ...broadcastMessages];
  }

  /**
   * 發送 ACK
   */
  sendAck(agentId, msgId, status = 'received', workflowId = null) {
    const workflowDir = this.getWorkflowDir(workflowId);
    const ackFile = path.join(workflowDir, 'channel', 'agents', `${agentId}.ack`);

    const ack = {
      msg_id: msgId,
      status,
      at: timestamp()
    };

    appendJsonLine(ackFile, ack);
    return ack;
  }

  /**
   * 等待 ACK
   */
  async waitForAck(msgId, agentId, workflowId = null, timeout = 5000) {
    const workflowDir = this.getWorkflowDir(workflowId);
    const ackFile = path.join(workflowDir, 'channel', 'agents', `${agentId}.ack`);

    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      const acks = readJsonLines(ackFile);
      const ack = acks.find(a => a.msg_id === msgId);

      if (ack) {
        return { success: true, ack };
      }

      await new Promise(resolve => setTimeout(resolve, 200));
    }

    return { success: false, error: 'timeout' };
  }

  /**
   * 更新心跳
   */
  updateHeartbeat(agentId, workflowId = null) {
    const workflowDir = this.getWorkflowDir(workflowId);
    const heartbeatFile = path.join(workflowDir, 'state', 'heartbeat', `${agentId}.ts`);
    const agentsFile = path.join(workflowDir, 'state', 'agents.json');
    const ts = timestamp();

    // 更新心跳檔案
    fs.writeFileSync(heartbeatFile, ts);

    // 更新 agents.json
    const agents = JSON.parse(fs.readFileSync(agentsFile, 'utf8'));
    if (agents.agents[agentId]) {
      agents.agents[agentId].last_heartbeat = ts;
      agents.agents[agentId].status = 'active';
      fs.writeFileSync(agentsFile, JSON.stringify(agents, null, 2));
    }
  }

  /**
   * 記錄事件
   */
  logEvent(eventType, data, status = 'info', workflowId = null) {
    const workflowDir = this.getWorkflowDir(workflowId);
    const eventsFile = path.join(workflowDir, 'logs', 'events.jsonl');

    const event = {
      id: generateId('evt'),
      timestamp: timestamp(),
      workflow_id: workflowId || this.currentWorkflow,
      event_type: eventType,
      data,
      status
    };

    appendJsonLine(eventsFile, event);
    return event.id;
  }

  /**
   * 記錄錯誤
   */
  logError(errorType, message, data = {}, workflowId = null) {
    const workflowDir = this.getWorkflowDir(workflowId);
    const errorsFile = path.join(workflowDir, 'logs', 'errors.jsonl');

    const error = {
      id: generateId('err'),
      timestamp: timestamp(),
      workflow_id: workflowId || this.currentWorkflow,
      error_type: errorType,
      message,
      data
    };

    appendJsonLine(errorsFile, error);
    return error.id;
  }

  /**
   * 檢查 Agent 健康狀態
   */
  checkAgentsHealth(workflowId = null, timeoutSeconds = 30) {
    const workflowDir = this.getWorkflowDir(workflowId);
    const agentsFile = path.join(workflowDir, 'state', 'agents.json');

    const agents = JSON.parse(fs.readFileSync(agentsFile, 'utf8'));
    const now = Date.now();
    const results = { healthy: [], unhealthy: [] };

    for (const [agentId, agent] of Object.entries(agents.agents)) {
      const heartbeatFile = path.join(workflowDir, 'state', 'heartbeat', `${agentId}.ts`);

      if (fs.existsSync(heartbeatFile)) {
        const lastHeartbeat = new Date(fs.readFileSync(heartbeatFile, 'utf8').trim()).getTime();
        const diff = (now - lastHeartbeat) / 1000;

        if (diff > timeoutSeconds) {
          results.unhealthy.push({ agentId, lastSeen: diff });
          // 更新狀態
          agents.agents[agentId].status = 'unresponsive';
        } else {
          results.healthy.push({ agentId, lastSeen: diff });
        }
      } else {
        results.unhealthy.push({ agentId, lastSeen: null, reason: 'no_heartbeat' });
      }
    }

    fs.writeFileSync(agentsFile, JSON.stringify(agents, null, 2));
    return results;
  }

  /**
   * 清理 Workflow
   */
  cleanupWorkflow(workflowId, archive = true) {
    const workflowDir = path.join(this.baseDir, workflowId);

    if (!fs.existsSync(workflowDir)) {
      throw new Error(`Workflow not found: ${workflowId}`);
    }

    if (archive) {
      const archiveDir = path.join(this.baseDir, 'archive');
      ensureDir(archiveDir);
      // 簡化版：只移動目錄
      fs.renameSync(workflowDir, path.join(archiveDir, workflowId));
    } else {
      fs.rmSync(workflowDir, { recursive: true, force: true });
    }

    // 清除當前 workflow（如果是）
    const currentFile = path.join(this.baseDir, 'current.json');
    if (fs.existsSync(currentFile)) {
      const current = JSON.parse(fs.readFileSync(currentFile, 'utf8'));
      if (current.workflow_id === workflowId) {
        fs.unlinkSync(currentFile);
      }
    }

    return { archived: archive };
  }
}

// CLI 模式
if (require.main === module) {
  const args = process.argv.slice(2);
  const command = args[0];
  const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const mq = new MessageQueue(projectDir);

  switch (command) {
    case 'init':
      const wfId = mq.initWorkflow(args[1], args[2], args[3]);
      console.log(`Workflow initialized: ${wfId}`);
      break;

    case 'register':
      mq.registerAgent(args[1], args[2]);
      console.log(`Agent registered: ${args[1]}`);
      break;

    case 'send':
      const msgId = mq.sendMessage(args[1], args[2], JSON.parse(args[3] || '{}'));
      console.log(`Message sent: ${msgId}`);
      break;

    case 'read':
      const messages = mq.readMessages(args[1]);
      console.log(JSON.stringify(messages, null, 2));
      break;

    case 'health':
      const health = mq.checkAgentsHealth();
      console.log(JSON.stringify(health, null, 2));
      break;

    default:
      console.log('Usage: node message-queue.js <command> [args]');
      console.log('Commands: init, register, send, read, health');
  }
}

module.exports = { MessageQueue, generateId, timestamp };
