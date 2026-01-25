# TASKS 階段設計 - 研究概覽

> 一頁速覽：6 視角深度研究的核心結論

## 核心結論

**新增 TASKS 階段**，位於 PLAN 和 IMPLEMENT 之間：

```
RESEARCH → PLAN → TASKS → IMPLEMENT → REVIEW → VERIFY
                    ↑
                 新增階段
```

## 為什麼需要 TASKS？

| 問題 | TASKS 如何解決 |
|------|----------------|
| PLAN 產出太抽象 | 將里程碑分解為 10-60 分鐘的可執行任務 |
| IMPLEMENT 職責過重 | 專注執行，不再需要邊做邊分解 |
| 依賴關係不清楚 | DAG + Wave 分組，明確並行機會 |
| 測試容易遺漏 | test-planner 視角確保 TDD 先行 |
| 風險處理被動 | risk-preventor 視角將風險轉為預防任務 |

## 核心設計

### 4 視角配置

| 視角 | 職責 | 產出 |
|------|------|------|
| `dependency-analyst` | 分析依賴、建立執行順序 | dependency-graph.md |
| `task-decomposer` | 分解實作任務 | T-F-* 任務 |
| `test-planner` | 規劃測試任務 | TEST-* 任務 |
| `risk-preventor` | 規劃風險預防任務 | RISK-* 任務 |

### 協作模式

```
依賴分析先行 → 其他視角並行 → REDUCE 彙整
```

### 主要產出

```yaml
tasks.yaml:
  - 15 個結構化任務定義
  - 依賴關係（blocked_by / blocks）
  - Wave 分組（並行執行計劃）
  - 驗收標準
```

## 快速連結

- [完整設計方案](./synthesis.md)
- [任務 Schema 定義](./synthesis.md#4-tasksyaml-schema)
- [執行流程](./synthesis.md#5-執行流程)
- [實施路線圖](./synthesis.md#10-實施路線圖)
