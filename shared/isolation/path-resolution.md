# Path Resolution（共用模組）

> Worktree 環境中的路徑解析規範

## 概述

在 Worktree 模式下，需要正確區分：
- **程式碼路徑**：在 worktree 目錄中
- **Memory 路徑**：始終在 main 目錄中

**此為共用模組**，定義路徑解析的標準邏輯。

## 核心原則

```
┌─────────────────────────────────────────────────────────────┐
│                    路徑解析規則                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  程式碼（Code）                Memory                        │
│      ↓                            ↓                          │
│  ┌──────────────┐          ┌──────────────┐                 │
│  │   Worktree   │          │     Main     │                 │
│  │   目錄       │          │    目錄      │                 │
│  │              │          │              │                 │
│  │ .worktrees/  │          │ .claude/     │                 │
│  │   {id}/      │          │   memory/    │                 │
│  │   src/       │          │              │                 │
│  │   tests/     │          │              │                 │
│  └──────────────┘          └──────────────┘                 │
│                                                              │
│  為什麼分離？                                                │
│  - Memory 是單一事實來源                                     │
│  - 避免 worktree 間的 Memory 衝突                            │
│  - 簡化 Memory 同步邏輯                                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Worktree 檢測

### 檢測當前環境

```yaml
worktree_detection:
  method: "git rev-parse"

  commands:
    # 檢查是否在 worktree 中
    is_worktree: |
      git rev-parse --git-common-dir 2>/dev/null | grep -q "\.git/worktrees"

    # 獲取 worktree 根目錄
    worktree_root: |
      git rev-parse --show-toplevel

    # 獲取 main 專案目錄
    main_directory: |
      git rev-parse --git-common-dir | sed 's|/.git/worktrees/.*|/.git|' | xargs dirname

  results:
    in_worktree: true | false
    worktree_path: "/path/to/.worktrees/{id}"
    main_path: "/path/to/project"
```

### 檢測邏輯流程

```
┌─────────────────────────────────────────────────────────────┐
│                    環境檢測流程                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  git rev-parse --git-common-dir                              │
│      ↓                                                       │
│  結果包含 ".git/worktrees"？                                 │
│      ↓                                                       │
│  ┌────────────────────┬────────────────────┐                │
│  │        是          │        否          │                │
│  │   在 Worktree 中   │   在 Main 目錄中   │                │
│  │                    │                    │                │
│  │   memory_path =    │   memory_path =    │                │
│  │   {main}/.claude/  │   ./.claude/       │                │
│  │   memory/          │   memory/          │                │
│  └────────────────────┴────────────────────┘                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 路徑解析函數

### 偽代碼

```yaml
path_resolution:
  get_memory_path:
    description: "獲取 Memory 存儲路徑"
    logic: |
      if is_in_worktree():
          main_dir = get_main_directory()
          return f"{main_dir}/.claude/memory"
      else:
          return ".claude/memory"

  get_code_path:
    description: "獲取程式碼路徑"
    logic: |
      # 總是使用當前目錄（可能是 worktree 或 main）
      return git_toplevel()

  get_worktree_path:
    description: "獲取 worktree 路徑"
    logic: |
      if is_in_worktree():
          return git_toplevel()
      elif workflow_has_worktree():
          return workflow.worktree.directory
      else:
          return None
```

### 實際命令

```bash
# 獲取 Memory 路徑
get_memory_path() {
    local git_common=$(git rev-parse --git-common-dir 2>/dev/null)

    if [[ "$git_common" == *".git/worktrees"* ]]; then
        # 在 worktree 中，解析 main 目錄
        local main_dir=$(echo "$git_common" | sed 's|/.git/worktrees/.*||')
        echo "$main_dir/.claude/memory"
    else
        # 在 main 目錄中
        echo "$(git rev-parse --show-toplevel)/.claude/memory"
    fi
}

# 獲取 Code 路徑
get_code_path() {
    git rev-parse --show-toplevel
}

# 檢查是否在 worktree 中
is_in_worktree() {
    git rev-parse --git-common-dir 2>/dev/null | grep -q "\.git/worktrees"
}
```

## workflow.yaml 路徑記錄

### 路徑欄位

```yaml
workflow:
  id: "{feature-id}"

  paths:
    main_directory: "/absolute/path/to/project"
    worktree_directory: "/absolute/path/to/project/.worktrees/{id}"
    memory_base: "/absolute/path/to/project/.claude/memory"

  # 各階段產出物路徑
  artifacts:
    plan: "{memory_base}/plans/{id}/"
    implementation: "{memory_base}/implementations/{id}/"
    review: "{memory_base}/reviews/{id}/"
    verification: "{memory_base}/verifications/{id}/"
```

### 路徑解析時機

```yaml
path_resolution_timing:
  on_workflow_start:
    - resolve main_directory
    - resolve memory_base

  on_worktree_create:
    - resolve worktree_directory
    - store in workflow.yaml

  on_stage_start:
    - resolve current_directory (may be worktree)
    - resolve memory_path (always main)
```

## 相對路徑 vs 絕對路徑

### 使用規則

```yaml
path_types:
  absolute:
    use_for:
      - workflow.yaml 中的路徑記錄
      - 跨目錄操作
      - Memory 寫入

  relative:
    use_for:
      - 報告中的程式碼引用
      - diff 輸出
      - 使用者展示

    base:
      in_worktree: worktree_root
      in_main: project_root
```

### 路徑轉換

```yaml
path_conversion:
  to_relative:
    description: "絕對路徑 → 相對路徑"
    logic: |
      if path.startswith(worktree_path):
          return path.replace(worktree_path, "")
      elif path.startswith(main_path):
          return path.replace(main_path, "")

  to_absolute:
    description: "相對路徑 → 絕對路徑"
    logic: |
      if is_memory_path(path):
          return f"{main_directory}/{path}"
      else:
          return f"{current_directory}/{path}"
```

## Git 操作路徑

### Diff 命令

```yaml
git_diff_paths:
  in_worktree:
    # 比較 worktree 分支與 main
    command: "git diff main..HEAD"

    # 或使用完整路徑
    command: "git -C {worktree_path} diff main..HEAD"

  in_main:
    # 比較 feature 分支與 main
    command: "git diff main..feature/{id}"
```

### 提交操作

```yaml
git_commit_paths:
  in_worktree:
    # 所有操作在 worktree 目錄中執行
    working_dir: "{worktree_path}"

    commands:
      stage: "git add {files}"
      commit: "git commit -m '{message}'"
      push: "git push -u origin feature/{id}"
```

## 錯誤處理

### 常見路徑錯誤

```yaml
path_errors:
  memory_in_worktree:
    error: "嘗試在 worktree 中寫入 Memory"
    cause: "未正確解析 Memory 路徑"
    fix: "使用 get_memory_path() 獲取正確路徑"

  relative_path_confusion:
    error: "相對路徑在不同目錄中解析不一致"
    cause: "未考慮 worktree 環境"
    fix: "使用絕對路徑或明確指定 base"

  missing_worktree:
    error: "Worktree 目錄不存在"
    cause: "Worktree 已被刪除或未創建"
    fix: "檢查 workflow.yaml 並重新創建 worktree"
```

### 驗證函數

```yaml
path_validation:
  validate_memory_path:
    checks:
      - path_exists
      - path_is_in_main_directory
      - path_is_writable

  validate_worktree_path:
    checks:
      - path_exists
      - is_git_worktree
      - branch_matches_expected
```

## 範例場景

### 場景 1：在 Worktree 中寫入 Memory

```yaml
scenario: "IMPLEMENT 階段在 worktree 中執行，需要寫入 Memory"

current_directory: "/project/.worktrees/user-auth"
main_directory: "/project"

memory_write:
  target_path: "{main_directory}/.claude/memory/implementations/user-auth/"
  resolved_to: "/project/.claude/memory/implementations/user-auth/"

  not: "/project/.worktrees/user-auth/.claude/memory/..."  # 錯誤！
```

### 場景 2：在 Worktree 中讀取程式碼

```yaml
scenario: "REVIEW 階段需要讀取 worktree 中的程式碼變更"

current_directory: "/project/.worktrees/user-auth"

code_read:
  source: "src/auth/login.ts"
  resolved_to: "/project/.worktrees/user-auth/src/auth/login.ts"

git_diff:
  command: "git diff main..HEAD -- src/"
  executed_in: "/project/.worktrees/user-auth"
```

### 場景 3：恢復工作流

```yaml
scenario: "從 main 目錄恢復之前的 worktree 工作流"

current_directory: "/project"
workflow_file: ".claude/memory/workflows/user-auth/workflow.yaml"

resume:
  1. read workflow.yaml
  2. get worktree_directory: "/project/.worktrees/user-auth"
  3. cd to worktree_directory
  4. continue workflow
```

## 相關資源

- [Worktree Setup](./worktree-setup.md)
- [Worktree Completion](./worktree-completion.md)
- [Memory System](../integration/memory-system.md)
