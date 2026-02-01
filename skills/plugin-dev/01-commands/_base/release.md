# /plugin-dev release

> 完整的發布自動化

## 格式

```bash
/plugin-dev release [LEVEL] [--dry-run] [--resume] [--yes] [--skip-tests]
```

## 參數

| 參數 | 說明 |
|------|------|
| `LEVEL` | 版本級別 patch/minor/major（預設 patch） |
| `--dry-run` | 預覽完整發布流程 |
| `--resume` | 從中斷點恢復 |
| `--yes, -y` | 跳過確認提示 |
| `--skip-tests` | 跳過測試步驟 |

## 實作路徑

```
Skill → Bash: python -m cli.plugin.release release [LEVEL] [options]
     → ReleaseCommands.release()
     → ReleaseProgress
```

## 發布流程

```
[1/9] VALIDATE      驗證 Plugin 結構
[2/9] TEST          執行測試套件
[3/9] CHECK_GIT     檢查 Git 狀態
[4/9] BUMP          升級版本號
[5/9] CHANGELOG     生成變更日誌
[6/9] COMMIT        Git commit
[7/9] TAG           建立 Git tag
[8/9] PUSH          推送到遠端
[9/9] COMPLETE      完成
```

## 範例

### 發布 patch 版本

```bash
/plugin-dev release patch
```

輸出：
```
🚀 發布 v2.4.1 (patch)

  [1/9] ✓ 驗證結構              完成
  [2/9] ✓ 執行測試              73/73 通過
  [3/9] ✓ 檢查 Git 狀態         無未提交變更
  [4/9] ✓ 升級版本              2.4.0 → 2.4.1
  [5/9] ✓ 生成變更日誌          3 個變更
  [6/9] ✓ Git commit            chore(release): v2.4.1
  [7/9] ✓ Git tag               v2.4.1
  [8/9] ✓ Git push              已推送到 origin
  [9/9] ✓ 完成

🎉 發布成功: v2.4.1
```

### 預覽發布

```bash
/plugin-dev release minor --dry-run
```

輸出：
```
預覽發布 v2.5.0 (minor)

將執行以下步驟:
  1. 驗證 Plugin 結構
  2. 執行測試套件
  3. 檢查 Git 狀態
  4. 升級版本: 2.4.0 → 2.5.0
  5. 生成變更日誌
  6. Git commit
  7. Git tag: v2.5.0
  8. Git push

確認執行? 使用 /plugin-dev release minor 開始
```

### 從中斷點恢復

```bash
/plugin-dev release --resume
```

輸出：
```
🔄 恢復發布 v2.4.1

上次進度:
  ✓ 步驟 1-5 已完成
  ✗ 步驟 6 失敗: Git commit

從步驟 6 繼續...

  [6/9] ✓ Git commit            chore(release): v2.4.1
  [7/9] ✓ Git tag               v2.4.1
  [8/9] ✓ Git push              已推送到 origin
  [9/9] ✓ 完成

🎉 發布成功: v2.4.1
```

## 進度持久化

發布進度保存在 `.plugin-dev/release-progress.json`：

```json
{
  "workflow_id": "release_20260201_143000",
  "current_step": "CHANGELOG",
  "completed_steps": ["VALIDATE", "TEST", "CHECK_GIT", "BUMP"],
  "failed_step": null,
  "error": null,
  "new_version": "2.4.1",
  "started_at": "2026-02-01T14:30:00"
}
```

## 錯誤處理

### 有未提交的變更

```
✗ 發布失敗

錯誤: Git 有未提交的變更

未提交:
  M cli/plugin/dev.py
  ? .plugin-dev/temp.json

修復建議:
  1. 提交變更: git add -A && git commit -m "..."
  2. 或暫存: git stash
  3. 然後重新執行發布
```

### 測試失敗

```
✗ 發布失敗

錯誤: 3 個測試失敗

失敗的測試:
  ✗ test_sync_basic
  ✗ test_validate_strict
  ✗ test_release_patch

修復建議:
  1. 執行 pytest tests/plugin/ 查看詳情
  2. 修復測試後重新發布
  3. 或使用 --skip-tests 跳過（不建議）
```

### 發布中斷

```
✗ 發布在步驟 5 失敗

錯誤: 生成變更日誌失敗

已保存進度:
  ✓ 步驟 1-4 已完成
  • 版本已升級到 2.4.1
  • plugin.json 已更新

恢復選項:
  1. 重試: /plugin-dev release --resume
  2. 回滾: git checkout plugin.json marketplace.json
```

## 回滾

如果發布後發現問題：

```bash
# 回滾到上一個版本
git revert HEAD
git push origin main
git push origin :refs/tags/v2.4.1
```

## 相關命令

- `/plugin-dev validate` - 預先驗證
- `/plugin-dev version` - 版本管理
- `/plugin-dev status` - 查看狀態
