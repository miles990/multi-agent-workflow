# E-WKF-001: 回退超限

## 錯誤資訊

| 欄位 | 值 |
|------|-----|
| 錯誤碼 | E-WKF-001 |
| 名稱 | 回退超限 |
| 嚴重度 | CRITICAL |
| 類別 | Workflow 流程 |

## 說明

當工作流的回退次數超過上限（預設 3 次）時，系統會觸發此錯誤並暫停執行。這表示連續的審查（REVIEW）或驗證（VERIFY）失敗導致工作流無法完成。

## 常見場景

### 場景 1：持續的安全問題

**狀況**：每次回退都是因為安全漏洞。

**原因**：
- 開發者不熟悉安全編碼實踐
- 缺少安全檢查清單
- 安全審查標準過於嚴格

**解決方案**：
1. 審查所有安全相關的 BLOCKER 問題
2. 使用安全編碼模板
3. 在 PLAN 階段加入安全考量

### 場景 2：測試持續失敗

**狀況**：驗證階段的測試反覆失敗。

**原因**：
- 需求理解有誤
- 測試案例設計不當
- 存在難以解決的技術限制

**解決方案**：
1. 重新審視原始需求
2. 與測試案例設計者討論
3. 考慮調整驗收標準

### 場景 3：程式碼品質問題

**狀況**：審查持續發現程式碼品質問題。

**原因**：
- 未遵循編碼規範
- 缺少程式碼審查經驗
- 時間壓力導致品質下降

**解決方案**：
1. 使用 linter 和格式化工具
2. 參考現有程式碼風格
3. 放慢開發速度，注重品質

## 快速修復

### 方法 1：手動修復後繼續

1. 審查失敗歷程中列出的所有問題
2. 手動修復關鍵問題
3. 使用 `--resume` 繼續執行：

```bash
/multi-orchestrate --resume {workflow-id}
```

### 方法 2：增加回退上限

如果問題需要更多迭代來解決：

```bash
/multi-orchestrate --max-rollbacks 5 --resume {workflow-id}
```

### 方法 3：從 PLAN 重新開始

如果問題根源在規劃階段：

```bash
/multi-orchestrate --start-at plan "任務描述"
```

### 方法 4：放棄並重新開始

如果需要完全重新開始：

```bash
/multi-orchestrate --abandon {workflow-id}
/multi-orchestrate "任務描述"
```

## 深入分析

### 診斷步驟

1. **審查失敗歷程**

   查看錯誤訊息中的「失敗歷程」部分：

   ```
   📋 失敗歷程
   • 迭代 1: BLOCKER - SQL 注入風險
   • 迭代 2: BLOCKER - XSS 漏洞
   • 迭代 3: HIGH - 測試覆蓋不足
   ```

2. **識別問題模式**

   - 是否都是同類型問題？
   - 是否集中在同一檔案/模組？
   - 是否有根本原因？

3. **檢查 Memory 記錄**

   ```bash
   cat .claude/memory/reviews/{feature-id}/issues/blockers.md
   cat .claude/memory/verifications/{feature-id}/failures.md
   ```

4. **分析根本原因**

   根據失敗模式判斷：
   - 需求問題 → 回到需求確認
   - 設計問題 → 回到 PLAN
   - 實作問題 → 專注修復特定問題
   - 審查標準問題 → 調整審查配置

### 預設配置

| 配置項 | 預設值 | 說明 |
|--------|--------|------|
| max_rollbacks | 3 | 最大回退次數 |
| rollback_target | IMPLEMENT | 回退目標階段 |
| on_exceed | pause | 超限時的行為 |

### 自訂配置

```yaml
# .claude/config/workflow.yaml
rollback:
  max_count: 5
  target_stage: "implement"
  on_exceed: "pause"  # pause | fail | ask
```

## 預防措施

### 1. 前置檢查

在 IMPLEMENT 之前確保：
- 需求清晰無歧義
- 設計方案經過評審
- 已識別所有技術風險

### 2. 增量式實作

- 小步快跑，頻繁驗證
- 每個功能點完成後立即審查
- 避免大批量變更

### 3. 使用檢查清單

建立各類型問題的檢查清單：
- 安全檢查清單
- 效能檢查清單
- 測試覆蓋檢查清單

### 4. 學習歷史問題

定期回顧過去的失敗原因，避免重複犯錯。

## 相關錯誤

- [E-WKF-007](./E-WKF-007.md) - 迭代超限
- [E-AGT-003](./E-AGT-003.md) - Agent 衝突

## 參考資料

- [錯誤碼定義](../../shared/errors/error-codes.md)
- [orchestrate SKILL](../../skills/orchestrate/SKILL.md)
