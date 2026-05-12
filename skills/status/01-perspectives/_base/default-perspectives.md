# Status 視角定義

本 Skill 為工具型 Skill，不使用多視角分析模式。

## 說明

`status` 是一個狀態查看工具，用於顯示工作流執行進度與統計。

由於這是一個查詢操作而非研究分析任務，因此不需要多視角協作。

## 狀態圖示

| 圖示 | 狀態 | 說明 |
|------|------|------|
| ⏳ | pending | 等待執行 |
| 🔄 | running | 執行中 |
| ✅ | completed | 成功完成 |
| ❌ | failed | 執行失敗 |
| ⏭️ | skipped | 已跳過 |

## 相關資源

- [SKILL.md](../../SKILL.md) - 完整的 Skill 定義
- [usage.md](../../00-quickstart/_base/usage.md) - 快速上手指南
- [workflow-status.py](../../_shared/tools/workflow-status.py) - CLI 核心工具
