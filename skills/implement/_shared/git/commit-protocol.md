# Git Commit Protocol（共用模組）

> Task 完成後自動 commit 的標準協議

## 概述

確保每個 Task（skill 階段）完成後都自動執行 git commit，保持工作進度的持久化。

**此為共用模組**，被所有 skill 在 CP4 checkpoint 時引用。

## Commit 時機

每個 skill 的主要階段完成後觸發 CP4：

| Skill | 觸發點 | Commit 內容 |
|-------|--------|-------------|
| **research** | Phase 5 後 | 研究報告 + perspectives/ + summaries/ |
| **plan** | Phase 6 後 | 實作計劃 + perspectives/ + summaries/ |
| **tasks** | Phase 6 後 | tasks.yaml + perspectives/ + summaries/ |
| **implement** | 每個 task 完成後 | 程式碼變更 + task-results/ |
| **review** | Phase 4 後 | 審查報告 + issues.yaml |
| **verify** | Phase 4 後 | 驗證結果 + test-results.yaml |

## Commit Message 格式

### 標準格式

```
{type}({skill}): {brief_description}

{details}

Memory: .claude/memory/{type}/{id}/
Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

### Type 對應

| Skill | Type | 說明 |
|-------|------|------|
| research | `docs` | 研究產出 |
| plan | `feat` | 新功能規劃 |
| tasks | `feat` | 任務分解 |
| implement | `feat`/`fix` | 實作或修復 |
| review | `docs` | 審查報告 |
| verify | `test` | 驗證結果 |

### 範例

```
docs(research): complete user-auth research

- 4 perspectives analyzed
- Synthesis report generated
- Quality score: 85

Memory: .claude/memory/research/user-auth/
Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

```
feat(plan): design user-auth implementation plan

- 12 tasks defined
- Dependencies mapped
- Risk analysis completed

Memory: .claude/memory/plans/user-auth/
Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

```
feat(implement): add login endpoint

- POST /api/auth/login implemented
- JWT token generation
- Unit tests passing

Memory: .claude/memory/implement/user-auth/task-results/task-001.yaml
Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

## 執行流程

### CP4 觸發條件

```yaml
cp4_trigger:
  prerequisite: "CP3.5 Memory 存檔完成"
  check:
    - memory_files_exist: true
    - primary_output_complete: true
```

### 執行步驟

```yaml
cp4_task_commit:
  steps:
    1. check_changes:
        command: "git status --porcelain"
        if_no_changes: "skip commit, continue workflow"

    2. stage_changes:
        primary: ".claude/memory/{type}/{id}/"
        secondary: "相關程式碼變更（如果有）"
        command: |
          git add .claude/memory/{type}/{id}/
          git add {code_changes}  # 如果有

    3. generate_commit_message:
        format: "{type}({skill}): {description}"
        include:
          - 變更摘要
          - Memory 路徑
          - Co-Author

    4. execute_commit:
        command: |
          git commit -m "$(cat <<'EOF'
          {type}({skill}): {description}

          {details}

          Memory: .claude/memory/{type}/{id}/
          Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
          EOF
          )"

    5. verify_success:
        command: "git log -1 --oneline"
        record: "commit_hash"
```

## 失敗處理

### 失敗類型與處理

```yaml
on_failure:
  no_changes:
    action: skip
    message: "無變更需要 commit"
    continue: true

  stage_error:
    action: warn
    message: "部分檔案無法 stage: {error}"
    continue: true
    fallback: "嘗試只 stage Memory 目錄"

  commit_error:
    action: warn
    message: "Commit 失敗: {error}"
    continue: true
    fallback: "記錄到 workflow.yaml，提醒用戶手動處理"

  pre_commit_hook_fail:
    action: fix_and_retry
    steps:
      1. "分析錯誤類型"
      2. "自動修復（如 lint）"
      3. "重新嘗試 commit"
    max_retries: 2
    on_final_fail:
      action: warn
      message: "Pre-commit hook 持續失敗，請手動處理"
      continue: true
```

### 錯誤恢復

```markdown
## CP4 Commit 警告

### 狀態
⚠️ Commit 未能完成

### 原因
{error_message}

### 待處理變更
```bash
git status
```

### 建議操作
1. 手動檢查 git status
2. 解決問題後執行：
   ```bash
   git add .claude/memory/{type}/{id}/
   git commit -m "{suggested_message}"
   ```
```

## 與其他 Checkpoint 的關係

```
CP3: 目標確認
    ↓
CP3.5: Memory 存檔
    ↓
CP4: Task Commit（本協議）
    ↓
繼續下一階段或結束
```

## 注意事項

### 安全性

- **不自動 push**：commit 只在本地執行，push 需要用戶確認
- **不 commit 敏感資料**：自動排除 `.env`、credentials 等
- **保留用戶選擇**：如果用戶不想 commit，可以跳過

### 效能

- **批次處理**：如果多個檔案需要 stage，一次完成
- **非阻塞**：commit 失敗不阻塞主工作流

### 相容性

- **Worktree 模式**：在 worktree 中執行時，commit 在該分支進行
- **Main 模式**：直接在 main 分支 commit（需注意 review 後再 push）
