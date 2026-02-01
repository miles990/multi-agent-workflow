# Quick Start Guide

> 1 分鐘快速上手 Memory Commit

## 最簡用法

```bash
/memory-commit
```

這會：
1. 掃描 `.claude/memory/` 目錄的變更
2. 按目錄分類變更（research, plans, tasks 等）
3. 自動生成符合規範的 commit message
4. 按優先順序執行 commit

## 常用模式

### 預覽模式

```bash
/memory-commit --dry
```

僅顯示會 commit 的內容，不實際執行。

### 完整 commit

```bash
/memory-commit
```

自動分析並 commit 所有 memory 變更。

## 輸出範例

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
- 按目錄優先順序 commit（research → plans → implement → review → tasks）

## 下一步

- 查看完整說明：[SKILL.md](../../SKILL.md)
