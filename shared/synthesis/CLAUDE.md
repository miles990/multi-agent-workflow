# 匯總模組（Synthesis）

> 交叉驗證與矛盾解決框架

## 自動載入

當引用 `@shared/synthesis` 時，自動應用：
- `cross-validation.md` - 交叉驗證邏輯
- `conflict-resolution.md` - 矛盾解決邏輯

## 交叉驗證流程

### Step 1: 提取發現

從每個視角報告提取關鍵發現，標準化格式：

```yaml
finding:
  id: F001
  source: perspective_id
  category: architecture | methodology | practice | risk
  statement: "發現描述"
  evidence: "支持證據"
  confidence: high | medium | low
```

### Step 2: 語義比對

識別相似或相關的發現：
- 主題相同 + 結論一致 → 可能共識
- 主題相同 + 結論相反 → 可能矛盾

### Step 3: 分類

| 類型 | 定義 | 信心度 |
|------|------|--------|
| 強共識 | 3-4 視角同意 | ★★★★ |
| 弱共識 | 2 視角同意 | ★★ |
| 矛盾 | 視角衝突 | 需解決 |
| 獨特洞察 | 單一視角發現 | 需評估 |

### Step 4: 信心評估

基於視角支持數和證據強度：
- 4/4 視角 + 強證據 → 非常高
- 3/4 視角 或 強證據 → 高
- 2/4 視角 或 中等證據 → 中
- 1/4 視角 或 弱證據 → 低

## 矛盾解決

1. 分析矛盾原因
2. 多輪比較分析
3. 產出解決方案或標記「需進一步處理」

## 輸出格式

```markdown
## 交叉驗證結果

### 強共識 (★★★★)
1. [F001, F005, F009] 描述...

### 弱共識 (★★)
1. [F002, F006] 描述...

### 矛盾
1. [F004 vs F010] 關於...的分歧

### 獨特洞察
1. [F013] (視角 C) 描述...
```

## 參考

- @shared/coordination/reduce-phase.md - Reduce 階段流程
- @shared/quality/completeness-checklist.yaml - 完整性檢查
