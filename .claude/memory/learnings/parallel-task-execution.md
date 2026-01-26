# 並行任務執行最佳實踐

**日期**: 2026-01-27
**主題**: Task 工具並行能力的正確使用方法
**優先級**: HIGH - 影響工作流效率

## 問題描述

在執行測試計劃或任務分解時，存在以下反模式：

- **症狀**: 依序執行了本可並行的任務，導致整體耗時翻倍
- **根本原因**:
  1. 習慣性順序思維模式
  2. 沒有主動分析任務間的依賴關係
  3. 使用 Write 工具逐一執行任務，而非利用 Task 工具系統

**具體案例**: 執行多個獨立的測試用例或驗證步驟時，按 case 1 → case 2 → case 3 順序依次執行，而不是並行啟動它們。

## 根本原因分析

| 原因 | 影響 | 解決方案 |
|------|------|--------|
| 習慣性順序編程 | 無法識別並行機會 | 先分析依賴關係圖 |
| 缺乏並行模式認知 | 不知道如何啟動並行任務 | 學習單個 message 中多個 Task 呼叫 |
| 直接使用工具 | 無法跟蹤和管理任務生命週期 | 統一使用 Task 工具系統 |

## 正確做法

### 1. 識別任務依賴關係

```
分析每個任務的前置條件：
- 任務 A 必須在任務 B 之前完成？
- 任務 B 和 C 是否無依賴？
- 形成依賴圖：A → B → C（順序）vs A, B, C（並行）
```

### 2. 在單一 Message 中發送多個 Task 呼叫

**錯誤做法**（順序執行）：
```
Message 1: TaskCreate({...}) → 任務 1
[等待 TaskCreate 完成]
Message 2: TaskCreate({...}) → 任務 2
[等待 TaskCreate 完成]
Message 3: TaskCreate({...}) → 任務 3
```

**正確做法**（並行執行）：
```
Message 1 同時包含：
  - TaskCreate({...}) → 任務 1
  - TaskCreate({...}) → 任務 2
  - TaskCreate({...}) → 任務 3
[所有任務並行執行]
```

### 3. 建立任務依賴關係

```yaml
# 無依賴 - 可完全並行
TaskCreate({
  subject: "測試用例 1",
  description: "驗證功能 A"
})

TaskCreate({
  subject: "測試用例 2",
  description: "驗證功能 B"
})

TaskCreate({
  subject: "測試用例 3",
  description: "驗證功能 C"
})

---

# 有依賴 - 需要順序執行
TaskCreate({
  subject: "初始化數據",
  description: "準備測試環境"
})
# → taskId: 1

TaskCreate({
  subject: "運行主測試",
  description: "依賴初始化完成",
  addBlockedBy: ["1"]  # 等待任務 1 完成
})
```

### 4. 使用 run_in_background 優化長時間任務

```javascript
// 對於耗時較長的任務，使用 run_in_background: true
Bash({
  command: "npm test -- --coverage",
  run_in_background: true,
  description: "運行完整測試套件（可後台執行）"
})

// 同時執行其他操作而不等待
Bash({
  command: "npm run lint",
  description: "進行程式碼檢查"
})
```

## 關鍵洞察

### 並行邊界

**完全並行的條件**：
- 任務 A 和 B 沒有數據依賴
- 任務 A 的輸出不作為任務 B 的輸入
- 任務 B 不需要等待任務 A 的結果

**必須順序的情況**：
- 任務 B 依賴任務 A 的輸出（`addBlockedBy`）
- 任務 A 修改全局狀態，任務 B 依賴此狀態
- 任務 A 和 B 共享臨界資源（如文件寫入）

### Task 工具的真正價值

- **Task 系統並非順序執行工具** - 它是 **并发任務管理框架**
- 單個 message 中的多個 TaskCreate 呼叫會 **並行啟動**
- 依賴關係（`addBlockedBy`）定義執行順序，不影響其他無依賴任務
- Task 狀態機管理生命週期，避免重複執行或死鎖

## 實際應用

### 場景 1：多視角並行研究

```javascript
// 4 個研究視角可以完全並行執行
TaskCreate({
  subject: "架構視角研究",
  description: "分析系統結構"
})

TaskCreate({
  subject: "認知視角研究",
  description: "分析方法論"
})

TaskCreate({
  subject: "工作流視角研究",
  description: "分析執行流程"
})

TaskCreate({
  subject: "業界視角研究",
  description: "分析最佳實踐"
})
```

### 場景 2：測試計劃執行

```javascript
// 獨立的測試套件可以並行執行
TaskCreate({
  subject: "單元測試",
  description: "運行 unit 測試"
})

TaskCreate({
  subject: "集成測試",
  description: "運行 integration 測試"
})

TaskCreate({
  subject: "端到端測試",
  description: "運行 e2e 測試"
})

TaskCreate({
  subject: "性能測試",
  description: "運行性能基準測試"
})
```

### 場景 3：有序測試計劃

```javascript
// 初始化任務必須先執行
TaskCreate({
  subject: "環境初始化",
  description: "準備測試環境"
})
// → taskId: 1

// 這些測試都依賴初始化，但彼此獨立
TaskCreate({
  subject: "功能測試 A",
  description: "測試模塊 A",
  addBlockedBy: ["1"]
})

TaskCreate({
  subject: "功能測試 B",
  description: "測試模塊 B",
  addBlockedBy: ["1"]
})

TaskCreate({
  subject: "功能測試 C",
  description: "測試模塊 C",
  addBlockedBy: ["1"]
})
```

## 檢查清單

在執行任務時，使用此清單確保最優效率：

- [ ] 是否識別了所有任務？
- [ ] 是否分析了任務間的依賴關係？
- [ ] 是否識別了可並行的任務？
- [ ] 是否在單一 message 中創建了所有無依賴的任務？
- [ ] 是否為有依賴的任務設置了 `addBlockedBy`？
- [ ] 是否為長耗時任務使用了 `run_in_background`？
- [ ] 是否監控了 TaskList 確保進度？

## 相關資源

- [Task 工具文檔](./../../task-tools-reference.md)
- [多視角並行執行](./../../shared/coordination/map-phase.md)
- [執行模式配置](./../../shared/config/execution-profiles.yaml)

## 學習來源

**學習日期**: 2026-01-27
**觸發事件**: 執行測試計劃時發現順序執行的性能問題
**改進效果**: 預期可減少 50-70% 的總執行時間（取決於任務依賴分佈）
