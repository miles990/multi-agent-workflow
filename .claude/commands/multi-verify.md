執行多視角驗證測試。

## 流程

1. 載入 @skills/verify/SKILL.md
2. 載入 @shared/coordination/map-phase.md
3. 並行啟動 4 視角 Agent（functional-tester, edge-case-hunter, regression-checker, acceptance-validator）
4. 收集視角報告到 `.claude/memory/verify/{review-id}/perspectives/`
5. 執行 @shared/coordination/reduce-phase.md 匯總
6. 生成 `verify-summary.md`

## 視角配置

| ID | 名稱 | 模型 | 聚焦 |
|----|------|------|------|
| functional-tester | 功能測試員 | haiku | 正常流程、功能驗證 |
| edge-case-hunter | 邊界獵人 | sonnet | 邊界條件、異常處理 |
| regression-checker | 回歸檢查員 | haiku | 回歸測試、副作用 |
| acceptance-validator | 驗收驗證員 | sonnet | 驗收標準、需求滿足 |

模型路由：@shared/config/model-routing.yaml

## 前置條件

必須先執行 `/multi-review`：
```
.claude/memory/review/{impl-id}/review-summary.md
```

## Flags

- `--review <path>` - 指定審查報告路徑
- `--acceptance <path>` - 指定驗收標準

## 通過標準

| 測試類型 | 通過率 |
|----------|--------|
| 功能測試 | 100% |
| 邊界測試 | 90% |
| 回歸測試 | 100% |

## 輸出

```
.claude/memory/verify/{review-id}/
├── meta.yaml
├── perspectives/*.md
├── summaries/*.yaml
└── verify-summary.md
```

## 最終判定

- ✅ PASS - 所有標準通過
- ⚠️ CONDITIONAL - 需修復後重測
- ❌ FAIL - 需重新實作

$ARGUMENTS
