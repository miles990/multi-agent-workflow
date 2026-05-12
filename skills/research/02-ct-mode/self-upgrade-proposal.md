# Self-Upgrade Proposal

## 目標

把 CT retrospective 找到的問題轉成可審查、可測試、可回滾的改善提案。

## 產生條件

符合任一條件就產生：

- `mode_was_correct: false`
- 有 high / blocker workflow failure
- required artifact 缺失
- quality gate false positive / false negative
- action log 或 status 工具無法解析 workflow output
- 使用者修正指出 CT mode 或 gate 判斷錯誤

## 輸出

寫入：

```text
.claude/memory/research/{topic-id}/self-upgrade-proposal.md
```

格式：

```markdown
# Self-Upgrade Proposal

## Problem

## Evidence

## Proposed Change

## Target Files

## Risk Level

## Automation Level

## Verification Plan

## Rollback Plan

## Decision
- status: proposed
- requires_human_approval:
```

## 安全規則

- 不得用 proposal 當作已實作。
- 不得靜默降低 quality gate。
- runtime 行為變更必須附最小重現與驗證命令。
- L5 架構變更只能提出，不得自動套用。

