# Worktree Completion（共用模組）

> Git Worktree 的完成與清理規範

## 概述

在 VERIFY 階段完成後，根據結果處理 Worktree：
- **SHIP IT** → 合併到 main + 清理 worktree
- **BLOCKED** → 保留 worktree 繼續迭代
- **ABORT** → 詢問保留 patch 或完全刪除

**此為共用模組**，定義 Worktree 完成的標準流程。

## 完成流程

```
┌─────────────────────────────────────────────────────────────┐
│                   CP6.5: Worktree Completion                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  VERIFY 結果判斷                                             │
│      ↓                                                       │
│  ┌──────────────────────────────────────────────────────────┐
│  │                                                          │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │
│  │  │  SHIP IT   │  │  BLOCKED   │  │   ABORT    │         │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘         │
│  │        ↓               ↓               ↓                 │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │
│  │  │ 合併流程   │  │ 保留迭代   │  │ 清理選項   │         │
│  │  │            │  │            │  │            │         │
│  │  │ 1. Push    │  │ 1. 保留    │  │ 1. 保留    │         │
│  │  │ 2. PR      │  │    worktree│  │    patch   │         │
│  │  │ 3. Merge   │  │ 2. 繼續    │  │ 2. 刪除    │         │
│  │  │ 4. Cleanup │  │    迭代    │  │    一切    │         │
│  │  └────────────┘  └────────────┘  └────────────┘         │
│  │                                                          │
│  └──────────────────────────────────────────────────────────┘
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## SHIP IT 流程

### 完整合併流程

```yaml
ship_it_flow:
  steps:
    1. final_verification:
        - all_tests_pass
        - no_uncommitted_changes
        - branch_up_to_date

    2. push_branch:
        command: "git push -u origin feature/{id}"
        on_fail: retry_with_force_if_needed

    3. create_pr:
        method: auto | manual
        auto:
          command: |
            gh pr create \
              --title "{feature_title}" \
              --body "{pr_template}" \
              --base main
        manual:
          message: "請手動創建 PR"
          url: "{repo_url}/compare/main...feature/{id}"

    4. merge_pr:
        method: auto | manual
        auto:
          wait_for_ci: true
          merge_method: squash | rebase | merge
        manual:
          message: "請手動合併 PR"

    5. cleanup:
        - git worktree remove .worktrees/{id}
        - git branch -d feature/{id}
        - update workflow.yaml state = "merged"
```

### 合併策略選項

```yaml
merge_strategies:
  squash:
    description: "壓縮為單一 commit"
    use_when:
      - many_small_commits
      - feature_is_atomic
    command: "gh pr merge --squash"

  rebase:
    description: "重寫 commit 歷史"
    use_when:
      - clean_commit_history
      - want_linear_history
    command: "gh pr merge --rebase"

  merge:
    description: "保留完整歷史"
    use_when:
      - want_full_history
      - complex_feature
    command: "gh pr merge --merge"

  default: squash
  flag: "--merge-strategy STR"
```

### 清理命令

```bash
# 完整清理流程
cd {main_directory}
git worktree remove .worktrees/{feature-id}
git branch -d feature/{feature-id}
git remote prune origin
```

## BLOCKED 流程

### 保留 Worktree

```yaml
blocked_flow:
  action: preserve_worktree

  steps:
    1. update_state:
        workflow.yaml:
          worktree.state: "blocked"
          current_stage: "IMPLEMENT"
          iteration: iteration + 1

    2. document_blockers:
        file: "workflows/{id}/blockers-iteration-{n}.md"
        content:
          - failure_summary
          - failed_tests
          - suggested_fixes

    3. notify_user:
        message: |
          ⚠️ 驗證失敗，需要修正

          Worktree 保留在：{worktree_path}

          繼續迭代：
          cd {worktree_path}
          # 修正問題
          /multi-orchestrate --resume {id}

    4. keep_worktree:
        action: no_cleanup
        reason: "continue iteration"
```

### 恢復迭代

```bash
# 恢復被 BLOCKED 的工作流
/multi-orchestrate --resume {feature-id}

# 指定從特定階段恢復
/multi-orchestrate --resume {feature-id} --start-at implement
```

## ABORT 流程

### 使用者選項

```yaml
abort_flow:
  trigger:
    - user_cancellation
    - max_iterations_exceeded
    - unrecoverable_error

  options:
    1. preserve_patch:
        description: "保留變更為 patch 文件"
        action:
          1. git diff main...HEAD > {patch_file}
          2. git worktree remove .worktrees/{id}
          3. git branch -D feature/{id}
        output: |
          ✅ Patch 已保存：{patch_file}

          日後恢復：
          git apply {patch_file}

    2. delete_all:
        description: "刪除所有變更"
        confirmation: "確定要刪除所有工作嗎？此操作不可恢復。[y/N]"
        action:
          1. git worktree remove --force .worktrees/{id}
          2. git branch -D feature/{id}
          3. update workflow.yaml state = "abandoned"
        output: |
          ✅ 已清理：
          - Worktree: .worktrees/{id}
          - Branch: feature/{id}

    3. lock_worktree:
        description: "鎖定 worktree（防止意外刪除）"
        action:
          1. git worktree lock .worktrees/{id}
          2. update workflow.yaml state = "locked"
        output: |
          🔒 Worktree 已鎖定

          解鎖命令：
          git worktree unlock .worktrees/{id}
```

### Patch 文件格式

```yaml
patch_file:
  path: ".claude/memory/patches/{feature-id}-{timestamp}.patch"

  metadata:
    header: |
      # Patch: {feature-id}
      # Created: {timestamp}
      # Commits: {commit_count}
      # Files changed: {files_count}
      #
      # Apply with: git apply {filename}
```

## workflow.yaml 狀態更新

### 狀態定義

```yaml
worktree_states:
  active:
    description: "Worktree 正在使用中"
    transitions:
      - to: merged (on SHIP_IT)
      - to: blocked (on BLOCKED)
      - to: abandoned (on ABORT + delete)
      - to: locked (on ABORT + lock)

  blocked:
    description: "等待修正後繼續"
    transitions:
      - to: active (on resume)
      - to: merged (on SHIP_IT)
      - to: abandoned (on ABORT)

  merged:
    description: "已合併到 main，worktree 已清理"
    final: true

  abandoned:
    description: "已放棄，worktree 已清理"
    final: true

  locked:
    description: "已鎖定，防止意外刪除"
    transitions:
      - to: active (on unlock + resume)
      - to: abandoned (on unlock + delete)
```

### 狀態更新範例

```yaml
# SHIP IT 後
workflow:
  worktree:
    state: "merged"
    merged_at: "{timestamp}"
    merge_commit: "{sha}"
    pr_number: "{pr_number}"

# BLOCKED 後
workflow:
  worktree:
    state: "blocked"
    blocked_at: "{timestamp}"
    block_reason: "{reason}"

# ABORT 後（保留 patch）
workflow:
  worktree:
    state: "abandoned"
    abandoned_at: "{timestamp}"
    patch_file: "{patch_path}"

# ABORT 後（完全刪除）
workflow:
  worktree:
    state: "abandoned"
    abandoned_at: "{timestamp}"
    patch_file: null
```

## 清理孤立 Worktrees

### 清理命令

```bash
# 列出所有 worktrees
git worktree list

# 清理孤立的 worktrees
git worktree prune

# 強制清理特定 worktree
git worktree remove --force .worktrees/{id}
```

### 批量清理

```yaml
cleanup_worktrees:
  flag: "--cleanup-worktrees"

  action:
    1. list_all_worktrees
    2. identify_orphans:
        - no matching workflow.yaml
        - state == "abandoned"
        - created > 30 days ago
    3. prompt_confirmation:
        message: |
          發現 {count} 個可清理的 worktrees：
          {worktree_list}

          確定要清理嗎？[y/N]
    4. cleanup_confirmed
```

## Flags

```bash
# 合併控制
--merge-strategy STR    # squash（預設）| rebase | merge
--auto-merge            # 自動合併（不創建 PR）
--no-cleanup            # 合併後不刪除 worktree

# 清理控制
--cleanup-worktrees     # 清理所有孤立的 worktrees
--force-cleanup         # 強制清理（跳過確認）

# 放棄控制
--abandon               # 放棄工作流
--keep-patch            # 放棄時保留 patch
--no-patch              # 放棄時不保留 patch
```

## 相關資源

- [Worktree Setup](./worktree-setup.md)
- [Path Resolution](./path-resolution.md)
- [Rollback Rules](../../skills/orchestrate/03-error-handling/_base/rollback-rules.md)
