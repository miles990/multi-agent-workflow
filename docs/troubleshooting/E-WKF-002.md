# E-WKF-002: 階段缺失

## 錯誤資訊

| 欄位 | 值 |
|------|-----|
| 錯誤碼 | E-WKF-002 |
| 名稱 | 階段缺失 |
| 嚴重度 | HIGH |
| 類別 | Workflow 流程 |

## 說明

當工作流嘗試執行某階段但發現其前置階段未完成或輸出缺失時，會觸發此錯誤。

## 常見場景

### 場景 1：跳過必要階段

**狀況**：嘗試從 IMPLEMENT 開始，但沒有 PLAN 輸出。

**原因**：
- 使用 `--start-at` 跳過了前置階段
- PLAN 階段的輸出被刪除

**解決方案**：
1. 從正確的階段開始
2. 重新執行 PLAN 階段
3. 使用 `--from-plan` 指定已有的計劃

### 場景 2：Memory 檔案缺失

**狀況**：前置階段的 Memory 檔案不存在。

**原因**：
- Memory 檔案被手動刪除
- 儲存過程中斷
- 路徑錯誤

**解決方案**：
1. 檢查 Memory 目錄
2. 重新執行缺失的階段
3. 使用 `--no-memory` 跳過 Memory 檢查

### 場景 3：不完整的輸出

**狀況**：前置階段有輸出但內容不完整。

**原因**：
- 階段執行中斷
- 部分儲存失敗

**解決方案**：
1. 重新執行前置階段
2. 檢查輸出檔案完整性

## 快速修復

### 方法 1：從正確階段開始

```bash
# 確認需要的前置階段
/multi-orchestrate --dry-run --start-at implement "任務"

# 從頭開始
/multi-orchestrate "任務描述"
```

### 方法 2：使用已有的輸出

如果已有之前的計劃：

```bash
/multi-orchestrate --from-plan user-auth "任務描述"
```

或從研究開始：

```bash
/multi-orchestrate --from-research user-auth "任務描述"
```

### 方法 3：重新執行缺失階段

```bash
# 只執行 PLAN
/multi-orchestrate --stop-at plan "任務描述"

# 然後繼續
/multi-orchestrate --from-plan {plan-id} "任務描述"
```

## 深入分析

### 階段依賴關係

```
RESEARCH (選用)
    ↓
   PLAN (必要)
    ↓
IMPLEMENT (必要)
    ↓
  REVIEW (必要)
    ↓
  VERIFY (必要)
```

### 各階段必要輸入

| 階段 | 必要輸入 | 來源 |
|------|----------|------|
| RESEARCH | 任務描述 | 使用者 |
| PLAN | 任務描述 或 research 報告 | 使用者 / RESEARCH |
| IMPLEMENT | implementation-plan.md | PLAN |
| REVIEW | 程式碼變更 | IMPLEMENT |
| VERIFY | review-summary.md | REVIEW |

### 檢查輸入存在

```bash
# 檢查 PLAN 輸出
ls .claude/memory/plans/{feature-id}/implementation-plan.md

# 檢查 IMPLEMENT 輸出
ls .claude/memory/implementations/{feature-id}/implementation-log.md

# 檢查 REVIEW 輸出
ls .claude/memory/reviews/{feature-id}/review-summary.md
```

## 預防措施

### 1. 完整執行

儘量使用完整的工作流執行，讓系統自動管理階段順序：

```bash
/multi-orchestrate "任務描述"
```

### 2. 使用 dry-run

在執行前確認流程：

```bash
/multi-orchestrate --dry-run "任務描述"
```

### 3. 保護 Memory

不要手動刪除 Memory 檔案，除非確定不再需要。

### 4. 記錄工作流 ID

記錄正在進行的工作流 ID，方便後續恢復。

## 相關錯誤

- [E-WKF-003](./E-WKF-003.md) - 依賴缺失
- [E-WKF-004](./E-WKF-004.md) - 階段順序錯誤
- [E-MEM-001](./E-MEM-001.md) - Memory 讀取失敗

## 參考資料

- [錯誤碼定義](../../shared/errors/error-codes.md)
- [orchestrate SKILL](../../skills/orchestrate/SKILL.md)
- [階段判斷邏輯](../../skills/orchestrate/01-stage-detection/)
