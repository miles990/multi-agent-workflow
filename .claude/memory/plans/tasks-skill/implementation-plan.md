# TASKS Skill 實作計劃

> 4 視角規劃整合：架構 + 風險 + 估算 + UX

**規劃日期**：2026-01-25
**來源研究**：tasks-stage-design
**預估工期**：6-7 小時

---

## 執行摘要

### 目標

建立 TASKS Skill，位於 PLAN 與 IMPLEMENT 之間，負責將宏觀計劃分解為可執行的細粒度任務。

### 新工作流

```
RESEARCH → PLAN → TASKS → IMPLEMENT → REVIEW → VERIFY
                    ↑
                 新增階段
```

### 核心價值

| 面向 | 價值 |
|------|------|
| **職責分離** | PLAN 做設計，TASKS 做分解，IMPLEMENT 專注執行 |
| **並行效率** | 明確的 Wave 分組，最大化並行機會 |
| **品質保障** | 測試任務 + 風險任務內建，TDD 先行 |
| **可追溯性** | 每個任務有明確的驗收標準和依賴關係 |

---

## 設計共識

### 4 視角達成的共識

| 共識點 | 說明 |
|--------|------|
| 目錄結構 | 複用現有 skill 結構（skills/tasks/） |
| 視角配置 | 4 視角：dependency-analyst, task-decomposer, test-planner, risk-preventor |
| 協作模式 | 依賴分析先行，其他 3 視角並行 |
| 輸出格式 | tasks.yaml（YAML 格式，結構化） |
| 任務粒度 | 10-60 分鐘可完成的任務單元 |
| 依賴模型 | DAG + Wave 分組 |
| CLI 設計 | /multi-tasks [plan-id] |
| Memory 路徑 | .claude/memory/tasks/{feature-id}/ |

### 解決的矛盾

| 矛盾 | 決策 | 理由 |
|------|------|------|
| 獨立階段 vs 整合到 PLAN | 獨立階段 | 職責更清晰，符合單一職責原則 |
| 依賴分析時機 | 先行執行 | 為其他視角提供 DAG 輸入 |

---

## 里程碑規劃

### M1: 基礎結構（2 小時）

**目標**：建立 skill 骨架和核心配置

| 任務 ID | 任務 | 優先級 | 預估 |
|---------|------|--------|------|
| T-1.1 | 建立 skills/tasks/ 目錄結構 | P0 | 15m |
| T-1.2 | 建立 SKILL.md 主入口 | P0 | 30m |
| T-1.3 | 建立 00-quickstart/ | P0 | 20m |
| T-1.4 | 定義 config/schema.yaml | P0 | 45m |
| T-1.5 | 建立 config/task-types.md | P1 | 20m |

**驗收標準**：
- [ ] 目錄結構完整且符合現有 skill 慣例
- [ ] SKILL.md 可被系統載入
- [ ] tasks.yaml schema 定義完成

---

### M2: 視角與模板（2.5 小時）

**目標**：實作 4 個核心視角和輸出模板

**依賴**：M1 完成

| 任務 ID | 任務 | 優先級 | 預估 |
|---------|------|--------|------|
| T-2.1 | 建立 default-perspectives.md | P0 | 20m |
| T-2.2 | 實作 dependency-analyst 視角 | P0 | 30m |
| T-2.3 | 實作 task-decomposer 視角 | P0 | 30m |
| T-2.4 | 實作 test-planner 視角 | P0 | 30m |
| T-2.5 | 實作 risk-preventor 視角 | P0 | 30m |
| T-2.6 | 建立 tasks.yaml 模板 | P0 | 15m |
| T-2.7 | 建立 dependency-graph 模板 | P1 | 15m |

**驗收標準**：
- [ ] 4 視角 prompt 完成且可執行
- [ ] 模板可生成符合 schema 的輸出
- [ ] 視角間協作模式正確（依賴分析先行）

---

### M3: 整合（1.5 小時）

**目標**：與現有生態系整合

**依賴**：M2 完成

| 任務 ID | 任務 | 優先級 | 預估 |
|---------|------|--------|------|
| T-3.1 | 建立 Memory 結構 | P0 | 15m |
| T-3.2 | 更新 ORCHESTRATE 階段判斷 | P0 | 30m |
| T-3.3 | 更新工作流文檔 | P1 | 20m |
| T-3.4 | 更新 README | P1 | 15m |
| T-3.5 | 端到端測試 | P0 | 30m |

**驗收標準**：
- [ ] ORCHESTRATE 可正確識別 TASKS 階段
- [ ] 完整工作流可從 PLAN → TASKS → IMPLEMENT 串接
- [ ] 文檔和 README 更新完成

---

## 執行計劃

### Wave 分組（並行優化）

```
Wave 1 [可並行]
├── T-1.1 建立目錄結構
└── T-1.2 建立 SKILL.md
    ↓
Wave 2 [可並行，依賴 Wave 1]
├── T-1.3 建立 quickstart
├── T-1.4 定義 schema
└── T-1.5 定義 task-types
    ↓
Wave 3 [可並行，依賴 Wave 2]
├── T-2.1 default-perspectives
├── T-2.2 dependency-analyst
├── T-2.3 task-decomposer
├── T-2.4 test-planner
└── T-2.5 risk-preventor
    ↓
Wave 4 [可並行，依賴 Wave 3]
├── T-2.6 tasks.yaml 模板
└── T-2.7 dependency-graph 模板
    ↓
Wave 5 [可並行，依賴 Wave 4]
├── T-3.1 Memory 結構
├── T-3.2 ORCHESTRATE 更新
├── T-3.3 文檔更新
└── T-3.4 README 更新
    ↓
Wave 6 [依賴 Wave 5]
└── T-3.5 端到端測試
```

### 關鍵路徑

```
T-1.1 → T-1.4 → T-2.2 → T-2.6 → T-3.2 → T-3.5
建立    定義     實作     建立     整合     測試
結構    schema   視角     模板     ORCH
```

**關鍵路徑預估**：3.5 小時

---

## 技術設計

### 目錄結構

```
skills/tasks/
├── SKILL.md                  # 主入口
├── 00-quickstart/
│   └── _base/
│       └── usage.md
├── 01-perspectives/
│   ├── _base/
│   │   └── default-perspectives.md
│   └── perspectives/
│       ├── dependency-analyst.md
│       ├── task-decomposer.md
│       ├── test-planner.md
│       └── risk-preventor.md
├── config/
│   ├── task-types.md
│   └── schema.yaml
└── templates/
    ├── tasks.yaml.template
    └── dependency-graph.template.md
```

### tasks.yaml Schema 摘要

```yaml
version: "1.0.0"
metadata:
  feature_id: string
  total_tasks: number
  estimated_duration: string

config:
  parallel_execution: boolean
  max_concurrent: number

milestones:
  - id: string
    name: string
    tasks: [string]

tasks:
  - id: string          # T-F-001, TEST-001, RISK-001
    type: enum          # feature, test, prevention
    name: string
    priority: enum      # P0, P1, P2
    dependencies:
      blocked_by: [string]
      blocks: [string]
    acceptance_criteria: [string]
    status: enum        # pending, completed

execution_plan:
  waves:
    - id: string
      tasks: [string]
  critical_path: [string]
```

### 4 視角定義

| ID | 名稱 | 職責 | 產出 |
|----|------|------|------|
| `dependency-analyst` | 依賴分析師 | 分析依賴、建立 DAG、排序 | dependency-graph.md |
| `task-decomposer` | 任務分解師 | 分解實作任務（T-F-*） | implementation-tasks |
| `test-planner` | 測試規劃師 | 規劃測試任務（TEST-*） | test-tasks |
| `risk-preventor` | 風險預防師 | 規劃風險任務（RISK-*） | risk-tasks |

### 協作流程

```
Phase 1: dependency-analyst（先行）
         ↓ 產出 DAG
Phase 2: task-decomposer + test-planner + risk-preventor（並行）
         ↓
Phase 3: REDUCE 整合 → tasks.yaml
```

---

## 風險緩解

### 已識別風險

| 風險 | 嚴重度 | 緩解策略 |
|------|--------|----------|
| R1: PLAN 格式不一致 | 高 | 格式驗證 + 容錯解析 |
| R2: 任務粒度不一致 | 中 | 在 prompt 明確定義 10-60m 範圍 |
| R3: 循環依賴 | 高 | DAG 驗證 + 錯誤報告 |
| R4: IMPLEMENT 整合 | 中 | 漸進式整合 + 版本號 |

### 回退點

| 回退點 | 觸發條件 | 動作 |
|--------|----------|------|
| BP-1 | PLAN 載入失敗 | 停止，要求修正 PLAN |
| BP-2 | 循環依賴 | 停止，顯示循環路徑 |
| BP-3 | 視角全部失敗 | 回退到 PLAN |

---

## CLI 設計

### 命令

```bash
/multi-tasks [plan-id]
/multi-tasks --from-plan user-auth
/multi-tasks --quick user-auth     # 2 視角
/multi-tasks --deep user-auth      # 6 視角
```

### 輸出格式

```
✅ 任務分解完成：{feature-id}

📊 分解摘要：
   - {N} 個視角完成
   - {N} 個任務產出
   - {N} 個 Wave 分組
   - 預估總時長：{duration}

📋 任務分佈：
   - 功能任務 (T-F-*): {N} 個
   - 測試任務 (TEST-*): {N} 個
   - 風險任務 (RISK-*): {N} 個

📁 已存檔：
   .claude/memory/tasks/{feature-id}/tasks.yaml
```

---

## Memory 輸出結構

```
.claude/memory/tasks/{feature-id}/
├── meta.yaml
├── overview.md
├── perspectives/
│   ├── dependency-analyst.md
│   ├── task-decomposer.md
│   ├── test-planner.md
│   └── risk-preventor.md
├── tasks.yaml              # 主輸出
├── dependency-graph.md
└── execution-plan.md
```

---

## 驗收標準

### 功能驗收

- [ ] `/multi-tasks` 命令可正確執行
- [ ] 4 視角可並行執行
- [ ] 產出符合 schema 的 tasks.yaml
- [ ] Wave 分組正確識別並行任務
- [ ] Memory 存檔結構正確

### 整合驗收

- [ ] ORCHESTRATE 可識別 TASKS 階段
- [ ] PLAN → TASKS 數據流正確
- [ ] TASKS → IMPLEMENT 數據流正確
- [ ] 回退機制正常運作

### 品質驗收

- [ ] 錯誤訊息清晰可操作
- [ ] 文檔完整且準確
- [ ] 與現有 skill 風格一致
