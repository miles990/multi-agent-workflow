# 工作流設計師報告

> Plugin 開發自動化工作流整合設計

**設計師**：工作流設計師
**日期**：2026-02-01
**版本**：1.0.0

## 核心發現

### 1. 工具分散問題嚴重

- 開發流程分散在 3 個層級：Shell 腳本、Python CLI、配置
- 發布流程包含 8 個主要步驟，每個步驟有獨立的驗證邏輯
- 監控工具使用 fswatch/inotifywait/polling 三層備選，缺乏統一入口
- **影響**：開發者需理解多個工具，錯誤恢復能力弱

### 2. 執行模式與品質閘門不對齊

- Orchestrate Skill 支援 3 種執行模式（express/default/quality）
- Plugin 工作流無相應的輪廓化設計
- 發布流程固定為 8 步，無法根據模式調整驗證深度

### 3. Task 系統整合不足

- 發布流程已設計 ReleaseProgress（9 步進度追蹤）
- 但未利用 Claude Code Tasks API
- 無法在失敗時創建可追蹤的任務

### 4. Hook 整合機會被低估

- 現有 Shell 腳本使用硬寫 commit message
- 未利用 commit-protocol.md 的統一格式
- 無 PostToolUse Hook 支援自動提交

## 詳細分析

### 現有工作流架構

**開發流程（Dev Workflow）**：
```
sync-to-cache.sh → watch (fswatch/inotifywait) → incremental sync
  ↓
cache/marketplace 更新
  ↓ (手動測試)
dev 循環完成
```

**發布流程（Release Workflow）**：
```
validate → test → check_git → bump_version → changelog → commit → tag → push
   ↓        ↓        ↓           ↓            ↓          ↓        ↓      ↓
 Shell    Python   Git         Python      Python      Git      Git    Git
```

**架構問題**：
- 開發流程：純 Shell，依賴系統工具
- 發布流程：混合 Shell/Python，增加維護負擔
- 缺乏統一入口和狀態管理

### Multi-Agent 工作流對比

| Orchestrate | Plugin Dev | Plugin Release |
|-------------|-----------|-----------------|
| RESEARCH(4視角) | _(無)_ | _(無)_ |
| PLAN(4視角) | _(無)_ | _(無)_ |
| IMPLEMENT(4角色) | dev-watch(1) | _(無)_ |
| REVIEW(4視角) | _(無)_ | validate(shell) |
| VERIFY(4視角) | _(無)_ | test(pytest) |

**發現**：Plugin 開發缺乏多視角並行設計

### ReleaseProgress 設計的潛力

```python
class ReleaseStep(Enum):
    VALIDATE → TEST → CHECK_GIT → BUMP_VERSION →
    GENERATE_CHANGELOG → GIT_COMMIT → GIT_TAG → GIT_PUSH →
    UPDATE_MARKETPLACE → COMPLETE

@dataclass
class ReleaseProgress:
    current_step: ReleaseStep
    completed_steps: list[ReleaseStep]
    failed_step: Optional[ReleaseStep]
```

**利用機會**：
- 可映射到 Task API：每個 Step = 一個 Task
- 支援失敗恢復：progress 持久化
- 支援進度 UI

## 工作流設計提案

### 方案 A：單一 Skill（推薦）

**建立 `skills/plugin-dev` Skill**

```yaml
---
name: plugin-dev
version: 1.0.0
description: Plugin 開發完整工作流 - 開發模式 + 發布流程
triggers: [plugin-dev, plugin-watch, plugin-publish]
context: fork
agent: general-purpose
allowed-tools: [Read, Write, Bash, Grep, Glob, Task, TaskCreate, TaskUpdate]
model: haiku
---
```

**內部階段**：

```
Phase 0: 初始化
  ├── 檢測 plugin.json
  ├── 確認模式（dev/release）
  └── 初始化 .plugin-dev/ 結構

Phase 1: DEV 模式（開發持續同步）
  ├── 執行 sync
  ├── 啟動 watch
  └── 監控檔案變更

Phase 2: RELEASE 模式（發布工作流）
  ├── 子階段 2.1: Validation
  │   ├── Structure Validator
  │   ├── Dependency Checker
  │   ├── Version Consistency
  │   └── Git Status
  │
  ├── 子階段 2.2: Testing
  │   ├── Unit Tester
  │   └── Integration Tester
  │
  ├── 子階段 2.3: Version & Changelog
  │   ├── Bump Version
  │   └── Generate Changelog
  │
  ├── 子階段 2.4: Git Operations
  │   ├── Commit
  │   ├── Tag
  │   └── Push
  │
  └── 子階段 2.5: Marketplace Update

Phase 3: 品質閘門
  ├── Release score ≥ 80
  ├── Test score ≥ 85
  └── Integrity check
```

**執行模式適配**：

```yaml
# express 模式
validation: [Structure, Version]  # 2 個檢查
testing: skip
release_dry_run: true

# default 模式
validation: [Structure, Dependency, Version, Git]  # 4 個檢查
testing: [Unit]
release_dry_run: false

# quality 模式
validation: [Structure, Dependency, Version, Git, Lint]  # 5 個檢查
testing: [Unit, Integration, Smoke]
final_review: require_human_approval
```

### 方案 B：兩個 Skills

**skills/plugin-dev** - 開發環境管理
**skills/plugin-release** - 發布流程編排

**優點**：職責清晰、獨立治理
**缺點**：增加整合複雜性

### 推薦：方案 A

**理由**：
1. Plugin 開發是單一領域
2. IMPLEMENT Skill 也是單一 Skill 多子階段
3. 簡化 Orchestrate 整合
4. 使用者體驗一致

## 整合策略

### 1. 與 Orchestrate Skill 整合

**新增 `/orchestrate --plugin` 模式**：

```bash
/orchestrate --plugin [需求描述]

# 等同於：
PLUGIN-RESEARCH → PLUGIN-PLAN → PLUGIN-RELEASE → VERIFY
```

### 2. Task API 整合

**ReleaseProgress → Task 映射**：

```python
task_id_validate = TaskCreate({
    'subject': 'Validate plugin structure',
})

task_id_test = TaskCreate({
    'subject': 'Run tests',
    'addBlockedBy': [task_id_validate],
})

task_id_release = TaskCreate({
    'subject': 'Execute release',
    'addBlockedBy': [task_id_test],
})
```

### 3. Hook 整合

**PostToolUse Hook 支援**：
```yaml
{
  "PostToolUse": {
    "condition": "stage === 'PLUGIN-RELEASE'",
    "action": "auto_commit_if_version_changed"
  }
}
```

### 4. 配置集中化

**新增 `shared/plugin/workflow.yaml`**：

```yaml
workflow:
  dev:
    watch_dirs: [skills/, shared/, templates/]
    sync_mode: incremental

  release:
    stages: [validate, test, version, git, marketplace]
    parallel_groups:
      - [structure, dependency, version, git]
    dry_run_default: true
```

## 自動化機會優先排序

| 優先級 | 機會 | 成本 | 效益 |
|--------|------|------|------|
| P0 | Task API 整合 | 低 | 高 |
| P0 | 執行模式適配 | 低 | 高 |
| P1 | Hook 自動 commit | 中 | 中 |
| P1 | 多視角驗證並行化 | 中 | 中 |
| P2 | 智慧版本建議 | 低 | 低 |

## 風險分析

| 風險 | 影響 | 預防措施 |
|------|------|---------|
| 發布中斷版本不一致 | 高 | Progress 持久化 + Resume |
| Shell 邏輯難維護 | 中 | 遷移至 Python CLI |
| Hook 與手動操作衝突 | 中 | 清晰觸發條件 + 審計 |
| 新手流程不清 | 中 | 改進文檔 + 引導 |

## 總結

### 設計原則

1. **單一入口**：統一為 `/plugin-dev` Skill
2. **模式適配**：支援 express/default/quality
3. **Task 整合**：利用 Claude Code Tasks API
4. **Hook 協作**：自動 commit 與進度追蹤
5. **漸進採用**：保留手動模式作為 fallback

### 實作優先順序

1. 建立 Skill 結構
2. 整合 Task API
3. 實作執行模式
4. Hook 整合
5. Dogfooding 迭代

---

*由工作流設計師視角產出*
