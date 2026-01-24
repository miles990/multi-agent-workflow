# E-GIT-001: Worktree 建立失敗

## 錯誤資訊

| 欄位 | 值 |
|------|-----|
| 錯誤碼 | E-GIT-001 |
| 名稱 | Worktree 建立失敗 |
| 嚴重度 | HIGH |
| 類別 | Git 操作 |

## 說明

當系統無法建立 Git Worktree 用於隔離開發時，會觸發此錯誤。Worktree 用於在不影響 main 分支的情況下執行 IMPLEMENT/REVIEW/VERIFY 階段。

## 常見場景

### 場景 1：分支已存在

**狀況**：嘗試建立的分支名稱已存在。

**原因**：
- 之前的工作流未清理
- 手動建立了同名分支
- 分支命名衝突

**解決方案**：
1. 刪除現有分支：`git branch -D feature/{id}`
2. 使用不同的工作流 ID
3. 清理孤立 worktrees

### 場景 2：路徑已被佔用

**狀況**：Worktree 目標路徑已存在。

**原因**：
- 之前的 worktree 未清理
- 目錄已被其他用途使用

**解決方案**：
1. 刪除現有目錄
2. 使用 `--worktree-dir` 指定其他路徑
3. 清理孤立 worktrees

### 場景 3：Git 狀態問題

**狀況**：Git 倉庫狀態不允許建立 worktree。

**原因**：
- 不是 Git 倉庫
- Git 倉庫損壞
- 有未提交的變更

**解決方案**：
1. 確認在 Git 倉庫中執行
2. 提交或暫存變更
3. 修復 Git 倉庫

## 快速修復

### 方法 1：清理孤立 Worktrees

```bash
# 列出所有 worktrees
git worktree list

# 清理孤立的 worktrees
git worktree prune

# 或使用內建指令
/multi-orchestrate --cleanup-worktrees
```

### 方法 2：手動刪除

```bash
# 刪除 worktree 目錄
rm -rf .worktrees/{workflow-id}

# 刪除對應分支
git branch -D feature/{workflow-id}
```

### 方法 3：禁用 Worktree

如果不需要隔離，可以直接在 main 工作：

```bash
/multi-orchestrate --no-worktree "任務描述"
```

### 方法 4：指定其他路徑

```bash
/multi-orchestrate --worktree-dir /tmp/worktrees "任務描述"
```

## 深入分析

### 診斷步驟

1. **檢查 Git 狀態**

   ```bash
   git status
   git worktree list
   ```

2. **檢查目標路徑**

   ```bash
   ls -la .worktrees/
   ```

3. **檢查分支列表**

   ```bash
   git branch -a | grep feature/
   ```

4. **檢查 Git 配置**

   ```bash
   git config --list | grep worktree
   ```

### Worktree 生命週期

```
PLAN 完成
    ↓
建立 Worktree (CP0.5)
    ↓
IMPLEMENT/REVIEW/VERIFY 在 worktree 中執行
    ↓
VERIFY 完成
    ↓
┌─────────────────────────┐
│ SHIP IT → 合併 + 清理   │
│ BLOCKED → 保留 worktree │
└─────────────────────────┘
```

### 清理策略

| 情況 | 處理方式 |
|------|----------|
| SHIP IT | 自動合併到 main，清理 worktree |
| BLOCKED | 保留 worktree 供後續迭代 |
| --abandon | 清理 worktree，可選保留 patch |

## 預防措施

### 1. 定期清理

定期執行清理：

```bash
# 加入到定期維護腳本
git worktree prune
rm -rf .worktrees/*
git branch | grep feature/ | xargs git branch -D
```

### 2. 使用唯一 ID

確保工作流 ID 唯一：

```bash
# 系統會自動生成唯一 ID，格式：
# {timestamp}-{task-slug}
# 例如：20260124-user-auth
```

### 3. 檢查空間

確保有足夠空間建立 worktree：

```bash
df -h .
```

### 4. 乾淨的工作區

建立 worktree 前確保工作區乾淨：

```bash
git status --porcelain
```

## 相關錯誤

- [E-GIT-002](./E-GIT-002.md) - 分支衝突
- [E-GIT-005](./E-GIT-005.md) - Worktree 清理失敗
- [E-GIT-006](./E-GIT-006.md) - 非 Git 倉庫

## 參考資料

- [錯誤碼定義](../../shared/errors/error-codes.md)
- [Git Worktree 隔離](../../skills/orchestrate/04-git-worktree/)
- [Git Worktree 官方文檔](https://git-scm.com/docs/git-worktree)
