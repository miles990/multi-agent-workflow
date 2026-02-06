# Quick Start Guide

> 3 分鐘快速上手 Architecture Audit

## 最簡用法

```bash
/audit src/
```

這會：
1. 啟動 4 個並行審查 Agent
2. 從不同視角分析架構健康度
3. 識別依賴問題、模式不一致、測試缺口、文檔過時
4. 按嚴重度分類問題
5. 產出審查報告到 Memory

## 常用模式

### 審查特定模組

```bash
/audit src/api/
```

適用：聚焦某個子系統的架構審查

### 全面審查

```bash
/audit --full
```

適用：定期全面架構健康檢查

### 快速審查（2 視角）

```bash
/audit --quick src/
```

適用：時間有限、快速檢查依賴和模式一致性

### 深度審查（6 視角）

```bash
/audit --deep src/core/
```

適用：核心模組、含安全和效能分析

### 聚焦特定面向

```bash
/audit --focus deps src/          # 只看依賴
/audit --focus patterns src/      # 只看模式一致性
/audit --focus tests src/         # 只看測試覆蓋
/audit --focus docs src/          # 只看文檔同步
```

適用：已知問題面向，針對性審查

## 輸出位置

所有審查結果存儲在：

```
.claude/memory/audit/{audit-id}/
+-- audit-summary.md        <-- 主報告（先看這個）
+-- issues.yaml             <-- 問題清單（按嚴重度排序）
+-- perspectives/            <-- 各視角詳細報告
    +-- dependency-auditor.md
    +-- pattern-checker.md
    +-- coverage-auditor.md
    +-- doc-sync-checker.md
```

## 問題嚴重度

| 等級 | 意義 | 行動 |
|------|------|------|
| CRITICAL | 架構缺陷、系統風險 | 立即修復 |
| HIGH | 一致性違反、可維護性問題 | 限時修復 |
| MEDIUM | 品質改善建議 | 記錄追蹤 |
| LOW | 風格建議或小改進 | 可選 |

## 審查後行動

### 有 CRITICAL 問題

```
發現 CRITICAL 問題

建議：
1. 優先修復 CRITICAL 問題
2. 重新執行 /audit 驗證修復
3. 再處理 HIGH/MEDIUM 問題
```

### 無 CRITICAL 問題

```
無 CRITICAL 問題

可選擇：
1. 按優先級處理 HIGH/MEDIUM 問題
2. 使用 /multi-plan 規劃改善方案
3. 建立任務追蹤（/multi-tasks）
```

## 下一步

- [了解預設視角](../../01-perspectives/_base/default-perspectives.md)
- [視角詳細定義](../../../../shared/perspectives/catalog.yaml)
- [理解 Map-Reduce 流程](../../../../shared/coordination/map-phase.md)
