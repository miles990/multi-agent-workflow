---
name: orchestrate
version: 3.4.0
description: 端到端工作流編排器 - File-Based Handoff + 智能並行決策
triggers: [orchestrate, workflow, 全流程, e2e]
allowed-tools: [Read, Write, Bash, Glob, Grep, Skill, Task, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

# Multi-Agent Orchestrate v3.4.0

## 路徑解析（必讀）

此 Skill 使用 `shared/` 目錄下的工具。執行時必須使用完整路徑。

**從 command-message header 取得 Base directory**，例如：
```
Base directory for this skill: /path/to/.../skills/orchestrate
```

**Plugin Root** = Base directory 往上兩層（去掉 `/skills/orchestrate`）

```bash
# 範例：如果 Base directory 是 /Users/user/.claude/plugins/cache/multi-agent-workflow/multi-agent-workflow/2.4.2/skills/orchestrate
# 則 Plugin Root 是 /Users/user/.claude/plugins/cache/multi-agent-workflow/multi-agent-workflow/2.4.2

# 工具路徑
PLUGIN_ROOT="${BASE_DIR%/skills/orchestrate}"  # 移除尾部
$PLUGIN_ROOT/shared/tools/workflow-init.sh     # 正確路徑
```

**重要**：不要使用 `./shared/tools/...`，因為工作目錄是用戶專案，不是 plugin 目錄。

---

## 前置檢查（重要）

在開始工作流之前，檢查專案是否已配置規範執行機制：

```bash
# 檢查 settings.local.json 是否包含必要的 hooks
cat .claude/settings.local.json 2>/dev/null | grep -q "PostToolUse" && echo "✓ Hooks configured" || echo "✗ Hooks not configured"
```

**如果 Hooks 未配置**，顯示以下提示：

```
⚠️ 專案尚未配置 workflow 規範執行機制。

建議執行 `/setup-workflow` 啟用以下功能：
  • Task 完成後自動 commit（保存進度）
  • 自動運行測試驗證
  • Memory 變更追蹤

執行 `/setup-workflow` 一鍵完成配置。
```

**如果用戶選擇繼續**：可以繼續執行，但不會有自動 commit 和驗證功能。

---

> 需求輸入 → 6 階段串聯 → 品質閘門 → 智慧回退 → 完成交付

## 使用方式

```bash
/orchestrate [需求描述]
/orchestrate 建立用戶認證系統，支援 JWT 和 OAuth2
```

**Flags**:
- `--profile <mode>` - 執行模式：`default`（預設）| `express`（快速）| `quality`（最高品質）
- `--start-from STAGE` - 從指定階段開始
- `--skip STAGE` - 跳過指定階段
- `--quick` - 快速模式（等同 `--profile express`）
- `--deep` - 深度模式（等同 `--profile quality`）

## 工作流階段

```
RESEARCH → PLAN → TASKS → IMPLEMENT → REVIEW → VERIFY
                                        ↑__________↓
                                      智慧回退機制
```

| 階段 | 輸入 | 輸出 | 閘門分數 |
|------|------|------|----------|
| RESEARCH | 需求 | synthesis.md | ≥70 |
| PLAN | 研究報告 | implementation-plan.md | ≥75 |
| TASKS | 實作計劃 | tasks.yaml | ≥80 |
| IMPLEMENT | 任務清單 | 程式碼 | ≥80 |
| REVIEW | 程式碼 | review-summary.md | ≥75 |
| VERIFY | 審查報告 | 驗證結果 | ≥85 |

## 執行流程

```
Phase 0: 初始化工作流
    ├── 生成 workflow-id
    ├── **【必要】執行 workflow-init.sh 初始化通訊環境**
    │   └── Bash: $PLUGIN_ROOT/shared/tools/workflow-init.sh init <workflow-id> orchestrate "<需求摘要>"
    │   └── 這會創建 .claude/workflow/current.json（Hooks 依賴此檔案）
    ├── 載入執行模式配置
    │   └── 讀取 $PLUGIN_ROOT/shared/config/execution-profiles.yaml
    │   └── 套用視角數和模型配置
    ├── 建立報告目錄
    └── 記錄開始時間
    ↓
For each stage in [RESEARCH, PLAN, TASKS, IMPLEMENT, REVIEW, VERIFY]:
    ↓
    Phase 1: 執行階段
    ├── 呼叫對應 skill
    └── 等待完成
    ↓
    Phase 2: 早期終止檢查
    ├── 滿足條件？→ 可跳過後續步驟
    └── 不滿足 → 繼續
    ↓
    Phase 3: 品質閘門
    ├── 通過 → 下一階段
    └── 失敗 → 智慧回退
    ↓
End for
    ↓
Phase 4: 完成
    ├── 生成報告
    ├── 更新 Memory
    └── 驗證變更已 commit（見下方 Fallback）
```

### Phase 4 Fallback：手動 Commit

如果自動 checkpoint commit 沒有觸發（例如 hooks 未配置），手動執行：

```bash
# 檢查是否有未 commit 的變更
git status

# 如果有變更，手動 commit
git add -A
git commit -m "chore(workflow): complete {workflow-id}"
```

**自動 Commit 觸發時機**：
- 寫入 `synthesis.md` → RESEARCH 完成
- 寫入 `implementation-plan.md` → PLAN 完成
- 寫入 `tasks.yaml` → TASKS 完成
- 寫入 `summary.md` → IMPLEMENT 完成
- 寫入 `review-summary.md` → REVIEW 完成
- 寫入 `verify-summary.md` → VERIFY 完成

## 智慧回退機制

根據迭代次數決定回退目標：

| 迭代 | 回退目標 | 原因 |
|------|----------|------|
| 1-2 | IMPLEMENT | 可能是實作問題 |
| 3 | TASKS | 可能是任務分解問題 |
| 4 | PLAN | 可能是設計問題 |
| 5+ | HUMAN | 超過自動修復能力 |

**循環偵測**：
- 相同錯誤兩次 → 升級回退層級
- 階段間振盪 → 暫停分析根因
- 總迭代 > 10 → 強制停止

→ 配置：[shared/quality/rollback-strategy.yaml](../../shared/quality/rollback-strategy.yaml)

## 部分完成處理（Partial Completion）

當工作流中斷或某階段失敗時，自動保存進度以便恢復。

### 自動保存進度

每個階段完成後立即保存進度到 `.claude/workflow/{id}/recovery/progress.yaml`：

```yaml
workflow_id: "orchestrate_20260206_123456_abc123"
status: "interrupted"  # completed | interrupted | failed
current_stage: "IMPLEMENT"
completed_stages:
  - stage: RESEARCH
    output: ".claude/memory/research/{topic-id}/synthesis.md"
    score: 82
    timestamp: "2026-02-06T12:35:00Z"
  - stage: PLAN
    output: ".claude/memory/plans/{feature-id}/implementation-plan.md"
    score: 78
    timestamp: "2026-02-06T12:40:00Z"
  - stage: TASKS
    output: ".claude/memory/tasks/{plan-id}/tasks.yaml"
    score: 85
    timestamp: "2026-02-06T12:45:00Z"
failed_stage:
  stage: IMPLEMENT
  error: "Tests failed after 3 retries"
  last_checkpoint: "task-3-of-8"
  timestamp: "2026-02-06T13:00:00Z"
```

### 恢復執行

```bash
/orchestrate --resume {workflow-id}
# 或
/orchestrate --resume  # 自動找到最近中斷的工作流
```

恢復流程：
1. 讀取 `progress.yaml` 確認中斷點
2. 驗證已完成階段的輸出仍然有效（檔案存在 + git status 乾淨）
3. 從中斷的階段/任務繼續執行
4. 如果已完成階段的輸出被破壞，回退到該階段重新執行

### 部分完成的通知

中斷時輸出：
```
⚠️ 工作流部分完成 (3/6 階段)
✅ RESEARCH → PLAN → TASKS
❌ IMPLEMENT（失敗：Tests failed after 3 retries）
⏸️ REVIEW → VERIFY（未執行）

進度已保存至：.claude/workflow/{id}/recovery/progress.yaml
恢復命令：/orchestrate --resume {id}
```

### 與智慧回退的區別

| 情境 | 機制 | 說明 |
|------|------|------|
| 品質閘門失敗 | 智慧回退 | 自動回退到適當階段重試（最多 5 次） |
| 回退次數超限 | 部分完成 | 保存進度，等待人工介入後 `--resume` |
| Context Limit | 部分完成 | 保存進度，新 session 中 `--resume` |
| 外部錯誤（網路/權限） | 部分完成 | 保存進度，修復問題後 `--resume` |
| Session 崩潰 | 部分完成 | 依賴 git checkpoint，`--resume` 從最後 commit 恢復 |

## 早期終止

| 階段 | 條件 | 動作 |
|------|------|------|
| RESEARCH | consensus ≥ 0.9 | 跳過衝突解決 |
| PLAN | risk < 0.2 | 快速模式 |
| REVIEW | 無 BLOCKER/HIGH | 直接通過 |
| VERIFY | pass_rate ≥ 0.98 | 可發布 |

→ 配置：[shared/config/early-termination.yaml](../../shared/config/early-termination.yaml)

## 報告生成

完成後自動生成：
- `dashboard.md` - 總覽
- `timeline.md` - 時間線
- `quality-report.md` - 品質報告
- `decisions.md` - 決策記錄

→ 工具：[shared/tools/generate-report.sh](../../shared/tools/generate-report.sh)

## 輸出結構

```
.claude/memory/workflows/[workflow-id]/
├── dashboard.md        # 總覽報告
├── timeline.md         # 時間線
├── decisions.md        # 決策記錄
├── quality-report.md   # 品質報告
├── stages/             # 各階段報告
├── agents/             # Agent 記錄
└── exports/            # 匯出格式
```

## 共用模組

| 模組 | 用途 |
|------|------|
| [quality/gates.yaml](../../shared/quality/gates.yaml) | 品質閘門 |
| [quality/rollback-strategy.yaml](../../shared/quality/rollback-strategy.yaml) | 智慧回退 |
| [config/early-termination.yaml](../../shared/config/early-termination.yaml) | 早期終止 |
| [config/execution-profiles.yaml](../../shared/config/execution-profiles.yaml) | 執行模式 |
| [config/context-freshness.yaml](../../shared/config/context-freshness.yaml) | 上下文新鮮 |
| [tools/generate-report.sh](../../shared/tools/generate-report.sh) | 報告生成 |
| [tools/workflow-init.sh](../../shared/tools/workflow-init.sh) | 工作流初始化 |

## 【重要】初始化步驟

在執行任何階段之前，**必須**先初始化工作流環境：

```bash
# 0. 從 command-message header 取得 Base directory，計算 Plugin Root
# 例如：Base directory: /path/.../2.4.2/skills/orchestrate
# PLUGIN_ROOT 就是 /path/.../2.4.2（去掉 /skills/orchestrate）

# 1. 生成 workflow ID（格式：orchestrate_YYYYMMDD_HHMMSS_xxxx）
WORKFLOW_ID="orchestrate_$(date +%Y%m%d_%H%M%S)_$(openssl rand -hex 4)"

# 2. 執行初始化（創建 current.json，讓 Hooks 能記錄活動）
# 使用完整路徑，不要用 ./shared/...
$PLUGIN_ROOT/shared/tools/workflow-init.sh init "$WORKFLOW_ID" orchestrate "需求摘要"
```

**為什麼這很重要？**
- Hooks（log-tool-pre.sh、log-tool-post.sh、log-agent-lifecycle.sh）依賴 `.claude/workflow/current.json`
- 如果沒有這個檔案，所有 Agent 活動都不會被記錄
- 這會導致 `/status` 和 statusline 無法顯示正確的工作流狀態

## File-Based Handoff Protocol（v3.3 核心機制）

**解決 Context Limit 的根本方案**：使用檔案系統作為 Agent 間的「外部記憶體」。

→ 完整說明：[shared/coordination/file-based-handoff.md](../../shared/coordination/file-based-handoff.md)

### 為什麼會 Context Limit？

```
傳統方式：
  Agent A 完成 → 15K tokens 回傳 Orchestrator
  Agent B 完成 → 15K tokens 回傳
  Agent C 完成 → 15K tokens 回傳
  Agent D 完成 → 15K tokens 回傳
  ─────────────────────────────────
  總計：60K+ tokens → 爆炸 💥
```

### 新方式

```
File-Based Handoff：
  Agent A 完成 → 寫入檔案 → 回傳 "完成，見 path/a.md" (~100 tokens)
  Agent B 完成 → 寫入檔案 → 回傳 "完成，見 path/b.md" (~100 tokens)
  ...
  ─────────────────────────────────
  Orchestrator 只累積：~400 tokens ✅
  完整結果在：檔案系統 + Git
```

### 執行規則

1. **大型任務使用背景執行**：
   ```javascript
   Task({
     description: "複雜任務",
     prompt: "...結果寫入 {path}，只回覆確認",
     run_in_background: true  // 關鍵！
   })
   ```

2. **Agent 輸出到檔案**：
   - 完整報告 → `.claude/memory/{type}/{id}/result.md`
   - 回傳給 Orchestrator → 只說「完成，結果在 {path}」

3. **Git Checkpoint**：
   - 每批任務完成 → `git commit`
   - 即使 session 崩潰，結果保留

4. **下一階段讀取檔案**：
   - Orchestrator 告訴下一個 Agent 檔案路徑
   - Agent 自己用 Read 讀取

### Context 使用量對比

| 方式 | 4 個大型 Agent | Orchestrator Context |
|------|---------------|---------------------|
| 傳統 | 全部回傳 | ~60K tokens（危險）|
| File-Based | 只回傳路徑 | ~10K tokens（安全）|

## 智能並行決策（v3.2 新增）

當用戶要求同時執行多個任務時，Orchestrator 會智能決定執行策略。

→ 配置：[shared/config/parallel-execution.yaml](../../shared/config/parallel-execution.yaml)

### 並行度控制

| 任務複雜度 | 最大並行數 | 判斷依據 |
|-----------|-----------|----------|
| 簡單 | 4 | 單一模組、< 3 檔案、測試已存在 |
| 中等 | 2 | 跨模組、3-10 檔案、需新測試 |
| 複雜 | 1 | 架構變更、> 10 檔案、多階段 |

### 決策流程

```
用戶請求多任務
    ↓
┌─────────────────────────────────────┐
│  1. 分析每個任務的複雜度              │
│  2. 偵測任務間的依賴關係              │
│  3. 估算 context 消耗                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  決策：                              │
│  - 無依賴 + 簡單 → 全部並行           │
│  - 有依賴 → 拓撲排序後分批            │
│  - 複雜任務 → 順序執行                │
│  - context 緊張 → 降低並行度          │
└─────────────────────────────────────┘
    ↓
執行並監控
```

### 依賴偵測

自動偵測以下依賴：
- **檔案重疊**：修改相同檔案的任務不能並行
- **模組依賴**：A 模組 import B 模組，B 要先完成
- **測試依賴**：測試依賴實作，實作要先完成

### 範例

**輸入**：同時執行 4 個 Phase 1 任務

**分析**：
- 複雜度：全部是複雜任務
- 依賴：無直接依賴
- 估算 context：高

**決策**：
```
批次 1: [智能待辦 P1, 動態 Skill P1]  → 並行
  ↓ 完成後 /compact
批次 2: [記憶演化 P1, 分布式記憶 P1]  → 並行
```

**原因**：每批 2 個任務，避免 context 爆炸。

## Context Limit 處理（v3.2 新增）

→ 指南：[shared/coordination/context-limit-handler.md](../../shared/coordination/context-limit-handler.md)

### 預防機制

1. **監控閾值**：
   - < 50%：正常並行
   - 50-70%：減少到 2 並行
   - 70-85%：順序執行
   - \> 85%：暫停並壓縮

2. **即時壓縮**：
   - Agent 完成後只保留摘要在 context
   - 完整輸出保存到檔案

3. **背景執行**：
   - 大型任務使用 `run_in_background: true`
   - 不佔用 orchestrator 的 context

### 發生時的處理

當看到 "Context limit reached"：

```
┌─────────────────────────────────────┐
│  1. 記錄哪些 Agent 已完成            │
│  2. 記錄哪些 Agent 還在運行          │
│  3. 開新 session                    │
│  4. 執行完成狀態檢查：               │
│     - git status                    │
│     - pnpm typecheck                │
│     - pnpm test <paths>             │
│  5. 從中斷點繼續，降低並行度          │
└─────────────────────────────────────┘
```

### 進度保存

自動保存到 `.claude/workflow/{id}/recovery/progress.yaml`：

```yaml
tasks:
  - id: "task-1"
    status: "completed"
    commit: "abc123"
  - id: "task-2"
    status: "in_progress"
    last_checkpoint: "80%"
```

### 恢復指令模板

```markdown
我需要繼續之前因 context limit 中斷的工作。

**已完成**：
- [x] 任務 A（已 commit）
- [x] 任務 B（未 commit 但完整）

**未完成**：
- [ ] 任務 C（進度 80%）

請：
1. 先 commit 任務 B
2. 驗證並繼續任務 C
3. **一個一個執行，不要並行**
```

## 新增 Flags（v3.2）

- `--max-parallel <n>` - 限制最大並行數（預設：自動決定）
- `--sequential` - 強制順序執行所有任務
- `--save-progress` - 每個任務完成後保存進度檔
- `--resume <progress-file>` - 從進度檔恢復執行
