執行多視角程式碼審查。

## 流程

1. 載入 @skills/review/SKILL.md
2. 載入 @shared/coordination/map-phase.md
3. 並行啟動 4 視角 Agent（code-quality, test-coverage, documentation, integration）
4. 收集視角報告到 `.claude/memory/review/{impl-id}/perspectives/`
5. 執行 @shared/coordination/reduce-phase.md 匯總
6. 生成 `review-summary.md`

## 視角配置

| ID | 名稱 | 模型 | 聚焦 |
|----|------|------|------|
| code-quality | 程式碼品質 | haiku | 命名、結構、可讀性 |
| test-coverage | 測試覆蓋 | haiku | 覆蓋率、測試品質 |
| documentation | 文檔檢查 | haiku | 註解、README、API 文檔 |
| integration | 整合分析 | sonnet | 整合問題、依賴衝突 |

模型路由：@shared/config/model-routing.yaml

## 前置條件

必須先執行 `/multi-implement`：
```
.claude/memory/implement/{tasks-id}/summary.md
```

## Flags

- `--impl <path>` - 指定實作摘要路徑
- `--severity <BLOCKER|HIGH|MEDIUM|LOW>` - 最低報告級別

## 問題分類

| 級別 | 說明 | 需處理 |
|------|------|--------|
| BLOCKER | 阻斷性問題 | 必須 |
| HIGH | 高風險問題 | 必須 |
| MEDIUM | 中等問題 | 建議 |
| LOW | 低風險/建議 | 可選 |

## 輸出

```
.claude/memory/review/{impl-id}/
├── meta.yaml
├── perspectives/*.md
├── summaries/*.yaml
└── review-summary.md
```

## 擴展思考

複雜整合分析時，建議使用擴展思考。

$ARGUMENTS
