# File-Based Handoff Protocol

> 使用檔案系統和 Git 作為 Agent 間的「外部記憶體」，避免 Context Limit

## 核心概念

```
傳統方式（會爆 context）：
  Agent A 完成 → 結果全部回傳 Orchestrator → 傳給 Agent B
                      ↑
                  這裡累積太多

新方式（檔案系統作為中介）：
  Agent A 完成 → 寫入檔案 → Git commit
                              ↓
  Agent B 啟動 ← 讀取檔案路徑 ← Orchestrator 只記路徑
                              ↑
                          只有幾行字
```

## 為什麼這樣有效？

| 項目 | 傳統方式 | File-Based |
|------|----------|------------|
| Orchestrator 收到的 | 完整報告（~15K tokens） | "完成，見 path/x.md"（~100 tokens） |
| 下一個 Agent 如何取得資料 | 從 context 繼承 | 自己用 Read 讀檔案 |
| Context 增長 | 線性累積 | 保持平穩 |
| 可恢復性 | 低（session 死就沒了） | 高（檔案和 git 都在） |

## 實作規則

### Rule 1: Agent 必須寫檔案

每個 Agent 完成時必須：

```markdown
### 強制輸出要求

1. 將完整結果寫入：
   Write → .claude/memory/{type}/{id}/{output_file}.md

2. 返回時只說：
   "✅ 完成。結果已保存至 {path}"

3. 不要在回覆中包含完整報告內容
```

### Rule 2: Orchestrator 只記錄路徑

Orchestrator 的 prompt 應該要求：

```markdown
### Agent 結果處理

當 Agent 完成時：
1. 記錄：任務名稱、狀態、輸出路徑
2. 不要複製 Agent 的完整輸出
3. 下一個 Agent 會自己讀取檔案
```

### Rule 3: 使用 run_in_background

對於大型任務，使用背景執行：

```javascript
Task({
  description: "複雜分析任務",
  prompt: `
    ...
    完成後將結果寫入 .claude/memory/analysis/result.md
    只回覆確認訊息，不要輸出完整內容
  `,
  run_in_background: true,  // 關鍵！
  subagent_type: "general-purpose"
})
```

**背景執行的好處**：
- Agent 的輸出不會進入 Orchestrator 的 context
- 透過 TaskOutput 只取得狀態，不取得完整內容
- 完整結果在檔案系統中

### Rule 4: Git 作為 Checkpoint

每個重要步驟後 commit：

```bash
# Agent 完成後自動執行
git add .claude/memory/{type}/{id}/
git commit -m "checkpoint({type}): {task_name} complete"
```

**好處**：
- 即使 session 崩潰，工作成果保留
- 新 session 可以從 git log 理解進度
- 可以回滾到任何 checkpoint

## 完整流程示例

### 場景：4 個 Phase 1 任務

```
Session 開始
    ↓
Orchestrator 分析任務
    ↓
┌─────────────────────────────────────────────────────────────┐
│  批次 1: 啟動 Agent A 和 B（背景執行）                       │
│                                                              │
│  Task({ run_in_background: true, prompt: "...寫入 path/a" })│
│  Task({ run_in_background: true, prompt: "...寫入 path/b" })│
└─────────────────────────────────────────────────────────────┘
    ↓
Orchestrator context 只增加：
  "已啟動 Agent A (task_id: xxx)"
  "已啟動 Agent B (task_id: yyy)"
    ↓
等待完成（定期檢查 TaskOutput）
    ↓
完成後，Orchestrator context 增加：
  "Agent A 完成，輸出: .claude/memory/.../a.md"
  "Agent B 完成，輸出: .claude/memory/.../b.md"
    ↓
Git commit checkpoint
    ↓
┌─────────────────────────────────────────────────────────────┐
│  批次 2: 啟動 Agent C 和 D（同樣方式）                       │
└─────────────────────────────────────────────────────────────┘
    ↓
全部完成
    ↓
最終 Orchestrator context 使用量：~15K（而不是 70K+）
```

## Orchestrator Prompt 範本

```markdown
## 任務執行規則

### 啟動 Agent

使用 Task 工具時：
1. 設定 `run_in_background: true`（大型任務）
2. 在 prompt 中指定輸出路徑
3. 要求 Agent 只回覆確認訊息

### 追蹤進度

使用 TaskOutput 檢查狀態：
1. 只關注「完成/進行中/失敗」
2. 不需要讀取完整輸出
3. 記錄輸出檔案路徑

### 傳遞給下一階段

下一個 Agent 的 prompt 應包含：
```
### 前置作業輸出

請讀取以下檔案以獲取上一階段的結果：
- {path_to_previous_output}
```

而不是直接把內容貼進 prompt。

### Git Checkpoint

每完成一批任務：
1. `git add .claude/memory/`
2. `git commit -m "checkpoint: {description}"`
```

## 錯誤恢復

### 如果 Session 崩潰

```bash
# 新 Session
git log --oneline -10  # 查看 checkpoints
git status             # 查看未 commit 的變更

# 讀取最後的進度
cat .claude/memory/workflows/{id}/progress.yaml

# 繼續執行
```

### 如果某個 Agent 失敗

```bash
# 結果檔案不存在或不完整
# 重新執行該 Agent，其他 Agent 的結果不受影響
```

## 配置更新

將此協議加入 parallel-execution.yaml：

```yaml
handoff_protocol:
  type: "file_based"

  agent_output:
    destination: "file"  # 不是 "context"
    path_pattern: ".claude/memory/{type}/{id}/{agent_id}.md"

  orchestrator_tracking:
    store: "path_only"  # 只記錄路徑
    full_content: false

  checkpoint:
    enabled: true
    trigger: "batch_complete"
    method: "git_commit"
```

## 總結

```
┌─────────────────────────────────────────────────────────────┐
│  Context Limit 解決方案                                     │
│                                                              │
│  1. Agent 寫檔案，不回傳完整內容                            │
│  2. Orchestrator 只記路徑                                   │
│  3. 下一個 Agent 自己讀檔案                                 │
│  4. Git commit 作為 checkpoint                              │
│  5. 大任務用 run_in_background                              │
│                                                              │
│  結果：Context 使用量從 70K+ 降到 ~15K                      │
└─────────────────────────────────────────────────────────────┘
```
