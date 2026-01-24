# Evolve Checkpoints Integration（共用模組）

> 與 evolve Skill 的 Checkpoint 機制整合

## 概述

Multi-Agent Workflow 的執行流程與 evolve Checkpoint 對應，確保在關鍵時刻執行必要的檢查。

**此為共用模組**，定義所有 skill 共用的 Checkpoint 對應。

## Checkpoint 對應總表

| Skill | Phase | evolve CP | 動作 |
|-------|-------|-----------|------|
| **research** | Phase 1: Memory 搜尋 | CP1 | 搜尋 .claude/memory/ |
| **research** | Phase 5: 匯總完成 | CP3 | 確認目標達成 |
| **research** | Phase 6: Memory 存檔 | CP3.5 | 同步 index.md |
| **plan** | Phase 1: Memory 搜尋 | CP1 | 搜尋相關計劃 |
| **plan** | Phase 3: 共識設計 | CP1.5 | 設計一致性檢查 |
| **plan** | Phase 4: 存檔 | CP3.5 | 同步 index.md |
| **implement** | Phase 1: 環境檢查 | CP1 | 搜尋相關實作 |
| **implement** | Phase 3: 整合驗證 | CP2 | Build + Test |
| **implement** | Phase 4: 存檔 | CP3.5 | 同步 index.md |
| **review** | Phase 0: 變更載入 | CP1 | 搜尋相關審查 |
| **review** | Phase 2: 問題整合 | CP3 | 審查共識達成 |
| **review** | Phase 3: 存檔 | CP3.5 | 同步 index.md |
| **verify** | Phase 0: 驗收準備 | CP1 | 載入相關記錄 |
| **verify** | Phase 2: 結果整合 | CP2 | 測試執行 |
| **verify** | Phase 3: 發布許可 | CP6 | 發布驗證 |

## CP0: 北極星錨定

### 時機

任務開始前（由 orchestrator 觸發）

### 動作

```markdown
## 北極星：{任務主題}

### 目標
- 主要問題：{核心問題}
- 期望輸出：{輸出類型}

### 成功標準
- [ ] 標準 1
- [ ] 標準 2

### 範圍
- 包含：{範圍內項目}
- 排除：{範圍外項目}
```

## CP1: Memory 搜尋

### 時機

每個 skill 開始處理前

### 動作

```bash
# 搜尋相關記錄
ls .claude/memory/{skill-type}/

# 搜尋關鍵字
grep -r "{topic}" .claude/memory/
```

### 發現相關記錄時

```
> 發現相關記錄：
>   1. {record-id-1} ({date})
>   2. {record-id-2} ({date})
>
> 選項：
>   1. 復用並補充
>   2. 從頭開始
>   3. 取消
```

## CP1.5: 一致性檢查

### 時機

plan skill 設計完成時

### Phase 1: 基礎檢查

- 搜尋現有實作，避免重複
- 檢查專案慣例（命名、風格）
- 檢查 Schema/API 一致性

### Phase 2: 架構檢查（自動觸發）

觸發條件：
- 新增目錄/模組
- 變更涉及 3+ 目錄
- 新增外部依賴
- 觸及 core/infra/domain/shared/
- 新增公開 API

## CP2: Build + Test

### 時機

implement 或 verify 進行測試時

### 動作

```bash
# 編譯檢查
npm run build  # 或對應的編譯命令

# 測試執行
npm test       # 或對應的測試命令
```

### 失敗處理

```markdown
## CP2 失敗報告

### 失敗類型
編譯錯誤 / 測試失敗

### 錯誤訊息
{error_message}

### 相關檔案
- {file_path}

### 建議修復
1. {suggestion_1}
2. {suggestion_2}
```

## CP3: 目標確認

### 時機

research 或 review 完成主要工作後

### 動作

對照北極星檢查：

```markdown
## 完成度檢查

### 對照北極星
- [x] 達成標準 1
- [x] 達成標準 2
- [ ] 達成標準 3（部分完成）

### 評估
{完成度評估}

### 決策
- 繼續：存檔並結束
- 深化：針對未完成項目進行額外工作
```

## CP3.5: Memory 存檔

### 時機

任何 skill 產出 Memory 文件後

### 動作

1. 建立目錄結構
2. 存儲所有報告
3. **立即**更新 index.md

### 目錄結構範例

```
.claude/memory/{skill-type}/[topic-id]/
├── meta.yaml
├── overview.md
├── perspectives/
│   └── {perspective}.md
└── {primary-output}.md
```

### 更新 index.md

```markdown
## {skill-type}/

| ID | 主題 | 日期 | 狀態 |
|----|------|------|------|
| {topic-id} | {topic} | {date} | completed |
```

## CP5: 失敗驗屍

### 時機

implement 的 pass@k 失敗時

### 動作

```markdown
## 失敗驗屍報告

### 失敗摘要
- 嘗試次數：{k}
- 失敗模式：{pattern}

### 根因分析
{root_cause}

### Lesson Learned
{lessons}

### 建議行動
1. {action_1}
2. {action_2}
```

## CP6: 發布驗證

### 時機

verify 完成所有測試後

### 動作

```markdown
## 發布驗證

### 測試結果
| 類型 | 通過率 | 要求 | 狀態 |
|------|--------|------|------|
| 功能測試 | 100% | 100% | ✅ |
| 邊界測試 | 95% | 90% | ✅ |
| 回歸測試 | 100% | 100% | ✅ |
| 驗收測試 | 100% | 100% | ✅ |

### 發布決策
✅ SHIP IT 或 ❌ BLOCKED

### 理由
{decision_rationale}
```

## 降級處理

如果不在 evolve 環境中執行：
- 跳過 evolve 特定檢查
- 仍執行核心工作流
- Memory 存檔仍然執行
