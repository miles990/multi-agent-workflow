# Worktree Setup（共用模組）

> Git Worktree 的創建與初始化規範

## 概述

在 IMPLEMENT 階段開始前創建隔離的 Git Worktree，確保 main 分支始終穩定。

**此為共用模組**，定義 Worktree 創建的標準流程。

## 創建流程

```
┌─────────────────────────────────────────────────────────────┐
│                    CP0.5: Worktree Setup                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Step 1: 目錄選擇                                            │
│  ┌──────────────────────────────────────┐                   │
│  │ 檢查 .gitignore 是否包含 worktree 目錄 │                   │
│  │ 選擇：.worktrees/ > worktrees/ > 詢問  │                   │
│  └──────────────────────────────────────┘                   │
│      ↓                                                       │
│  Step 2: 創建 Worktree                                       │
│  ┌──────────────────────────────────────┐                   │
│  │ git worktree add {dir}/{id} -b feature/{id}              │
│  │ 記錄 worktree 路徑到 workflow.yaml   │                   │
│  └──────────────────────────────────────┘                   │
│      ↓                                                       │
│  Step 3: 專案初始化                                          │
│  ┌──────────────────────────────────────┐                   │
│  │ 自動檢測專案類型                      │                   │
│  │ 執行 setup 命令（npm install 等）     │                   │
│  └──────────────────────────────────────┘                   │
│      ↓                                                       │
│  Step 4: 基線驗證                                            │
│  ┌──────────────────────────────────────┐                   │
│  │ 執行測試，確保基線通過                │                   │
│  │ 失敗則中止並報告                      │                   │
│  └──────────────────────────────────────┘                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 目錄選擇邏輯

### 優先順序

```yaml
directory_selection:
  priority:
    1: ".worktrees/"    # 首選（隱藏目錄）
    2: "worktrees/"     # 備選
    3: ask_user         # 如果都不適用

  validation:
    - check_gitignore   # 確認已被忽略
    - check_writable    # 確認可寫入
    - check_space       # 確認有足夠空間
```

### .gitignore 驗證

```yaml
gitignore_check:
  required_entries:
    - ".worktrees/"
    - "worktrees/"      # 如果使用

  on_missing:
    action: prompt_user
    message: |
      ⚠️ Worktree 目錄未被 .gitignore 忽略

      建議添加以下內容到 .gitignore：
      ```
      .worktrees/
      ```

      選項：
      1. 自動添加到 .gitignore
      2. 手動處理後繼續
      3. 取消
```

## 專案類型檢測

### 自動檢測

```yaml
project_detection:
  rules:
    - file: "package.json"
      type: "nodejs"
      setup: "npm install"
      test: "npm test"

    - file: "Cargo.toml"
      type: "rust"
      setup: "cargo build"
      test: "cargo test"

    - file: "go.mod"
      type: "golang"
      setup: "go mod download"
      test: "go test ./..."

    - file: "pyproject.toml"
      type: "python"
      setup: "pip install -e ."
      test: "pytest"

    - file: "requirements.txt"
      type: "python-legacy"
      setup: "pip install -r requirements.txt"
      test: "pytest"

    - file: "pom.xml"
      type: "java-maven"
      setup: "mvn install -DskipTests"
      test: "mvn test"

    - file: "build.gradle"
      type: "java-gradle"
      setup: "./gradlew build -x test"
      test: "./gradlew test"

  fallback:
    type: "unknown"
    setup: null
    test: null
    action: warn_user
```

### Setup 執行

```yaml
setup_execution:
  steps:
    1. detect_project_type
    2. run_setup_command:
        timeout: 300s  # 5 分鐘
        on_fail: abort_with_error

    3. verify_setup:
        check: "build artifacts exist"
        on_fail: warn_and_continue
```

## 基線驗證

### 測試執行

```yaml
baseline_verification:
  description: "確保 worktree 基線狀態正常"

  steps:
    1. run_tests:
        command: "{project_type.test}"
        timeout: 600s  # 10 分鐘

    2. check_results:
        if_pass: continue_workflow
        if_fail: abort_and_report

  on_failure:
    action: abort
    message: |
      ❌ 基線測試失敗

      無法在不穩定的基礎上開始實作。
      請先修復 main 分支的測試。

      失敗的測試：
      {failed_tests}

      建議：
      1. 切回 main 分支修復測試
      2. 使用 --skip-baseline 跳過（不建議）
```

### 跳過基線（不建議）

```yaml
skip_baseline:
  flag: "--skip-baseline"
  warning: |
    ⚠️ 跳過基線驗證可能導致：
    - 無法區分新引入的問題和既有問題
    - 浪費時間調試非相關問題

    確定要跳過嗎？[y/N]
```

## 完整 Worktree 創建命令

```bash
# Step 1: 創建 worktree
git worktree add .worktrees/{feature-id} -b feature/{feature-id}

# Step 2: 進入 worktree
cd .worktrees/{feature-id}

# Step 3: 執行專案 setup（以 Node.js 為例）
npm install

# Step 4: 驗證基線
npm test
```

## workflow.yaml 更新

```yaml
# 創建 worktree 後更新 workflow.yaml
workflow:
  id: "{feature-id}"
  # ... existing fields ...

  worktree:
    enabled: true
    directory: ".worktrees/{feature-id}"
    branch: "feature/{feature-id}"
    main_directory: "{main_project_path}"
    created_at: "{timestamp}"
    state: "active"
    baseline_verified: true
    project_type: "{detected_type}"
```

## 錯誤處理

| 錯誤 | 處理 |
|------|------|
| Worktree 已存在 | 提示選項：恢復/刪除/重命名 |
| 分支已存在 | 提示選項：使用現有/重命名/刪除後重建 |
| 空間不足 | 報告所需空間，中止 |
| 權限不足 | 報告錯誤，中止 |
| Setup 失敗 | 報告錯誤，中止 |
| 基線測試失敗 | 報告失敗測試，中止（除非 --skip-baseline）|

## 邊界情況

### 巢狀 Worktree

```yaml
nested_worktree:
  check: "current directory is inside a worktree"

  detection:
    command: "git rev-parse --git-common-dir"
    if_contains: ".git/worktrees"
      action: abort
      message: |
        ❌ 禁止在 Worktree 內創建巢狀 Worktree

        當前位置：{current_path}
        所屬 Worktree：{parent_worktree}

        請先返回主專案目錄執行。
```

### 恢復中斷的創建

```yaml
interrupted_setup:
  detection:
    - worktree 目錄存在
    - state != "active"
    - 或 setup 未完成

  options:
    1: "繼續 setup"
    2: "刪除重建"
    3: "取消"
```

## Flags

```bash
# Worktree 控制
--worktree              # 強制使用 worktree（預設：自動判斷）
--no-worktree           # 禁用 worktree，直接在 main 工作
--worktree-dir PATH     # 自訂 worktree 目錄

# Setup 控制
--skip-baseline         # 跳過基線測試（不建議）
--setup-command CMD     # 自訂 setup 命令
--test-command CMD      # 自訂測試命令
```

## 相關資源

- [Worktree Completion](./worktree-completion.md)
- [Path Resolution](./path-resolution.md)
- [Evolve Checkpoints](../integration/evolve-checkpoints.md)
