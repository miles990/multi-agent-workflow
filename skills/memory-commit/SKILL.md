---
name: memory-commit
version: 1.0.0
description: 智能 commit .claude/memory/ 目錄的變更（含任務追蹤）
triggers: [memory-commit, mc]
allowed-tools: [Bash, Glob, Grep, Read]
---

# Memory Commit

掃描並 commit `.claude/memory/` 目錄的變更，包含任務狀態追蹤。

## 使用方式

```bash
/memory-commit         # 自動分析並 commit 所有 memory 變更
/memory-commit --dry   # 僅顯示會 commit 的內容，不執行
```

## Memory 目錄結構

```
.claude/memory/
├── tasks/           # 任務追蹤
│   ├── current.json      # 當前工作流狀態
│   ├── history/          # 歷史記錄
│   └── dag/              # 任務依賴圖
├── research/        # 研究報告
├── plans/           # 實作計劃
├── implement/       # 實作記錄
├── review/          # 審查報告
└── workflows/       # 工作流輸出
```

## Commit Message 格式

| 目錄 | Commit Type | 範例 |
|------|-------------|------|
| tasks/ | chore(tasks) | chore(tasks): complete phase 1 implementation |
| research/ | docs(research) | docs(research): user authentication analysis |
| plans/ | feat(plans) | feat(plans): todo system implementation plan |
| implement/ | feat(implement) | feat(implement): phase 1 memory integration |
| review/ | docs(review) | docs(review): code review findings |
| workflows/ | chore(workflow) | chore(workflow): update orchestrate output |

## 執行步驟

### 1. 檢查變更

```bash
# 顯示 memory 目錄變更
git status --porcelain .claude/memory/
```

### 2. 分類變更

分析變更檔案，按目錄分類：

| 優先順序 | 目錄 | 說明 |
|---------|------|------|
| 1 | research/ | 研究結果先 commit |
| 2 | plans/ | 計劃依賴研究 |
| 3 | implement/ | 實作記錄 |
| 4 | review/ | 審查報告 |
| 5 | workflows/ | 工作流輸出 |
| 6 | tasks/ | 任務狀態最後（可能引用其他 commit） |

### 3. 生成 Commit Message

每個分類：
1. 讀取變更檔案內容
2. 摘要主要變更（標題、狀態變化等）
3. 生成符合格式的 commit message

### 4. 執行 Commit

```bash
# 按順序 commit
git add .claude/memory/research/
git commit -m "docs(research): <摘要>

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

git add .claude/memory/plans/
git commit -m "feat(plans): <摘要>

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

# ... 其他目錄
```

## 範例輸出

```
📝 Memory Commit

掃描 .claude/memory/ 變更...

變更統計：
  research/  2 files changed
  plans/     1 file changed
  tasks/     3 files changed

執行 commit：
  [1/3] docs(research): add authentication flow analysis ✓
  [2/3] feat(plans): todo system implementation plan ✓
  [3/3] chore(tasks): update workflow status ✓

完成！3 個 commits 已建立。
```

## 注意事項

- 只處理 `.claude/memory/` 下的變更
- 不會影響其他目錄的 staged changes
- 如果某個分類沒有變更，跳過該分類
- 使用 `--dry` 可預覽但不執行
