# Issue Classification Rules

> review skill 的問題分類規則

## 嚴重度分類

### CRITICAL（必須立即修正）

**定義**：會導致系統崩潰、安全漏洞或資料損失

**範例**：
- 安全漏洞（SQL Injection、XSS、CSRF）
- 資料洩露風險
- 生產環境崩潰
- 資料損壞
- 認證/授權繞過

**標記**：
```yaml
severity: critical
urgency: immediate
action: block_merge
```

### HIGH（應在此 PR 修正）

**定義**：嚴重影響功能或效能，但不會立即崩潰

**範例**：
- 功能邏輯錯誤
- 嚴重效能問題（10x 以上）
- 記憶體洩漏
- 競態條件
- 缺少關鍵錯誤處理

**標記**：
```yaml
severity: high
urgency: before_merge
action: strongly_suggest
```

### MEDIUM（建議修正）

**定義**：影響程式碼品質或可維護性

**範例**：
- 程式碼重複
- 過度複雜
- 缺少測試
- 文檔不完整
- 命名不清晰

**標記**：
```yaml
severity: medium
urgency: soon
action: suggest
```

### LOW（可延後）

**定義**：小問題或優化建議

**範例**：
- 風格不一致
- 微小效能優化
- 額外的程式碼整理
- 過度詳細的註解
- 非關鍵的重構

**標記**：
```yaml
severity: low
urgency: future
action: note
```

## 問題分類矩陣

```
                    嚴重度
              高 ←─────────→ 低
         ┌──────────┬──────────┐
    急   │ CRITICAL │   HIGH   │
    迫   │ 🚨 阻擋  │ ⚠️ 修正  │
    度   ├──────────┼──────────┤
         │  MEDIUM  │   LOW    │
    低   │ 📝 建議  │ 💡 未來  │
         └──────────┴──────────┘
```

## 自動分類規則

### 安全相關 → CRITICAL

```yaml
patterns:
  - "sql.*injection"
  - "xss"
  - "csrf"
  - "password.*plain"
  - "secret.*hardcoded"
  - "api.*key.*exposed"
```

### 效能相關 → HIGH/MEDIUM

```yaml
patterns:
  - "O(n²)" → HIGH
  - "memory.*leak" → HIGH
  - "n+1.*query" → MEDIUM
  - "unnecessary.*loop" → MEDIUM
```

### 測試相關 → MEDIUM

```yaml
patterns:
  - "no.*test"
  - "missing.*coverage"
  - "mock.*incorrect"
```

### 風格相關 → LOW

```yaml
patterns:
  - "naming.*convention"
  - "formatting"
  - "comment.*style"
```

## 問題去重規則

當多個視角報告相同問題時：

### 去重策略

```yaml
deduplication:
  strategy: "merge"
  rules:
    - same_file_line: true
    - similar_description: 0.8  # 80% 相似度
    - prefer_higher_severity: true
```

### 合併規則

```
視角 A: line 42 - "缺少輸入驗證" (MEDIUM)
視角 B: line 42 - "SQL 注入風險" (CRITICAL)
→ 合併為: line 42 - "SQL 注入風險（缺少輸入驗證）" (CRITICAL)
```

## 優先排序規則

### 排序因素

1. **嚴重度**：CRITICAL > HIGH > MEDIUM > LOW
2. **檔案重要性**：核心模組 > 一般模組
3. **修復複雜度**：簡單 > 複雜
4. **依賴數量**：被依賴多 > 被依賴少

### 排序公式

```
priority_score =
    severity_weight * 10 +
    file_importance * 5 +
    (10 - fix_complexity) +
    dependency_count
```

## 報告分組

### blockers.md

```markdown
# Blockers（必須修正）

以下問題必須在合併前修正：

## CRITICAL

### [C01] 安全漏洞 - SQL 注入

- **位置**：src/auth/login.ts:42
- **描述**：用戶輸入未經驗證直接拼接 SQL
- **發現者**：code-quality, integration
- **建議**：使用參數化查詢
```

### suggestions.md

```markdown
# Suggestions（建議修正）

以下問題建議在此 PR 或近期修正：

## HIGH

### [H01] 效能問題 - N+1 查詢

- **位置**：src/users/list.ts:28
- **描述**：迴圈內執行資料庫查詢
- **發現者**：code-quality
- **建議**：批次查詢或預載入
```

### future.md

```markdown
# Future（未來改進）

以下問題可在未來迭代中處理：

## LOW

### [L01] 程式碼風格 - 變數命名

- **位置**：src/utils/helper.ts:15
- **描述**：變數 'x' 命名不清晰
- **發現者**：documentation
- **建議**：改為描述性名稱
```

## 共用模組參考

- 交叉驗證：[shared/synthesis/cross-validation.md](../_shared/synthesis/cross-validation.md)
- 矛盾解決：[shared/synthesis/conflict-resolution.md](../_shared/synthesis/conflict-resolution.md)
