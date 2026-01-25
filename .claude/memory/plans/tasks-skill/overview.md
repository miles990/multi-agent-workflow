# TASKS Skill 實作計劃 - 概覽

> 一頁速覽：4 視角規劃的核心結論

## 核心結論

**新增 TASKS Skill**，位於 PLAN 和 IMPLEMENT 之間：

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

## 設計決策

| 決策 | 選擇 |
|------|------|
| 目錄結構 | 複用現有 skill 結構 |
| 視角配置 | 4 視角 |
| 協作模式 | 依賴分析先行，其他並行 |
| 輸出格式 | tasks.yaml |
| 任務粒度 | 10-60 分鐘 |

## 4 視角配置

| 視角 | 職責 | 產出 |
|------|------|------|
| `dependency-analyst` | 分析依賴、建立執行順序 | dependency-graph.md |
| `task-decomposer` | 分解實作任務 | T-F-* 任務 |
| `test-planner` | 規劃測試任務 | TEST-* 任務 |
| `risk-preventor` | 規劃風險預防任務 | RISK-* 任務 |

## 里程碑

| 里程碑 | 時間 | 任務數 | 目標 |
|--------|------|--------|------|
| M1: 基礎結構 | 2h | 5 | Skill 骨架和配置 |
| M2: 視角與模板 | 2.5h | 7 | 4 視角實作 |
| M3: 整合 | 1.5h | 5 | 與生態系整合 |

**總計**：6-7 小時，17 個任務

## 關鍵路徑

```
T-1.1 → T-1.4 → T-2.2 → T-2.6 → T-3.2 → T-3.5
建立    定義     實作     建立     整合     測試
結構    schema   視角     模板     ORCH
```

## 主要風險

| 風險 | 嚴重度 | 緩解 |
|------|--------|------|
| R1: PLAN 格式不一致 | 高 | 格式驗證 + 容錯解析 |
| R3: 循環依賴 | 高 | DAG 驗證 + 錯誤報告 |
| R4: IMPLEMENT 整合 | 高 | 漸進式整合 + 版本號 |

## 快速連結

- [完整實作計劃](./implementation-plan.md)
- [里程碑清單](./milestones.md)
- [風險緩解策略](./risk-mitigation.md)
- [視角報告](./perspectives/)

## 來源研究

本計劃基於深度研究報告：
- 研究 ID：tasks-stage-design
- 研究模式：deep（6 視角）
- 路徑：.claude/memory/research/tasks-stage-design/
