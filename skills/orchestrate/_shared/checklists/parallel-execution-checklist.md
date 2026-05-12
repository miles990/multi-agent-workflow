# 並行執行識別 Checklist

> 幫助計劃執行時識別和最大化並行機會的完整檢查清單

---

## 一、任務依賴關係分析

### 1.1 依賴映射

- [ ] **讀取計劃文檔**
  - [ ] 打開 `implementation-plan.md` 檔案
  - [ ] 定位 `## 工作項` 或 `## Tasks` 部分
  - [ ] 識別所有 `depends_on` 聲明

- [ ] **提取顯式依賴（L1）**
  - [ ] 列出每個任務的 `depends_on` 列表
  - [ ] 檢查依賴的目標任務是否真實存在
  - [ ] 驗證沒有自身依賴自己的情況
  - [ ] 記錄依賴的原因（使用/生成的數據或資源）

**範例**：
```yaml
Task T-F-001 (實作登入功能):
  depends_on: [TEST-001, T-F-000-setup-auth]
  reason: 需要測試先行，需要認證框架已設置

Task T-F-002 (實作登出功能):
  depends_on: [T-F-001]
  reason: 登出功能依賴登入功能
```

### 1.2 隱含依賴偵測

- [ ] **檔案層面依賴（L2）**
  - [ ] 列出每個任務修改的檔案
  - [ ] 識別多個任務修改同一檔案的情況
  - [ ] 檢查檔案讀寫順序
  - [ ] 標記為「同檔案衝突」或「讀寫序列」

**檢查清單**：
```
[] 檔案 A：被任務 T1, T2 修改 → T1 → T2（順序依賴）
[] 檔案 B：被任務 T3 修改，被 T4 讀取 → T3 → T4
[] 檔案 C：被多個任務讀取（無依賴）→ 可並行
```

- [ ] **語意依賴（L3）**
  - [ ] 檢查任務描述中的關鍵詞
  - [ ] 尋找「生成」「使用」「依賴」等詞彙
  - [ ] 識別資料流依賴（一個任務輸出是另一個任務輸入）
  - [ ] 識別配置依賴（需要特定配置或常數）

**語意關鍵詞映射**：
```
生成類: generates, creates, exports, outputs, produces, returns, saves
消費類: uses, requires, imports, reads, loads, depends on, needs

例: "生成 JWT token" 的任務 必須 在 "使用 JWT 驗證" 的任務之前
```

- [ ] **環境依賴（L4）**
  - [ ] 檢查是否需要數據庫初始化
  - [ ] 檢查是否需要外部服務啟動（Redis, API Server）
  - [ ] 檢查是否需要環境變數/配置
  - [ ] 檢查是否需要特定版本的工具/庫
  - [ ] 標記為「環境前置條件」

**環境依賴範例**：
```
[] Database Setup → 所有涉及 DB 的任務依賴此
[] Redis Cache → 所有使用 Redis 的任務依賴此
[] API Server Start → 所有調用 API 的任務依賴此
[] Node Modules Installed → 所有 JS 任務依賴此
```

---

## 二、並行機會識別

### 2.1 無依賴任務

- [ ] **尋找孤立任務**
  - [ ] 沒有 `depends_on` 的任務
  - [ ] 不與其他任務共享檔案
  - [ ] 不修改全局配置或共享狀態
  - [ ] 不依賴外部環境前置條件

**識別方法**：
```
for each task:
  if (task.depends_on is empty OR task.depends_on only contains completed tasks)
    and (task.files has no overlap with other pending tasks)
    and (task.description has no semantic dependencies)
  then: 可並行
```

- [ ] **分組獨立任務**
  - [ ] 將無依賴任務分為同一「波次」
  - [ ] 驗證同波次的任務之間確實無依賴
  - [ ] 記錄各波次的任務列表

**波次範例**：
```
Wave 1（可同時執行）:
  - TEST-001: 登入測試
  - TEST-002: 登出測試
  - TEST-003: 忘記密碼測試

Wave 2（需完成 Wave 1）:
  - T-F-001: 實作登入功能
  - T-F-002: 實作登出功能
  - T-F-003: 實作忘記密碼功能
```

### 2.2 並行鏈式結構

- [ ] **識別獨立執行鏈**
  - [ ] 尋找任務序列 A → B → C（無橫向依賴）
  - [ ] 尋找平行的序列 X → Y → Z
  - [ ] 驗證兩條鏈之間無依賴關係
  - [ ] 標記為「並行鏈」

**鏈式結構範例**：
```
鏈 1: TEST-Auth → T-F-Auth → T-I-Auth（認證鏈）
鏈 2: TEST-Profile → T-F-Profile → T-I-Profile（資料鏈）
鏈 3: TEST-Permission → T-F-Permission → T-I-Permission（權限鏈）

✓ 三條鏈可完全並行，各鏈內部順序執行
```

### 2.3 並行寬度分析

- [ ] **計算最大並行寬度**
  - [ ] 找出每個時間點最多能並行的任務數
  - [ ] 識別「瓶頸任務」（許多任務的 blocker）
  - [ ] 識別「扇形展開」（一個任務依賴多個）
  - [ ] 識別「扇形收縮」（多個任務依賴一個）

**寬度分析圖示**：
```
Wave 1: [T1] [T2] [T3] [T4]      寬度 = 4（最大並行）
Wave 2: [T5 ─ 依賴 T1, T2]
        [T6 ─ 依賴 T3, T4]       寬度 = 2

Critical Path: T1 → T5 → T7 → T9  (決定總耗時)
```

---

## 三、何時使用並行 vs 順序

### 3.1 應該使用並行的情況

- [ ] **檢查清單**

| 條件 | 檢查 | 並行適用 |
|------|------|---------|
| 零依賴 | 任務間無 `depends_on` | ✅ |
| 檔案隔離 | 修改不同的檔案 | ✅ |
| 資源隔離 | 使用不同的資源（DB, API） | ✅ |
| 語意獨立 | 描述中無「先/後」關鍵詞 | ✅ |
| 環境充足 | 前置環境已準備好 | ✅ |
| 非短期任務 | 不是「檢查」或「驗證」類短任務 | ✅ |

- [ ] **並行收益評估**
  - [ ] 任務數量 >= 3？（收益明顯）
  - [ ] 個別任務耗時 >= 5 分鐘？（並行開銷相對小）
  - [ ] 總時間會顯著減少？（預期節省時間）
  - [ ] 資源足夠承載？（CPU/Memory/連接數）

### 3.2 應該使用順序的情況

- [ ] **檢查清單**

| 條件 | 檢查 | 順序適用 |
|------|------|---------|
| 明確依賴 | `depends_on` 清晰 | ✅ |
| 同檔案修改 | 多個任務修改同一檔案 | ✅ |
| 同資源競爭 | 修改同一 DB/API 資源 | ✅ |
| 環境預置 | 需要特定環境前置條件 | ✅ |
| 短任務 | 總耗時 < 2 分鐘 | ✅ |
| 測試依賴 | 需要前一個測試通過才能進行 | ✅ |

**順序適用範例**：
```yaml
# ✓ 應該順序執行
- TEST-001 → T-F-001      # 測試需先定義，實作需後進行
- T-F-001 → T-I-001       # 實作需先完成，再進行整合
- Setup-DB → Migrate-DB   # 前置環境需順序建立

# ✗ 不應該順序執行（浪費時間）
- TEST-001 → TEST-002 → TEST-003   # 測試無依賴，應並行
- Review-Auth → Review-Profile     # 審查無依賴，應並行
```

---

## 四、Task 工具並行使用語法

### 4.1 基本並行語法

- [ ] **使用 TaskCreate 建立任務**

```javascript
// 方式 1: 逐一建立（順序）
const task1 = TaskCreate({
  subject: "登入測試",
  description: "編寫登入功能測試",
  estimate: 15
});

const task2 = TaskCreate({
  subject: "實作登入",
  description: "實作登入功能",
  estimate: 30,
  addBlockedBy: [task1.id]  // 依賴 task1
});
```

```javascript
// 方式 2: 批量建立（建議用於無依賴任務）
const independentTasks = await Promise.all([
  TaskCreate({
    subject: "登入測試",
    description: "編寫登入功能測試",
    estimate: 15
  }),
  TaskCreate({
    subject: "登出測試",
    description: "編寫登出功能測試",
    estimate: 15
  }),
  TaskCreate({
    subject: "忘記密碼測試",
    description: "編寫忘記密碼功能測試",
    estimate: 15
  })
]);
// 所有任務同時建立，無互相依賴
```

- [ ] **設定依賴關係**

```javascript
// 錯誤：直接建立大量任務但無依賴信息（難以追蹤）
const tasks = await Promise.all([...]);

// 正確：先建立，再明確設定依賴
const testTasks = await Promise.all([
  TaskCreate({ subject: "TEST-001", ... }),
  TaskCreate({ subject: "TEST-002", ... })
]);

const featureTasks = await Promise.all([
  TaskCreate({
    subject: "T-F-001",
    addBlockedBy: [testTasks[0].id]  // 依賴 TEST-001
  }),
  TaskCreate({
    subject: "T-F-002",
    addBlockedBy: [testTasks[1].id]  // 依賴 TEST-002
  })
]);
```

### 4.2 並行執行模式

- [ ] **波次執行（Wave-based）**

```javascript
// 定義波次結構
const waves = {
  wave1: [
    { id: "TEST-001", depends: [] },
    { id: "TEST-002", depends: [] },
    { id: "TEST-003", depends: [] }
  ],
  wave2: [
    { id: "T-F-001", depends: ["TEST-001"] },
    { id: "T-F-002", depends: ["TEST-002"] },
    { id: "T-F-003", depends: ["TEST-003"] }
  ],
  wave3: [
    { id: "T-I-001", depends: ["T-F-001", "T-F-002", "T-F-003"] }
  ]
};

// Wave 1: 並行建立所有測試
const wave1Tasks = await Promise.all(
  waves.wave1.map(task => TaskCreate({
    subject: task.id,
    description: `... ${task.id} ...`,
    estimate: 15
  }))
);

// Wave 2: 依賴 Wave 1 完成
const wave2Tasks = await Promise.all(
  waves.wave2.map((task, idx) => TaskCreate({
    subject: task.id,
    description: `... ${task.id} ...`,
    addBlockedBy: [wave1Tasks[idx].id],
    estimate: 30
  }))
);

// Wave 3: 依賴 Wave 2 完成
const wave3Tasks = await Promise.all(
  waves.wave3.map(task => TaskCreate({
    subject: task.id,
    description: `... ${task.id} ...`,
    addBlockedBy: task.depends.map(depId =>
      wave2Tasks.find(t => t.subject === depId).id
    ),
    estimate: 20
  }))
);
```

- [ ] **DAG 執行（有向無環圖）**

```javascript
// 適用於複雜依賴關係
const tasks = {
  "TEST-001": {},
  "TEST-002": {},
  "T-F-001": { blockedBy: ["TEST-001"] },
  "T-F-002": { blockedBy: ["TEST-001", "TEST-002"] },
  "T-F-003": { blockedBy: ["TEST-002"] },
  "T-I-001": { blockedBy: ["T-F-001", "T-F-002", "T-F-003"] }
};

// 拓撲排序 + 並行建立
const sortedTasks = topologicalSort(tasks);
const createdTasks = {};

for (const layer of sortedTasks) {
  // 同一層可並行建立
  const layerResults = await Promise.all(
    layer.map(taskId => TaskCreate({
      subject: taskId,
      description: `... ${taskId} ...`,
      addBlockedBy: tasks[taskId].blockedBy?.map(depId => createdTasks[depId].id) || []
    }))
  );

  // 記錄結果供下層使用
  layer.forEach((taskId, idx) => {
    createdTasks[taskId] = layerResults[idx];
  });
}
```

### 4.3 跨 Session 並行協作

- [ ] **設定共享任務清單**

```bash
# Session 1: 主協調器
export CLAUDE_CODE_TASK_LIST_ID=auth-feature-workflow

# TaskCreate, TaskUpdate 自動使用相同的 task list
TaskCreate({ subject: "TEST-001", ... })   # → task-list-id: auth-feature-workflow
```

```bash
# Session 2: 子 Agent（不同的 Session）
export CLAUDE_CODE_TASK_LIST_ID=auth-feature-workflow

# 自動連接到同一個任務清單
TaskList()  # → 能看到 Session 1 建立的任務
TaskUpdate({ taskId: "1", status: "in_progress" })  # → 更新共享任務
```

- [ ] **自動依賴解除**

```javascript
// Session 1 建立
TaskCreate({ subject: "TEST-001", id: "1" });
TaskCreate({ subject: "T-F-001", addBlockedBy: ["1"], id: "2" });

// Session 2: TEST-001 完成
TaskUpdate({ taskId: "1", status: "completed" });
// → 系統自動檢查依賴
// → T-F-001 的 blockedBy 自動移除
// → Task List 中 T-F-001 變為可執行（unblocked）
```

---

## 五、常見錯誤和避免方式

### 5.1 依賴分析錯誤

**錯誤 1: 遺漏隱含依賴**

- [ ] ✗ 錯誤做法
```yaml
# 錯誤: 假設任務完全獨立
Task T-F-Auth: depends_on: []
Task T-F-Profile: depends_on: []
Task T-I-Combined: depends_on: []

# 但實際上: 整合需要 Auth 和 Profile 都完成
# 且它們都修改同一個 services/ 目錄
```

- [ ] ✓ 正確做法
```yaml
# 正確: 明確標記隱含依賴
Task T-F-Auth:
  depends_on: [TEST-Auth]
  files: [src/services/auth.ts]

Task T-F-Profile:
  depends_on: [TEST-Profile]
  files: [src/services/profile.ts]

Task T-I-Combined:
  depends_on: [T-F-Auth, T-F-Profile]  # 明確依賴
  files: [src/services/index.ts]  # 整合層
```

**錯誤 2: 誤判並行安全性**

- [ ] ✗ 錯誤做法
```javascript
// 錯誤: 認為「不同功能」就能並行
Promise.all([
  TaskCreate({ subject: "修改 DB Schema", files: ["migrations/001.js"] }),
  TaskCreate({ subject: "執行數據遷移", files: ["migrations/001.js"] })
  // ⚠️ 同一個檔案被修改 → 必須順序執行
]);
```

- [ ] ✓ 正確做法
```javascript
// 正確: 檢查文件和資源衝突
const migration1 = await TaskCreate({
  subject: "建立 users 表",
  files: ["migrations/001.js"]
});

const migration2 = await TaskCreate({
  subject: "執行數據遷移",
  files: ["migrations/002.js"],  // 不同的檔案
  addBlockedBy: [migration1.id]  // 顯式依賴
});
```

### 5.2 並行度配置錯誤

**錯誤 3: 過度並行導致資源耗盡**

- [ ] ✗ 錯誤做法
```javascript
// 錯誤: 一次性建立 100+ 任務同時執行
const allTasks = await Promise.all(
  tasks.map(t => TaskCreate(t))  // 太多並行，可能耗盡連接或內存
);
```

- [ ] ✓ 正確做法
```javascript
// 正確: 按批次執行，控制並行度
async function createTasksWithBatching(tasks, batchSize = 10) {
  const results = [];
  for (let i = 0; i < tasks.length; i += batchSize) {
    const batch = tasks.slice(i, i + batchSize);
    const batchResults = await Promise.all(
      batch.map(t => TaskCreate(t))
    );
    results.push(...batchResults);
  }
  return results;
}

const allTasks = await createTasksWithBatching(tasks, 10);
```

**錯誤 4: 完全串行導致低效率**

- [ ] ✗ 錯誤做法
```javascript
// 錯誤: 無必要地順序建立獨立任務
const t1 = await TaskCreate({ subject: "TEST-001" });
const t2 = await TaskCreate({ subject: "TEST-002" });
const t3 = await TaskCreate({ subject: "TEST-003" });
// 浪費時間，應該並行
```

- [ ] ✓ 正確做法
```javascript
// 正確: 並行建立無依賴任務
const [t1, t2, t3] = await Promise.all([
  TaskCreate({ subject: "TEST-001" }),
  TaskCreate({ subject: "TEST-002" }),
  TaskCreate({ subject: "TEST-003" })
]);
```

### 5.3 循環依賴

**錯誤 5: 創建循環依賴**

- [ ] ✗ 錯誤做法
```yaml
# 錯誤: 形成循環
Task A: depends_on: [B]
Task B: depends_on: [C]
Task C: depends_on: [A]  # ⚠️ 循環！
```

- [ ] ✓ 正確做法
```bash
# 檢查循環依賴
./shared/tools/dag-validator.py tasks.yaml
# 應無輸出（表示無循環）

# 或手動檢查
cat tasks.yaml | grep "depends_on" | sort -u
# 確保無上述循環鏈
```

### 5.4 同步檢查點不足

**錯誤 6: 無法驗證波次完成**

- [ ] ✗ 錯誤做法
```javascript
// 錯誤: 建立大量任務後無法追蹤進度
const tasks = await Promise.all([...]);
// 後續無法知道哪些任務完成、哪些未完成
```

- [ ] ✓ 正確做法
```javascript
// 正確: 在關鍵波次後驗證
const wave1 = await Promise.all([
  TaskCreate({ subject: "TEST-001" }),
  TaskCreate({ subject: "TEST-002" })
]);

// 波次 1 同步檢查點
const wave1Status = await Promise.all(
  wave1.map(t => TaskGet(t.id))
);
if (!wave1Status.every(t => t.status === "completed")) {
  console.error("Wave 1 未完成，停止 Wave 2");
  return;
}

// 波次 2 依賴前提滿足
const wave2 = await Promise.all([
  TaskCreate({ subject: "T-F-001", addBlockedBy: [wave1[0].id] }),
  TaskCreate({ subject: "T-F-002", addBlockedBy: [wave1[1].id] })
]);
```

### 5.5 缺少並行度通知

**錯誤 7: 忘記在計劃中記錄並行機會**

- [ ] ✗ 錯誤做法
```markdown
# implementation-plan.md

## 工作項

1. TEST-001: 登入測試 (15 點)
2. TEST-002: 登出測試 (15 點)
3. TEST-003: 忘記密碼測試 (15 點)
4. T-F-001: 實作登入 (30 點)
5. T-F-002: 實作登出 (30 點)

# ⚠️ 沒有指明哪些可並行，導致執行者逐一進行
```

- [ ] ✓ 正確做法
```markdown
# implementation-plan.md

## 工作項

### Wave 1（可並行，預期 15 分鐘）
- TEST-001: 登入測試 (15 點)
- TEST-002: 登出測試 (15 點)
- TEST-003: 忘記密碼測試 (15 點)

**並行機會**: 三個測試無依賴，可同時執行，建議用 Promise.all()

### Wave 2（依賴 Wave 1 完成，預期 30 分鐘）
- T-F-001: 實作登入 (30 點, 依賴: TEST-001)
- T-F-002: 實作登出 (30 點, 依賴: TEST-002)

**並行機會**: 兩個功能相同層級，可並行，建議用 Promise.all()

## 預期時間

- 串行執行: TEST + Feature = (15 + 30) × 3 = 135 分鐘
- 並行執行: Wave1 + Wave2 = 15 + 30 = 45 分鐘
- **時間節省: 66%**
```

---

## 六、並行執行檢查清單（執行前驗收）

使用此清單在開始並行執行前驗收計劃：

### 6.1 依賴驗收

- [ ] 所有 `depends_on` 都指向真實存在的任務
- [ ] 沒有自身依賴自己的任務
- [ ] 沒有循環依賴（A → B → C → A）
- [ ] 隱含依賴都已明確化（檔案層、語意層、環境層）
- [ ] DAG 驗證通過：`./shared/tools/dag-validator.py tasks.yaml`

### 6.2 並行機會驗收

- [ ] 識別出至少 1 個並行波次（>= 2 個無依賴任務）
- [ ] 計算了最大並行寬度
- [ ] 識別了 Critical Path（決定總時間的路徑）
- [ ] 估算了預期時間節省比例

### 6.3 資源驗收

- [ ] 確認有足夠的 CPU/Memory 承載並行任務
- [ ] 確認沒有資源競爭（同時訪問同一 DB/API/檔案）
- [ ] 確認環境前置條件已準備（DB, Redis 等）
- [ ] 確認並行度設置合理（不超過系統限制）

### 6.4 工具驗收

- [ ] 已使用 TaskCreate 建立任務
- [ ] 已使用 addBlockedBy 設定依賴
- [ ] 已使用 Promise.all() 進行批量並行操作
- [ ] 已設定 CLAUDE_CODE_TASK_LIST_ID 進行跨 Session 協作（如需要）

### 6.5 監控驗收

- [ ] 定義了同步檢查點（Wave 完成後驗證）
- [ ] 準備了監控方式（TaskList/TaskGet）
- [ ] 記錄了預期的完成時間和實際時間對比
- [ ] 準備了失敗恢復方案

---

## 七、並行執行實例

### 案例 1: 多功能並行開發

**場景**: 開發用戶認證系統，包含登入、登出、忘記密碼三個功能

**計劃**:
```yaml
features:
  - feature: login
    tests: [TEST-Auth-Login]
    implementation: T-F-Auth-Login
    integration: T-I-Auth-Complete

  - feature: logout
    tests: [TEST-Auth-Logout]
    implementation: T-F-Auth-Logout

  - feature: forgot_password
    tests: [TEST-Auth-Forgot]
    implementation: T-F-Auth-Forgot
```

**並行結構**:
```
Wave 1 (可並行):
  ├─ TEST-Auth-Login
  ├─ TEST-Auth-Logout
  └─ TEST-Auth-Forgot

Wave 2 (可並行，依賴 Wave 1):
  ├─ T-F-Auth-Login (依賴: TEST-Auth-Login)
  ├─ T-F-Auth-Logout (依賴: TEST-Auth-Logout)
  └─ T-F-Auth-Forgot (依賴: TEST-Auth-Forgot)

Wave 3 (依賴 Wave 2):
  └─ T-I-Auth-Complete (依賴: T-F-Auth-Login, T-F-Auth-Logout, T-F-Auth-Forgot)
```

**時間對比**:
```
串行: 15 + 15 + 15 + 30 + 30 + 30 + 20 = 155 分鐘
並行: 15 (Wave 1) + 30 (Wave 2) + 20 (Wave 3) = 65 分鐘
節省: 58%
```

### 案例 2: 複雜依賴的 DAG 執行

**場景**: 包含測試、實作、審查、驗收的完整流程

**DAG 結構**:
```
TEST-1  TEST-2  TEST-3  TEST-4 (無依賴，並行)
  ↓       ↓       ↓       ↓
IMPL-1  IMPL-2  IMPL-3  IMPL-4 (依賴對應測試，可並行)
  ↓\      ├─────┬────────/
   ╲     ╱      ╲
    REVIEW      (所有實作完成後，並行執行單元測試和審查)
    ↓
 VERIFY        (依賴 REVIEW 和 IMPL-4)
```

**波次分解**:
```
Layer 1: [TEST-1, TEST-2, TEST-3, TEST-4]
Layer 2: [IMPL-1, IMPL-2, IMPL-3, IMPL-4]
Layer 3: [REVIEW, UNIT-TEST]
Layer 4: [VERIFY]
```

**Task 建立邏輯**:
```javascript
// Layer 1 並行建立
const tests = await Promise.all([
  TaskCreate({ subject: "TEST-1" }),
  TaskCreate({ subject: "TEST-2" }),
  TaskCreate({ subject: "TEST-3" }),
  TaskCreate({ subject: "TEST-4" })
]);

// Layer 2 依賴 Layer 1，但可並行
const impls = await Promise.all(
  tests.map((test, idx) =>
    TaskCreate({
      subject: `IMPL-${idx + 1}`,
      addBlockedBy: [test.id]
    })
  )
);

// Layer 3 可並行執行
const [review, unitTest] = await Promise.all([
  TaskCreate({
    subject: "REVIEW",
    addBlockedBy: impls.map(i => i.id)
  }),
  TaskCreate({
    subject: "UNIT-TEST",
    addBlockedBy: impls.map(i => i.id)
  })
]);

// Layer 4 依賴 Layer 3
const verify = await TaskCreate({
  subject: "VERIFY",
  addBlockedBy: [review.id, unitTest.id]
});
```

---

## 八、性能最佳實踐

### 8.1 並行度調整

| 場景 | 建議並行度 | 理由 |
|------|-----------|------|
| 快速測試（< 2 分鐘） | 10-20 | 開銷相對小，可積極並行 |
| 標準任務（2-10 分鐘） | 4-8 | 平衡效率和資源 |
| 長任務（> 10 分鐘） | 2-4 | 資源限制，適度並行 |
| I/O 密集（網絡/磁盤） | 8-16 | I/O 阻塞期間可執行其他 |
| CPU 密集（計算） | CPU 核數 | 避免過度並行 |

### 8.2 資源監控

- [ ] 監控 CPU 使用率（目標: 70-85%）
- [ ] 監控記憶體使用率（目標: < 90%）
- [ ] 監控連接數（確保不超過數據庫連接池限制）
- [ ] 監控磁盤 I/O（避免磁盤瓶頸）

### 8.3 動態調整

```javascript
// 根據系統狀態動態調整並行度
async function intelligentBatching(tasks) {
  let batchSize = 10;  // 初始值

  for (let i = 0; i < tasks.length; i += batchSize) {
    const cpuUsage = getSystemCPUUsage();
    const memUsage = getSystemMemUsage();

    // 動態調整
    if (cpuUsage > 85 || memUsage > 90) {
      batchSize = Math.max(1, batchSize / 2);
    } else if (cpuUsage < 50 && memUsage < 70) {
      batchSize = Math.min(20, batchSize * 1.5);
    }

    const batch = tasks.slice(i, i + batchSize);
    await Promise.all(batch.map(t => TaskCreate(t)));
  }
}
```

---

## 使用指南

1. **計劃階段**: 使用第一、二、三部分分析並識別並行機會
2. **實施前**: 完成第六部分的檢查清單驗收
3. **編碼階段**: 參考第四部分的語法進行 Task 操作
4. **監控階段**: 使用第五部分避免常見錯誤
5. **優化階段**: 參考第八部分調整並行度

---

**最後更新**: 2026-01-27
**版本**: 1.0
**相關文檔**:
- `shared/coordination/map-phase.md` - 並行協調細節
- `shared/tasks/dependency-detection.yaml` - 依賴偵測配置
- `shared/quality/gates.yaml` - 品質閘門標準
