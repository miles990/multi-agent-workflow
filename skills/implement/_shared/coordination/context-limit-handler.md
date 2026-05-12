# Context Limit 處理指南

> 當遇到 "Context limit reached" 時的標準處理流程

## 問題描述

當多個大型 Agent 並行執行時，Orchestrator 的 context window 可能達到上限：
- 每個 Agent 的輸出都會累積到 Orchestrator 的 context
- `/compact` 可能因為對話太長而失敗
- 需要開新 session 繼續工作

## 預防機制

### 1. 並行度控制

```yaml
# 參考 shared/config/parallel-execution.yaml
max_concurrent_tasks: 2  # 最多 2 個並行
```

### 2. 使用背景執行

對於大型任務，使用 `run_in_background: true`：

```javascript
Task({
  description: "複雜任務",
  prompt: "...",
  run_in_background: true  // 不佔用 orchestrator context
})
```

### 3. 即時壓縮 Agent 輸出

每個 Agent 完成後，只保留摘要：

```markdown
## Agent 完成

**任務**: {task_name}
**狀態**: ✅ 完成
**輸出**: 已保存至 {output_path}
**摘要**: {3-5 句重點}

（完整輸出請讀取 {output_path}）
```

## 發生時的處理流程

### Phase 1: 立即保存進度

當看到 "Context limit reached" 訊息時：

```
┌─────────────────────────────────────────────────────────────┐
│  1. 記錄當前狀態                                              │
│     - 哪些 Agent 顯示 "completed"                            │
│     - 哪些 Agent 還在運行                                     │
│     - 最後一次成功的操作是什麼                                │
└─────────────────────────────────────────────────────────────┘
```

### Phase 2: 在舊 Session 嘗試（如果可能）

如果還能輸入命令：

```bash
# 嘗試 1: 按 ESC 兩次，回退幾條訊息
# （如錯誤訊息所建議的）

# 嘗試 2: 如果可以，先 commit 已完成的工作
git add <completed_files>
git commit -m "wip: save progress before context limit"
```

### Phase 3: 開新 Session

```bash
# 1. 開新 session
cd /path/to/project
claude

# 2. 檢查狀態
git status
git log --oneline -5

# 3. 驗證已完成的工作
pnpm typecheck
pnpm test <affected_paths>

# 4. 識別未完成的工作
# 查看 git status 中的 untracked 或 modified 文件
```

### Phase 4: 繼續未完成的工作

```markdown
## 恢復指令模板

我需要繼續之前因 context limit 中斷的工作。

**已完成**：
- [x] 任務 A（已 commit: abc123）
- [x] 任務 B（已 commit: def456）

**未完成**：
- [ ] 任務 C（進度：80%，輸出在 src/xxx/）
- [ ] 任務 D（未開始）

請幫我：
1. 檢查任務 C 的完成狀態
2. 如果不完整，繼續完成
3. 完成後執行任務 D

**注意**：這次請一個一個執行，不要並行。
```

## 完成狀態檢查清單

### 如何判斷任務是否完整？

| 檢查項目 | 命令 | 完整標準 |
|----------|------|----------|
| TypeScript | `pnpm typecheck` | 無錯誤 |
| 測試 | `pnpm test <path>` | 全通過 |
| 文件結構 | `ls src/<module>/` | 有 index.ts + 主要文件 |
| Git | `git status` | 知道哪些需要 commit |
| 導出 | `grep "export" src/<module>/index.ts` | 必要的導出都在 |

### 快速驗證腳本

```bash
# 放在 scripts/verify-completion.sh
#!/bin/bash
MODULE=$1

echo "=== Checking $MODULE ==="

# 1. 檔案結構
echo "📁 Files:"
ls -la src/$MODULE/

# 2. TypeScript
echo "📝 TypeScript:"
pnpm typecheck 2>&1 | grep -E "error|warning" | head -10

# 3. 測試
echo "🧪 Tests:"
pnpm test tests/unit/$MODULE/ 2>&1 | tail -5

# 4. 導出
echo "📤 Exports:"
grep "export" src/$MODULE/index.ts
```

## 進度保存格式

當 context limit 即將發生時，保存以下資訊：

```yaml
# .claude/workflow/{id}/recovery/progress.yaml
version: "1.0"
workflow_id: "orchestrate_20260131_180000_abcd"
timestamp: "2026-01-31T18:00:00Z"
interrupted_by: "context_limit"

tasks:
  - id: "todo-p1"
    name: "智能待辦 Phase 1"
    status: "completed"
    commit: "cd578be"
    output_files:
      - "src/todo/store.ts"
      - "src/todo/manager.ts"
      - "tests/unit/todo/"

  - id: "evolution-p1"
    name: "記憶演化 Phase 1"
    status: "completed"
    commit: null  # 未 commit
    output_files:
      - "src/memory/evolution/"
      - "tests/unit/memory/evolution.test.ts"
    verification:
      typecheck: "pass_with_warning"
      tests: "29/29 pass"

  - id: "skill-p1"
    name: "動態 Skill Phase 1"
    status: "completed"
    commit: "92d675b"

  - id: "memory-repo-p1"
    name: "分布式記憶 Phase 1"
    status: "in_progress"  # 正在執行時中斷
    last_checkpoint: "github provider 完成"
    remaining:
      - "local provider 測試"
      - "整合測試"

recovery_instructions: |
  1. 先 commit evolution-p1 的變更
  2. 繼續 memory-repo-p1 從 local provider 測試開始
  3. 使用順序執行，不要並行
```

## 舊 Session 的處理

### 可以做的事

1. **查看 session 歷史**（如果 Claude Code 支援）
2. **從終端機歷史找線索**：
   ```bash
   history | grep -E "git|pnpm|claude"
   ```
3. **檢查臨時檔案**：
   ```bash
   ls -la /tmp/*claude* 2>/dev/null
   ls -la .claude/workflow/
   ```

### 不能做的事

1. **不能恢復舊 session 的 context** - 已經丟失
2. **不能在舊 session 繼續** - 必須開新的
3. **不能完全還原中斷時的狀態** - 只能從檔案系統重建

### 最佳實踐

```
1. 養成習慣：每完成一個 Phase 就 commit
2. 大任務分批執行，不要一次啟動太多
3. 使用 run_in_background 執行獨立任務
4. 定期 /compact 減少 context 使用
5. 監控 context 使用量（statusline 會顯示）
```

## 預設的並行策略建議

根據任務類型選擇並行度：

| 任務類型 | 建議並行度 | 原因 |
|----------|-----------|------|
| 完整 /orchestrate | 1 | 本身就是大型流程 |
| Phase 1 類任務 | 2 | 每個都可能有多視角 |
| 簡單修復 | 3-4 | 快速完成，低 context 消耗 |
| 研究/探索 | 2 | 中等 context 消耗 |

## 總結

```
┌─────────────────────────────────────────────────────────────┐
│  Context Limit 處理三步驟                                    │
│                                                              │
│  1. 保存：記錄完成狀態、commit 已完成的工作                  │
│  2. 驗證：typecheck、test 確認哪些是完整的                   │
│  3. 繼續：在新 session 從中斷點繼續，降低並行度              │
└─────────────────────────────────────────────────────────────┘
```
