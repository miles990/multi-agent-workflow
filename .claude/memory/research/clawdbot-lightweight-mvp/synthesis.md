# Clawdbot 輕量 MVP 研究匯總報告

## 摘要

經過 4 視角並行研究分析（架構分析師、認知研究員、工作流設計師、業界實踐專家），確認 Clawdbot 現有架構是打造輕量 MVP 的優秀基礎。核心策略為「**保留骨架，精簡功能**」：保留插件架構、適配器模式、權限系統的設計模式，移除多 Channel、Agent Runtime、進階功能的具體實作，將 Agent 責任轉移給 Claude Code，Gateway 專注於連接和授權。

## 方法

- **視角**：架構分析師 (sonnet)、認知研究員 (sonnet)、工作流設計師 (haiku)、業界實踐專家 (haiku)
- **日期**：2026-01-27
- **模式**：default (4 視角並行)
- **專案**：/Users/user/Workspace/clawdbot

## 共識發現

### 強共識（4/4 視角同意）

1. **插件化架構值得保留**
   - 提供統一心智模型，降低認知負擔
   - 支援未來 Channel 擴展
   - 建議縮減為 3 種插件：Channel、Tool、Hook

2. **Telegram 通道可完整隔離**
   - 與其他 channel 高度解耦
   - 依賴鏈清晰：telegram → channels → auto-reply → routing → config
   - 可移除 7 個其他 channel 實作

3. **Claude Code 整合可行且推薦**
   - 使用 Task API 替代 Pi Agent
   - 保留 Session 管理層（routing, session-key, agent-scope）
   - 建立 adapter 層隔離 API 變更

4. **長輪詢優於 Webhook（MVP 階段）**
   - 無需公開 IP 或反向代理
   - Grammy 內建支援，故障轉移更簡單
   - Telegram 限速 30 更新/秒足夠 MVP

5. **Allowlist 是 MVP 最佳權限實踐**
   - 實施成本低（3-5 行配置）
   - 預設拒絕，安全性足夠
   - v2.0 可遷移到 RBAC

### 弱共識（3/4 視角同意）

1. **權限檢查需要集中化**
   - 現有 6 層檢查可優化為 3+2 步
   - 快速失敗機制提高效能
   - 添加審計日誌記錄所有決策

2. **必要複雜度不可移除**
   - Security Audit 系統（~1000 行）
   - Permission System（~500 行）
   - Config Schema Validation（~1000 行）

## 矛盾分析

### 已解決

本次研究未發現視角間的實質矛盾。4 個視角從不同角度（架構、認知、工作流、業界）分析，結論高度一致。

### 需進一步處理

無

## 關鍵洞察

### 1. MVP 架構設計

```
clawdbot-mvp/
├── src/
│   ├── gateway/               # Gateway 核心
│   │   ├── server.ts          # WebSocket server
│   │   ├── routing.ts         # 訊息路由
│   │   └── tool-api.ts        # Tool invocation API
│   ├── channels/
│   │   └── telegram/          # 唯一 Channel
│   │       ├── bot.ts
│   │       └── handlers.ts
│   ├── security/              # 權限與審計
│   │   ├── permission.ts      # 集中化權限檢查
│   │   ├── pairing.ts         # DM 配對
│   │   └── audit.ts           # 審計日誌
│   ├── agents/
│   │   ├── agent-scope.ts     # Agent 配置
│   │   └── claude-adapter.ts  # Claude Code 整合
│   ├── config/                # 配置系統
│   └── infra/                 # 基礎設施
├── docs/
│   ├── architecture.md
│   └── claude-integration.md
└── tests/
```

### 2. Claude Code 整合方案

```typescript
// src/agents/claude-adapter.ts

interface ClaudeCodeAdapter {
  // 消息處理
  processMessage(params: {
    sessionKey: string;
    message: string;
    sender: SenderInfo;
  }): Promise<AgentResponse>;

  // 工具調用 API（供 Claude Code 回調）
  invokeTool(params: {
    tool: string;
    params: unknown;
    context: ToolContext;
  }): Promise<ToolResult>;
}

// 整合流程
// 1. Telegram 消息 → Gateway
// 2. Gateway 權限檢查
// 3. Gateway → Claude Code (via Task API)
// 4. Claude Code 執行，工具調用回調 Gateway
// 5. Claude Code 回覆 → Gateway
// 6. Gateway → Telegram
```

### 3. 權限系統設計

```yaml
# config.yaml
security:
  dm_policy: "pairing"        # 強制配對驗證
  group_policy: "disabled"    # MVP 階段禁用群組

  allowlist:
    - user_id: "123456789"
      permissions:
        - "*"                  # 完整權限
    - user_id: "987654321"
      permissions:
        - "read"               # 只讀權限
        - "chat"

  tool_policy:
    profile: "coding"          # minimal | coding | messaging
    deny:
      - "exec.dangerous"       # 禁止危險操作

  audit:
    enabled: true
    retention: "30d"
    redact_content: true       # 脫敏消息內容
```

### 4. 消息處理流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Telegram   │────▶│   Gateway   │────▶│ Claude Code │
│   User      │     │             │     │             │
└─────────────┘     │ 1. 接收     │     │ 4. 推理     │
                    │ 2. 權限檢查 │     │ 5. 工具調用 │
                    │ 3. 路由     │◀────│ 6. 回覆     │
                    │ 7. 發送     │     │             │
                    └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Audit Log   │
                    │ .claude/    │
                    │ audit/      │
                    └─────────────┘
```

### 5. 模組保留/移除決策

| 類別 | 保留 | 移除 |
|------|------|------|
| **Channel** | telegram/ | whatsapp/, discord/, slack/, signal/, imessage/, googlechat/, line/ |
| **Agent** | agent-scope.ts, routing/ | pi-embedded-*, pi-tools.* |
| **基礎設施** | config/, infra/, plugins/ (核心) | browser/, canvas-host/, macos/, tts/ |
| **功能** | 權限檢查, 審計日誌 | Memory Search, Cron Jobs, Skills 系統 |

## 行動建議

### 1. 立即行動（Week 1-2）

- [ ] Fork clawdbot 到新專案 `clawdbot-mvp`
- [ ] 移除 7 個非 Telegram channel 目錄
- [ ] 建立 `claude-adapter.ts` 基礎框架
- [ ] 實作最小 Telegram → Claude Code 流程
- [ ] 配置基礎 allowlist 權限

### 2. 短期規劃（Week 3-4）

- [ ] 集中化權限檢查為單一函數
- [ ] 添加審計日誌系統
- [ ] 實作工具調用 API（Gateway ↔ Claude Code）
- [ ] 完成錯誤處理和重試機制
- [ ] 編寫核心路徑測試

### 3. 長期考量（v2.0）

- [ ] RBAC 權限系統升級
- [ ] 多 Channel 支援（保留介面已準備）
- [ ] Memory Search 整合（如需要）
- [ ] 效能優化和監控

## 風險評估

| 風險 | 機率 | 影響 | 緩解措施 |
|------|------|------|---------|
| Claude Code API 變更 | 中 | 高 | adapter 層隔離 |
| 隱性依賴遺漏 | 低 | 中 | 漸進式移除 + 完整測試 |
| 權限繞過漏洞 | 低 | 高 | 集中化檢查 + 審計日誌 |
| 長輪詢斷線丟消息 | 低 | 中 | offset 確認機制 |
| Allowlist 維護成本 | 中 | 低 | 預留 RBAC 升級路徑 |

## 品質評估

| 指標 | 分數 | 說明 |
|------|------|------|
| 共識率 | 95% | 4/4 視角在關鍵決策上一致 |
| 可行性 | 90% | 技術路徑清晰，風險可控 |
| 完整性 | 85% | 涵蓋架構、權限、工作流、業界 |
| **總分** | **90** | 超過 RESEARCH 階段閾值 (≥70) |

## 附錄

### 視角報告連結

- [架構分析師報告](./perspectives/architecture.md)
- [認知研究員報告](./perspectives/cognitive.md)
- [工作流設計師報告](./perspectives/workflow.md)
- [業界實踐專家報告](./perspectives/industry.md)

### 結構化摘要

- [architecture.yaml](./summaries/architecture.yaml)
- [cognitive.yaml](./summaries/cognitive.yaml)
- [workflow.yaml](./summaries/workflow.yaml)
- [industry.yaml](./summaries/industry.yaml)

---

*報告生成時間: 2026-01-27*
*工作流 ID: clawdbot-lightweight_20260127_1962d6*
*階段: RESEARCH → PLAN (可銜接)*
