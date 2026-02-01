# Quick Start Guide

> 1 分鐘快速上手 Setup Workflow

## 最簡用法

```bash
/setup-workflow
```

這會：
1. 檢查現有配置狀態
2. 創建 Hook 腳本（自動 commit、測試驗證）
3. 更新 settings.local.json（權限、Hooks）
4. 創建 Memory 目錄結構

## 常用模式

### 完整設置

```bash
/setup-workflow
```

配置所有功能：Hooks、權限、Memory 結構。

### 僅檢查配置

```bash
/setup-workflow --check
```

顯示當前配置狀態，不做任何修改。

### 最小設置

```bash
/setup-workflow --minimal
```

僅設置權限預設，不啟用 Hooks。

## 配置完成後

```
✅ Workflow 設置完成！

配置項目：
  ✓ Hook 腳本：scripts/hooks/workflow_hooks.py
  ✓ 權限：12 個常用命令已允許
  ✓ Hooks：PostToolUse(Task), SubagentStop

功能說明：
  • Task 完成後自動 commit 並運行測試
  • Subagent 結束時檢測 memory 變更
  • 測試失敗會提示修復

相關命令：
  • /memory-commit - 手動 commit memory 變更
  • /orchestrate - 端到端工作流（會自動使用這些 hooks）
```

## 注意事項

- 會保留現有的 settings.local.json 配置
- Hook 腳本需要 Python 3.8+
- 如果專案沒有測試框架，驗證步驟會跳過

## 下一步

- 查看完整說明：[SKILL.md](../../SKILL.md)
