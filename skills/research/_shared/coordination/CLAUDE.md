# 協調模組（Coordination）

> Map-Reduce 並行執行框架

## 自動載入

當引用 `@shared/coordination` 時，自動應用：
- `map-phase.md` - 並行執行指南
- `reduce-phase.md` - 整合匯總指南

## 核心概念

### Map Phase（並行執行）

多個 Agent 同時處理不同視角：

```
┌──────────┬──────────┬──────────┬──────────┐
│ 視角 A   │ 視角 B   │ 視角 C   │ 視角 D   │
│          │          │          │          │
│  獨立    │  獨立    │  獨立    │  獨立    │
│  執行    │  執行    │  執行    │  執行    │
└────┬─────┴────┬─────┴────┬─────┴────┬─────┘
     └──────────┴──────────┴──────────┘
                    ↓
              收集所有結果
```

### Reduce Phase（匯總整合）

收集視角報告 → 交叉驗證 → 解決矛盾 → 生成匯總報告

## 強制要求

1. **視角報告必須寫入檔案**
   ```
   .claude/memory/{type}/{id}/perspectives/{perspective_id}.md
   ```

2. **報告格式規範**
   - 必須包含 `## 核心發現` section
   - 最少 50 行（確保分析深度）
   - 無長度上限（Reduce 會智能處理）

3. **Agent 能力限制**
   - ✅ Read, Glob, Grep, Bash, WebFetch, Write
   - ❌ Task（視角 Agent 不應開子 Agent）

## 模型路由

參考 @shared/config/model-routing.yaml 決定模型選擇：
- 深度分析類 → sonnet
- 流程整理類 → haiku
- 關鍵決策類 → opus

## 失敗處理

- Agent 超時：記錄部分結果，標記「部分完成」
- Agent 錯誤：重試一次，仍失敗則跳過或使用備用視角

## 參考

- @shared/synthesis/cross-validation.md - 交叉驗證
- @shared/synthesis/conflict-resolution.md - 矛盾解決
- @shared/config/model-routing.yaml - 模型路由
