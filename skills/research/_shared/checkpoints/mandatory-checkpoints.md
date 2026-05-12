# 強制檢查點協議（Mandatory Checkpoints）

> **此協議已自動化** - Claude Code Hooks 會自動處理 logging、state tracking 和 git commit。
>
> Skill 只需要在正確時機調用初始化腳本。

## 自動化機制

| 操作 | 觸發時機 | 處理方式 |
|------|---------|---------|
| Action Logging | Write/Task 工具調用 | PostToolUse Hook |
| Agent 狀態追蹤 | Task 啟動/完成 | PreToolUse + PostToolUse Hook |
| Memory Commit | **子代理完成時** | **SubagentStop Hook** |

> ⚠️ **注意**: git commit 在 SubagentStop 時執行，而非每次 Write。
> 這避免了多次小 commit，確保每個 Task 完成時有一個完整的 commit。

## 檢查點清單

### CP1: 工作流初始化 ⚡ 手動

**觸發時機**：skill 開始時

**必須執行**：
```bash
python scripts/hooks/init_workflow.py \
  --topic "{topic}" \
  --stage {STAGE}
```

**輸出**：
```json
{
  "workflow_id": "user-auth_20260126_a1b2c3",
  "workflow_dir": ".claude/workflow/user-auth_20260126_a1b2c3",
  "state": { ... }
}
```

### CP2: Agent 啟動 ✅ 自動

**由 `pre_task.py` 自動處理**

當 Task 工具被調用時，Hook 會自動：
- 更新 `current.json` 中的 agent 狀態為 `running`
- 記錄 `agent_start` action

### CP3: Agent 完成 ✅ 自動

**由 `post_task.py` 自動處理**

當 Task 工具返回時，Hook 會自動：
- 更新 `current.json` 中的 agent 狀態為 `completed` 或 `failed`
- 記錄 `agent_complete` action

### CP3.5: Memory 存檔 ✅ 自動

**由 `post_write.py` 自動處理**

當 Write 工具寫入檔案時，Hook 會自動：
- 記錄 `file_write` action

### CP4: Task Commit ✅ 自動

**由 `subagent_stop.py` 自動處理**

當子代理（Task）完成時（SubagentStop 事件），Hook 會自動：
1. 檢查 `.claude/memory/` 是否有變更
2. `git add .claude/memory/{type}/{id}/`
3. `git commit` with appropriate message
4. 記錄 `git_commit` action

> 這確保每個 Task 完成時才 commit，避免多次小 commit。

## Commit Message 格式

| Type | Scope | 範例 |
|------|-------|------|
| docs | research | `docs(research): complete user-auth research` |
| feat | plan | `feat(plan): design user-auth implementation` |
| feat | tasks | `feat(tasks): decompose user-auth into 12 tasks` |
| feat/fix | implement | `feat(implement): add login endpoint` |
| docs | review | `docs(review): complete user-auth code review` |
| test | verify | `test(verify): verify user-auth implementation` |

## Skill 需要做的事

### 1. 開始時初始化 (CP1)

```bash
# 在 skill 開頭執行
result=$(python scripts/hooks/init_workflow.py --topic "用戶認證" --stage RESEARCH)
workflow_id=$(echo "$result" | jq -r '.workflow_id')
```

### 2. 其他操作自動處理

- ✅ Task 啟動/完成 → 自動記錄
- ✅ 檔案寫入 → 自動記錄
- ✅ Memory 寫入 → 自動 commit

### 3. 驗證

```bash
# 檢查狀態
cat .claude/workflow/{workflow_id}/current.json | jq .

# 檢查日誌
tail -20 .claude/workflow/{workflow_id}/logs/actions.jsonl

# 檢查 commit
git log --oneline -5
```

## 設定檔位置

複製 `.claude/settings.local.json.template` 到 `.claude/settings.local.json`：

```bash
cp .claude/settings.local.json.template .claude/settings.local.json
```

設定內容：
```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Task", "hooks": [{"type": "command", "command": "python \"$CLAUDE_PROJECT_DIR\"/scripts/hooks/pre_task.py"}] }
    ],
    "PostToolUse": [
      { "matcher": "Write", "hooks": [{"type": "command", "command": "python \"$CLAUDE_PROJECT_DIR\"/scripts/hooks/post_write.py"}] },
      { "matcher": "Task", "hooks": [{"type": "command", "command": "python \"$CLAUDE_PROJECT_DIR\"/scripts/hooks/post_task.py"}] }
    ],
    "SubagentStop": [
      { "hooks": [{"type": "command", "command": "python \"$CLAUDE_PROJECT_DIR\"/scripts/hooks/subagent_stop.py"}] }
    ]
  }
}
```

> ⚠️ Hook 腳本從 stdin 讀取 JSON，使用 `$CLAUDE_PROJECT_DIR` 確保路徑正確。

## 故障排除

### 沒有 log

1. 檢查 `.claude/settings.local.json` 是否存在
2. 檢查 `scripts/hooks/*.py` 是否可執行
3. 手動測試: `python scripts/hooks/log_action.py --tool Test --status success`

### 沒有 commit

1. 確認 SubagentStop hook 已配置
2. 確認寫入路徑是 `.claude/memory/` 開頭
3. 檢查 git status
4. 手動測試:
   ```bash
   echo '{"session_id": "test", "cwd": "'$(pwd)'"}' | python scripts/hooks/subagent_stop.py
   ```

### Dashboard 沒更新

1. 檢查 `current.json` 是否存在
2. 確認 workflow 已初始化 (CP1)
3. 手動測試: `python scripts/hooks/update_state.py --workflow-id test --agent-id test --agent-status running`
