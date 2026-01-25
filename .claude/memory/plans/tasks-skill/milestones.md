# TASKS Skill 里程碑

> 3 個里程碑，17 個任務，預估 6-7 小時

---

## 里程碑總覽

```
┌─────────────────────────────────────────────────────────────────┐
│  M1: 基礎結構        M2: 視角與模板       M3: 整合              │
│  (2h)                (2.5h)               (1.5h)               │
│                                                                 │
│  ┌─────────┐        ┌─────────┐         ┌─────────┐           │
│  │ T-1.1   │───────→│ T-2.1   │────────→│ T-3.1   │           │
│  │ T-1.2   │        │ T-2.2   │         │ T-3.2   │           │
│  │ T-1.3   │        │ T-2.3   │         │ T-3.3   │           │
│  │ T-1.4   │        │ T-2.4   │         │ T-3.4   │           │
│  │ T-1.5   │        │ T-2.5   │         │ T-3.5   │           │
│  └─────────┘        │ T-2.6   │         └─────────┘           │
│                     │ T-2.7   │                                │
│                     └─────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## M1: 基礎結構

**預估時間**：2 小時
**目標**：建立 skill 骨架和核心配置

### 任務清單

| ID | 任務 | 複雜度 | 優先級 | 預估 | 狀態 |
|----|------|--------|--------|------|------|
| T-1.1 | 建立 skills/tasks/ 目錄結構 | XS | P0 | 15m | pending |
| T-1.2 | 建立 SKILL.md 主入口 | S | P0 | 30m | pending |
| T-1.3 | 建立 00-quickstart/ | S | P0 | 20m | pending |
| T-1.4 | 定義 config/schema.yaml | M | P0 | 45m | pending |
| T-1.5 | 建立 config/task-types.md | S | P1 | 20m | pending |

### 依賴關係

```
T-1.1 ──→ T-1.2 ──→ T-1.3
  │                   │
  └───→ T-1.4 ───→ T-1.5
```

### 驗收標準

- [ ] 目錄結構完整：skills/tasks/{00-quickstart, 01-perspectives, config, templates}
- [ ] SKILL.md 包含完整的 skill 定義（name, version, triggers, keywords）
- [ ] schema.yaml 定義完整的 tasks.yaml 結構
- [ ] 符合現有 skill 目錄結構慣例

---

## M2: 視角與模板

**預估時間**：2.5 小時
**目標**：實作 4 個核心視角和輸出模板
**依賴**：M1 完成

### 任務清單

| ID | 任務 | 複雜度 | 優先級 | 預估 | 狀態 |
|----|------|--------|--------|------|------|
| T-2.1 | 建立 default-perspectives.md | S | P0 | 20m | pending |
| T-2.2 | 實作 dependency-analyst 視角 | M | P0 | 30m | pending |
| T-2.3 | 實作 task-decomposer 視角 | M | P0 | 30m | pending |
| T-2.4 | 實作 test-planner 視角 | M | P0 | 30m | pending |
| T-2.5 | 實作 risk-preventor 視角 | M | P0 | 30m | pending |
| T-2.6 | 建立 tasks.yaml 模板 | S | P0 | 15m | pending |
| T-2.7 | 建立 dependency-graph 模板 | S | P1 | 15m | pending |

### 依賴關係

```
T-2.1 ──→ T-2.2 ──┐
          T-2.3 ──┼──→ T-2.6 ──→ T-2.7
          T-2.4 ──┤
          T-2.5 ──┘
```

### 驗收標準

- [ ] 4 視角 prompt 完成且符合 base-perspective.md 格式
- [ ] dependency-analyst 可產出 DAG 和 Wave 分組
- [ ] task-decomposer 可產出 T-F-* 任務
- [ ] test-planner 可產出 TEST-* 任務
- [ ] risk-preventor 可產出 RISK-* 任務
- [ ] tasks.yaml 模板符合 schema 定義
- [ ] 協作模式正確：依賴分析先行，其他並行

---

## M3: 整合

**預估時間**：1.5 小時
**目標**：與現有生態系整合
**依賴**：M2 完成

### 任務清單

| ID | 任務 | 複雜度 | 優先級 | 預估 | 狀態 |
|----|------|--------|--------|------|------|
| T-3.1 | 建立 Memory 結構 | S | P0 | 15m | pending |
| T-3.2 | 更新 ORCHESTRATE 階段判斷 | M | P0 | 30m | pending |
| T-3.3 | 更新工作流文檔 | S | P1 | 20m | pending |
| T-3.4 | 更新 README | S | P1 | 15m | pending |
| T-3.5 | 端到端測試 | M | P0 | 30m | pending |

### 依賴關係

```
T-3.1 ──→ T-3.2 ──→ T-3.5
          T-3.3 ──┘
          T-3.4 ──┘
```

### 驗收標準

- [ ] Memory 結構：.claude/memory/tasks/{feature-id}/
- [ ] ORCHESTRATE 可識別 TASKS 階段並正確路由
- [ ] 工作流圖更新為：RESEARCH → PLAN → TASKS → IMPLEMENT → REVIEW → VERIFY
- [ ] README 包含 TASKS skill 說明
- [ ] 端到端測試通過：PLAN → TASKS → IMPLEMENT 串接正常

---

## 執行順序

### 建議順序（考慮並行）

```
Week 1 / Day 1:
├── Wave 1: T-1.1, T-1.2 (並行)
├── Wave 2: T-1.3, T-1.4, T-1.5 (並行)
└── 驗收 M1

Week 1 / Day 2:
├── Wave 3: T-2.1 → T-2.2, T-2.3, T-2.4, T-2.5 (先後+並行)
├── Wave 4: T-2.6, T-2.7 (並行)
└── 驗收 M2

Week 1 / Day 3:
├── Wave 5: T-3.1, T-3.2, T-3.3, T-3.4 (並行)
├── Wave 6: T-3.5
└── 驗收 M3
```

---

## 進度追蹤

| 里程碑 | 任務數 | 完成數 | 進度 |
|--------|--------|--------|------|
| M1: 基礎結構 | 5 | 0 | 0% |
| M2: 視角與模板 | 7 | 0 | 0% |
| M3: 整合 | 5 | 0 | 0% |
| **總計** | **17** | **0** | **0%** |
