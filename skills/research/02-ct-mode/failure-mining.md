# Failure Mining

## 目標

把 CT 違規、低品質 claim、drift、未解矛盾轉成可重用的失敗模式。

## 分類

- `evidence`: 無來源、來源弱、推論當事實
- `drift`: topic drift、role drift、phase drift
- `conflict`: 矛盾未解、強行合併
- `experiment`: 假設不可測、缺少對照組
- `output`: 不符合 output contract

## 輸出格式

```markdown
# Failure Modes

| ID | Category | Trigger | Severity | Prevention | Regression Case |
|---|---|---|---|---|---|
```
