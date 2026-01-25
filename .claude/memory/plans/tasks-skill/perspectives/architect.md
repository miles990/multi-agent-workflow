# 架構師視角報告

> 視角：系統架構師
> 聚焦：技術可行性、組件設計、擴展性

## 技術架構設計

### 目錄結構

```
skills/tasks/
├── SKILL.md                  # 主入口
├── 00-quickstart/
│   └── _base/
│       └── usage.md          # 快速開始
├── 01-perspectives/
│   ├── _base/
│   │   └── default-perspectives.md
│   └── perspectives/
│       ├── dependency-analyst.md
│       ├── task-decomposer.md
│       ├── test-planner.md
│       └── risk-preventor.md
├── config/
│   ├── task-types.md         # 任務類型定義
│   └── schema.yaml           # tasks.yaml schema
└── templates/
    ├── tasks.yaml.template   # 輸出模板
    └── dependency-graph.template.md
```

### 組件設計

#### 1. 核心組件

| 組件 | 職責 | 依賴 |
|------|------|------|
| PlanLoader | 載入 PLAN 輸出 | shared/integration |
| DependencyAnalyzer | 建立 DAG、拓撲排序 | 無 |
| TaskDecomposer | 分解實作任務 | DependencyAnalyzer |
| WaveGenerator | 生成並行分組 | DependencyAnalyzer |
| TasksYamlWriter | 產出 tasks.yaml | 全部 |

#### 2. 數據流

```
PLAN 輸出
    ↓
┌─────────────────────────────────────────────┐
│  PlanLoader                                   │
│  - 讀取 implementation-plan.md               │
│  - 讀取 milestones.md                        │
│  - 讀取 risk-mitigation.md（可選）           │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  MAP Phase                                    │
│  1. DependencyAnalyzer (先行)                │
│  2. 並行：TaskDecomposer + TestPlanner +     │
│           RiskPreventor                       │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  REDUCE Phase                                 │
│  1. WaveGenerator (合併+分組)                │
│  2. TasksYamlWriter (輸出)                   │
└─────────────────────────────────────────────┘
    ↓
tasks.yaml
```

### tasks.yaml Schema

```yaml
version: "1.0.0"
metadata:
  feature_id: string
  source_plan: string
  generated_at: datetime
  total_tasks: number
  estimated_duration: string

config:
  parallel_execution: boolean
  max_concurrent: number
  pass_at_k: number

milestones:
  - id: string
    name: string
    depends_on: [string]
    tasks: [string]

tasks:
  - id: string          # 格式：T-F-001, TEST-001, RISK-001
    type: enum          # feature, test, prevention, rollback, monitoring
    milestone: string
    name: string
    description: string
    estimate:
      duration: string
      complexity: enum  # XS, S, M, L, XL
    priority: enum      # P0, P1, P2
    dependencies:
      blocked_by: [string]
      blocks: [string]
    acceptance_criteria: [string]
    files:
      create: [string]
      modify: [string]
    supervision_hints:
      tdd: string
      security: string
    status: enum        # pending, in_progress, completed, failed, skipped

execution_plan:
  waves:
    - id: string
      tasks: [string]
      depends_on: [string]
      sync_point: string
  critical_path: [string]
  estimated_total: string

summary:
  by_type: object
  by_priority: object
  by_milestone: object
```

### 擴展性考量

1. **新視角擴展**：透過 `01-perspectives/perspectives/` 新增
2. **任務類型擴展**：透過 `config/task-types.md` 定義
3. **輸出格式擴展**：保持 YAML 主檔，可新增 JSON/Markdown 轉換
4. **驗證規則擴展**：透過 schema 驗證

## 共用模組整合

複用以下 shared 模組：

| 模組 | 用途 |
|------|------|
| `shared/coordination/` | Map-Reduce 協調 |
| `shared/synthesis/` | 交叉驗證 |
| `shared/perspectives/` | 視角基礎 |
| `shared/integration/` | Memory 整合 |
| `shared/metrics/` | 指標收集 |

## 設計決策

| 決策 | 選擇 | 理由 |
|------|------|------|
| 目錄結構 | 複用現有 skill 結構 | 一致性、減少學習成本 |
| Schema 格式 | YAML | 可讀性、註解支援、現有慣例 |
| 依賴分析時機 | 先行執行 | 為其他視角提供輸入 |
| Wave 分組 | 內建於 execution_plan | 簡化 IMPLEMENT 消費 |
