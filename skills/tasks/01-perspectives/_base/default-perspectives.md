# Tasks 視角定義

本 Skill 的視角定義集中管理於 `shared/perspectives/catalog.yaml`。

## 引用方式

```yaml
# 從 catalog.yaml 載入本 skill 適用的視角
perspectives:
  source: shared/perspectives/catalog.yaml
  filter:
    category: tasks
  preset: standard  # 預設使用 4 視角
```

## 視角列表

### 標準模式 (4 視角)

| ID | 名稱 | 關注重點 | 模型層級 | 方法 | 產出 |
|----|------|----------|----------|------|------|
| `dependency-analyst` | 依賴分析師 | 任務依賴和執行順序分析 | sonnet | deep | dependency-graph.md |
| `task-decomposer` | 任務分解師 | 功能任務分解和工作量估算 | haiku | deep | T-F-*, T-R-* 任務 |
| `test-planner` | 測試規劃師 | TDD 對應和測試策略 | haiku | deep | TEST-* 任務 |
| `risk-preventor` | 風險預防師 | 風險任務識別和預防措施 | haiku | deep | RISK-* 任務 |

### 快速模式 (2 視角)

| ID | 名稱 | 關注重點 |
|----|------|----------|
| `dependency-analyst` | 依賴分析師 | 任務依賴和執行順序分析 |
| `task-decomposer` | 任務分解師 | 功能任務分解和工作量估算 |

### 深度模式 (6 視角)

標準 4 視角 + 專用視角：

| ID | 名稱 | 關注重點 |
|----|------|----------|
| `parallel-optimizer` | 並行效率優化師 | 並行執行優化、資源利用、瓶頸消除 |
| `doc-planner` | 文檔任務規劃師 | 文檔任務規劃、知識傳承、團隊溝通 |

## 視角協作模式

```
Phase 1: 依賴分析（先行）
┌──────────────────────────────────────────────────┐
│  dependency-analyst                               │
│  產出：dependency-graph.md（含 DAG 和 Wave 分組） │
└──────────────────────────────────────────────────┘
         ↓ 依賴圖作為輸入
Phase 2: 並行任務分解
┌──────────────┬──────────────┬──────────────┐
│ task-        │ test-        │ risk-        │
│ decomposer   │ planner      │ preventor    │
│              │              │              │
│ T-F-*, T-R-* │ TEST-*       │ RISK-*       │
└──────────────┴──────────────┴──────────────┘
         ↓
Phase 3: REDUCE 整合
┌──────────────────────────────────────────────────┐
│  合併任務清單 → 應用依賴 → 生成 Wave → tasks.yaml │
└──────────────────────────────────────────────────┘
```

## 視角輸出要求

### 通用要求

1. 任務 ID 格式正確（T-F-001, TEST-001, RISK-001）
2. 每個任務有明確的驗收標準
3. 任務粒度在 10-60 分鐘範圍
4. 優先級標記（P0/P1/P2）
5. 依賴關係明確

### 視角專屬要求

| 視角 | 專屬要求 |
|------|----------|
| dependency-analyst | DAG 無循環、Wave 分組合理 |
| task-decomposer | 估算完整、files 欄位填寫 |
| test-planner | test_cases 完整、TDD 順序正確 |
| risk-preventor | related_risk 關聯、trigger 明確 |

完整定義請參考 [catalog.yaml](../../../../shared/perspectives/catalog.yaml)。
