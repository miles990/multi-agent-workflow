# Quick Start Guide

> 3 分鐘快速上手 Multi-Agent Review

## 最簡用法

```bash
/multi-review src/auth/
```

這會：
1. 啟動 4 個並行審查 Agent
2. 從不同視角分析程式碼
3. 識別並分類問題
4. 產出審查報告
5. 自動存檔到 Memory

## 常用模式

### 審查暫存區變更

```bash
/multi-review --staged
```

適用：提交前審查

### 審查分支差異

```bash
/multi-review --branch feature-auth
```

適用：PR 前審查

### 快速審查（2 視角）

```bash
/multi-review --quick src/
```

適用：時間有限、快速檢查

### 深度審查（6 視角）

```bash
/multi-review --deep src/core/
```

適用：核心程式碼、安全敏感區

## 輸出位置

所有審查結果存儲在：

```
.claude/memory/reviews/[review-id]/
├── review-summary.md   ← 主報告（先看這個）
├── issues/
│   ├── blockers.md     ← 必須修正
│   ├── suggestions.md  ← 建議修正
│   └── future.md       ← 未來改進
├── overview.md         ← 一頁摘要
└── perspectives/       ← 各視角詳細報告
```

## 問題嚴重度

| 等級 | 意義 | 行動 |
|------|------|------|
| 🚨 CRITICAL | 嚴重問題 | 必須立即修正 |
| ⚠️ HIGH | 重要問題 | 應在此 PR 修正 |
| 📝 MEDIUM | 建議改進 | 建議修正 |
| 💡 LOW | 小建議 | 可延後 |

## 進階技巧

### 過濾嚴重度

```bash
/multi-review --severity high src/
```

只顯示 HIGH 及以上問題

### 指定視角數量

```bash
/multi-review --perspectives 3 src/
```

### 不存檔

```bash
/multi-review --no-memory src/
```

### 與 evolve 整合

審查結果會自動與 evolve Checkpoint 同步：
- CP1: 搜尋相關 Memory
- CP3: 審查共識達成
- CP3.5: 審查完成後更新 index.md

## 審查後行動

### 有 BLOCKER

```
🚨 發現 1 個 BLOCKER

建議：
1. 先修正 BLOCKER 問題
2. 重新執行 /multi-review
3. 確認無 BLOCKER 後繼續
```

### 無 BLOCKER

```
✅ 無 BLOCKER 問題

可選擇：
1. 修正 HIGH/MEDIUM 問題
2. 或直接進入 /multi-verify
```

## 下一步

- [了解預設視角](../../01-perspectives/_base/default-perspectives.md)
- [問題分類規則](../../config/issue-classification.md)
- [理解 Map-Reduce 流程](../../_shared/coordination/map-phase.md)
