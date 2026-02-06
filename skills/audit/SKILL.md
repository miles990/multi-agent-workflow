---
name: audit
version: 1.0.0
description: 跨子系統架構一致性審查 - 利用多視角並行分析架構健康度
triggers: [audit, architecture-audit, 架構審查]
context: shared
allowed-tools: [Read, Grep, Glob, Bash, Write, Task]
model: sonnet
---

# Audit v1.0.0

> 跨子系統架構一致性審查 -- 多視角並行分析架構健康度，識別不一致和技術債務

## 用途

對 codebase 進行全面的架構健康度審查，識別：
- 依賴方向違反（下層依賴上層）
- 命名不一致
- 錯誤處理模式不統一
- 橫切關注點缺失（logging、metrics、error handling）
- 代碼重複與 DRY 違反
- 測試覆蓋率缺口

## 使用方式

```bash
/audit [目標路徑或模組]
/audit src/api/              # 審查 API 模組
/audit src/                  # 審查 src 整體
/audit --full                # 全面審查（整個 codebase）
```

**Flags**: `--full` | `--focus deps|patterns|tests|docs` | `--quick` | `--deep`

## 預設 4 視角

| ID | 名稱 | 模型 | 聚焦 |
|----|------|------|------|
| `dependency-auditor` | 依賴分析師 | sonnet | import/require 掃描、循環依賴、方向違反 |
| `pattern-checker` | 模式一致性檢查員 | haiku | 錯誤處理、命名慣例、API 介面風格 |
| `coverage-auditor` | 測試覆蓋分析師 | haiku | 缺少測試的模組、測試品質、mock 濫用 |
| `doc-sync-checker` | 文檔同步檢查員 | haiku | 代碼與文檔比對、過時文檔、API 文檔完整性 |

-> 模型路由配置：[shared/config/model-routing.yaml](../../shared/config/model-routing.yaml)

## 執行流程

```
Phase 0: 收集目標 -> 確定審查範圍、掃描目標路徑
    |
Phase 1: MAP（並行審查）
    +-------------+----------------+----------------+----------------+
    | 依賴分析師  | 模式一致性     | 測試覆蓋       | 文檔同步       |
    | (sonnet)    | 檢查員 (haiku) | 分析師 (haiku) | 檢查員 (haiku) |
    +-------------+----------------+----------------+----------------+

    ** 並行執行關鍵 **：
       在單一訊息中發送 4 個 Task 工具呼叫：
       - Task({description: "依賴方向審查", ...})
       - Task({description: "模式一致性檢查", ...})
       - Task({description: "測試覆蓋分析", ...})
       - Task({description: "文檔同步檢查", ...})

    ** 強制 **：每個 Agent 完成前必須執行：
       1. mkdir -p .claude/memory/audit/{audit-id}/perspectives/
       2. Write -> .claude/memory/audit/{audit-id}/perspectives/{perspective_id}.md
       未執行 Write = 任務失敗
    |
Phase 2: REDUCE（問題匯總）
    +-- 問題分類（CRITICAL/HIGH/MEDIUM/LOW）
    +-- 按嚴重度排序
    +-- 修復建議
    |
Phase 3: 產出審查報告
```

## 問題分類

| 級別 | 定義 | 處理 |
|------|------|------|
| CRITICAL | 架構缺陷，可能導致系統故障 | 立即修復 |
| HIGH | 一致性違反，影響可維護性 | 限時修復 |
| MEDIUM | 建議改善，提升品質 | 記錄追蹤 |
| LOW | 風格建議或小改進 | 可選 |

## 輸出結構

```
.claude/memory/audit/{audit-id}/
+-- meta.yaml               # 元數據（審查範圍、時間、配置）
+-- perspectives/            # 完整視角報告（MAP 產出）
|   +-- dependency-auditor.md
|   +-- pattern-checker.md
|   +-- coverage-auditor.md
|   +-- doc-sync-checker.md
+-- issues.yaml              # 問題清單（按嚴重度排序）
+-- audit-summary.md         # 審查摘要 + 建議（主輸出）
```

> perspectives/ 保存各視角的完整分析報告，issues.yaml 匯總所有問題。

## Agent 能力限制

**審查 Agent 不應該開啟 Task**：

| 允許的操作 | 說明 |
|-----------|------|
| Read | 讀取程式碼和配置 |
| Glob/Grep | 搜尋檔案和內容模式 |
| Bash | 執行分析命令（如 dependency graph） |
| Write | 寫入審查報告 |
| ~~Task~~ | 不允許開子 Agent |

## 視角 Prompt 指引

### 視角 1: 依賴分析師 (dependency-auditor)

**目標**：掃描 import/require 語句，繪製依賴關係，識別問題。

**檢查項目**：
1. 掃描所有 import/require/from...import 語句
2. 識別模組間依賴方向（上層不應依賴下層的具體實現）
3. 檢測循環依賴
4. 識別過度耦合的模組（依賴數超過閾值）
5. 檢查是否有跨層依賴違反

**輸出格式**：
- 依賴圖摘要（文字描述）
- 問題列表（含檔案路徑、行號、嚴重度）
- 建議的重構方向

### 視角 2: 模式一致性檢查員 (pattern-checker)

**目標**：檢查 codebase 中的模式一致性。

**檢查項目**：
1. 錯誤處理模式（統一 try-catch 風格、自定義錯誤類型使用）
2. 命名慣例（變數、函數、類別、檔案命名）
3. API 介面風格（REST 路由命名、請求/回應格式）
4. 日誌記錄模式（logger 使用一致性）
5. 配置存取模式（環境變數 vs 配置檔案）

**輸出格式**：
- 每種模式的一致性評分
- 不一致的具體案例（含檔案路徑、行號）
- 建議的統一標準

### 視角 3: 測試覆蓋分析師 (coverage-auditor)

**目標**：找出測試覆蓋缺口，評估測試品質。

**檢查項目**：
1. 找出沒有對應測試的模組
2. 評估現有測試的品質（是否只測試 happy path）
3. 識別 mock/stub 濫用（過度 mock 導致測試失去意義）
4. 檢查邊界條件測試覆蓋
5. 評估整合測試 vs 單元測試比例

**輸出格式**：
- 未覆蓋模組列表
- 測試品質評估
- 建議新增的測試案例

### 視角 4: 文檔同步檢查員 (doc-sync-checker)

**目標**：確保文檔與代碼同步。

**檢查項目**：
1. 比對 README/CLAUDE.md 中描述的功能與實際代碼
2. 檢查 API 文檔與實際 endpoint 是否一致
3. 識別過時的文檔（提到已刪除的模組/函數）
4. 檢查配置文檔完整性（所有環境變數是否有文檔）
5. 確認命令文檔與實際可用命令一致

**輸出格式**：
- 文檔 vs 代碼差異清單
- 過時文檔列表
- 缺失文檔建議

## CP4: Task Commit

審查完成後執行 Task Commit：

```
Phase 3: 審查報告產出
    |
CP4: Task Commit
    +-- git add .claude/memory/audit/{audit-id}/
    +-- git commit -m "docs(audit): complete architecture audit for {target}"
```

-> 協議：[shared/git/commit-protocol.md](../../shared/git/commit-protocol.md)

## 共用模組

| 模組 | 用途 |
|------|------|
| [coordination/map-phase.md](../../shared/coordination/map-phase.md) | 並行協調 |
| [coordination/reduce-phase.md](../../shared/coordination/reduce-phase.md) | 匯總整合 |
| [perspectives/catalog.yaml](../../shared/perspectives/catalog.yaml) | 視角定義 |

## 工作流位置

```
RESEARCH -> PLAN -> TASKS -> IMPLEMENT -> REVIEW -> VERIFY
                                                        |
                                              AUDIT <---+
                                         (獨立工具，隨時可用)
```

- **輸入**：目標路徑或模組名稱
- **輸出**：架構審查報告，可供 PLAN 或 IMPLEMENT 參考
- **定位**：獨立的架構健康檢查工具，不屬於固定工作流階段，隨時可執行
