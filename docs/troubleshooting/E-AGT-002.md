# E-AGT-002: Agent 格式錯誤

## 錯誤資訊

| 欄位 | 值 |
|------|-----|
| 錯誤碼 | E-AGT-002 |
| 名稱 | Agent 格式錯誤 |
| 嚴重度 | MEDIUM |
| 類別 | Agent 執行 |

## 說明

當 Agent（視角）的輸出格式不符合預期結構時，會觸發此錯誤。系統需要特定格式的輸出才能正確處理和整合各視角的結果。

## 常見場景

### 場景 1：缺少必要欄位

**狀況**：Agent 輸出缺少必要的結構欄位。

**原因**：
- Agent 提示詞未明確要求格式
- Agent 理解偏差
- 輸出被截斷

**解決方案**：
1. 系統會自動重試
2. 檢查輸出是否被截斷
3. 使用 `--debug` 查看原始輸出

### 場景 2：YAML/JSON 解析失敗

**狀況**：輸出的結構化資料無法解析。

**原因**：
- 格式語法錯誤
- 特殊字元未轉義
- 縮排不正確

**解決方案**：
1. 系統會自動重試
2. 檢查輸出中的特殊字元
3. 驗證 YAML/JSON 語法

### 場景 3：輸出內容為空

**狀況**：Agent 產生了空的輸出。

**原因**：
- Agent 未能完成任務
- 輸出被過濾
- 連線問題

**解決方案**：
1. 重試執行
2. 檢查連線狀態
3. 使用 `--debug` 模式診斷

## 快速修復

### 方法 1：自動重試

系統預設會自動重試，通常可以解決暫時性問題。

### 方法 2：手動重試

```bash
/multi-orchestrate --resume {workflow-id}
```

### 方法 3：Debug 模式

查看詳細的輸入輸出：

```bash
/multi-orchestrate --debug --resume {workflow-id}
```

### 方法 4：跳過問題視角

如果特定視角持續出錯：

```bash
/multi-orchestrate --skip-perspective {perspective-id} "任務描述"
```

## 深入分析

### 預期輸出格式

各視角需要產生符合以下結構的輸出：

```yaml
# 研究視角輸出
perspective_id: architecture
status: completed
findings:
  - title: "發現標題"
    description: "詳細說明"
    evidence: "支持證據"
recommendations:
  - "建議 1"
  - "建議 2"
```

```yaml
# 審查視角輸出
perspective_id: code-quality
status: completed
issues:
  - id: "ISSUE-001"
    severity: "HIGH"
    category: "security"
    description: "問題說明"
    file_path: "src/auth.ts"
    line: 42
    suggestion: "修復建議"
```

### 驗證規則

| 檢查項 | 說明 | 必要性 |
|--------|------|--------|
| perspective_id | 視角識別碼 | 必要 |
| status | 執行狀態 | 必要 |
| findings/issues | 發現或問題列表 | 依視角 |
| recommendations | 建議列表 | 選用 |

### 常見解析錯誤

```
解析錯誤：缺少必要欄位 'perspective_id'
解析錯誤：'issues' 應為陣列，但收到字串
解析錯誤：YAML 語法錯誤 at line 15
解析錯誤：JSON 格式無效
```

## 預防措施

### 1. 明確的提示詞

確保 Agent 提示詞包含清晰的輸出格式要求。

### 2. 輸出驗證

系統會自動驗證輸出格式，並在失敗時重試。

### 3. 格式範例

提供輸出格式的具體範例給 Agent 參考。

### 4. 錯誤處理

系統對格式錯誤有容錯機制，會嘗試修復常見問題。

## 相關錯誤

- [E-AGT-001](./E-AGT-001.md) - Agent 超時
- [E-AGT-006](./E-AGT-006.md) - Agent 輸出為空

## 參考資料

- [錯誤碼定義](../../shared/errors/error-codes.md)
- [視角基礎結構](../../shared/perspectives/base-perspective.md)
