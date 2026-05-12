# 錯誤碼定義

> 標準化錯誤分類和編碼系統

## 概述

錯誤碼系統提供一致的錯誤識別和分類方式，方便問題診斷和解決。

## 錯誤碼格式

```
E-{類別}-{編號}

範例：E-AGT-001
```

### 組成部分

| 部分 | 說明 | 範例 |
|------|------|------|
| E | 錯誤前綴 | E |
| 類別 | 錯誤分類（3 字母） | AGT, WKF, MEM, USR |
| 編號 | 流水號（3 位數） | 001, 002, ... |

## 錯誤分類

### E-AGT: Agent 執行錯誤

與 Agent（視角）執行相關的錯誤。

| 錯誤碼 | 名稱 | 說明 | 嚴重度 |
|--------|------|------|--------|
| E-AGT-001 | Agent 超時 | Agent 執行超過時間限制 | HIGH |
| E-AGT-002 | Agent 格式錯誤 | Agent 輸出格式不符預期 | MEDIUM |
| E-AGT-003 | Agent 衝突 | 多個 Agent 輸出互相矛盾 | MEDIUM |
| E-AGT-004 | Agent 啟動失敗 | 無法啟動 Agent 任務 | HIGH |
| E-AGT-005 | Agent 崩潰 | Agent 執行中異常終止 | HIGH |
| E-AGT-006 | Agent 輸出為空 | Agent 未產生任何輸出 | MEDIUM |
| E-AGT-007 | Agent 重試失敗 | Agent 重試次數耗盡 | HIGH |
| E-AGT-008 | Agent 資源不足 | Agent 執行資源超限 | HIGH |

### E-WKF: Workflow 流程錯誤

與工作流邏輯相關的錯誤。

| 錯誤碼 | 名稱 | 說明 | 嚴重度 |
|--------|------|------|--------|
| E-WKF-001 | 回退超限 | 回退次數超過上限 | CRITICAL |
| E-WKF-002 | 階段缺失 | 必要階段未執行 | HIGH |
| E-WKF-003 | 依賴缺失 | 階段依賴的輸入不存在 | HIGH |
| E-WKF-004 | 階段順序錯誤 | 階段執行順序不正確 | HIGH |
| E-WKF-005 | 工作流中斷 | 工作流非正常終止 | HIGH |
| E-WKF-006 | 狀態不一致 | 工作流狀態與預期不符 | MEDIUM |
| E-WKF-007 | 迭代超限 | 總迭代次數超過上限 | HIGH |
| E-WKF-008 | 無效起點 | 無法判斷工作流起始階段 | MEDIUM |

### E-MEM: Memory 存取錯誤

與 Memory 系統相關的錯誤。

| 錯誤碼 | 名稱 | 說明 | 嚴重度 |
|--------|------|------|--------|
| E-MEM-001 | 讀取失敗 | 無法讀取 Memory 檔案 | HIGH |
| E-MEM-002 | 寫入失敗 | 無法寫入 Memory 檔案 | HIGH |
| E-MEM-003 | 寫入衝突 | 多個進程同時寫入 | MEDIUM |
| E-MEM-004 | 格式錯誤 | Memory 檔案格式無效 | MEDIUM |
| E-MEM-005 | 路徑不存在 | Memory 目錄不存在 | MEDIUM |
| E-MEM-006 | 權限錯誤 | 無權限存取 Memory | HIGH |
| E-MEM-007 | 空間不足 | 儲存空間不足 | HIGH |
| E-MEM-008 | 索引損壞 | Memory 索引檔案損壞 | HIGH |

### E-USR: User 輸入錯誤

與使用者輸入相關的錯誤。

| 錯誤碼 | 名稱 | 說明 | 嚴重度 |
|--------|------|------|--------|
| E-USR-001 | 參數錯誤 | 命令參數格式不正確 | LOW |
| E-USR-002 | 缺少輸入 | 必要參數未提供 | LOW |
| E-USR-003 | 無效選項 | 使用了不支援的選項 | LOW |
| E-USR-004 | 路徑無效 | 指定的檔案/目錄不存在 | LOW |
| E-USR-005 | 格式不符 | 輸入內容格式不正確 | LOW |
| E-USR-006 | 權限不足 | 使用者無權限執行操作 | MEDIUM |
| E-USR-007 | 操作取消 | 使用者取消操作 | LOW |
| E-USR-008 | 確認失敗 | 需要使用者確認但未確認 | LOW |

### E-GIT: Git 操作錯誤

與 Git/Worktree 相關的錯誤。

| 錯誤碼 | 名稱 | 說明 | 嚴重度 |
|--------|------|------|--------|
| E-GIT-001 | Worktree 建立失敗 | 無法建立 Git Worktree | HIGH |
| E-GIT-002 | 分支衝突 | 分支名稱已存在 | MEDIUM |
| E-GIT-003 | 合併衝突 | 合併時發生衝突 | HIGH |
| E-GIT-004 | 提交失敗 | Git commit 失敗 | HIGH |
| E-GIT-005 | Worktree 清理失敗 | 無法清理 Worktree | MEDIUM |
| E-GIT-006 | 非 Git 倉庫 | 當前目錄不是 Git 倉庫 | HIGH |
| E-GIT-007 | 髒工作區 | 工作區有未提交的變更 | MEDIUM |
| E-GIT-008 | 遠端同步失敗 | 無法與遠端同步 | MEDIUM |

### E-ENV: 環境錯誤

與執行環境相關的錯誤。

| 錯誤碼 | 名稱 | 說明 | 嚴重度 |
|--------|------|------|--------|
| E-ENV-001 | 依賴缺失 | 系統缺少必要依賴 | HIGH |
| E-ENV-002 | 版本不相容 | 工具版本不符要求 | MEDIUM |
| E-ENV-003 | 配置錯誤 | 環境配置不正確 | MEDIUM |
| E-ENV-004 | 網路錯誤 | 網路連接問題 | HIGH |
| E-ENV-005 | 資源限制 | 系統資源不足 | HIGH |
| E-ENV-006 | 權限問題 | 系統權限不足 | HIGH |

## 嚴重度定義

| 嚴重度 | 說明 | 自動處理 | 需人工介入 |
|--------|------|----------|------------|
| CRITICAL | 工作流無法繼續 | 否 | 是 |
| HIGH | 重大問題，可能需要人工處理 | 可能 | 可能 |
| MEDIUM | 一般問題，通常可自動恢復 | 是 | 否 |
| LOW | 輕微問題，不影響執行 | 是 | 否 |

## 錯誤碼使用

### 在程式碼中引用

```yaml
error:
  code: "E-AGT-001"
  title: "Agent 超時"
  stage: "implement"
  perspective: "tdd-enforcer"
  message: "TDD 守護者執行超過 5 分鐘未完成"
  timestamp: "2026-01-24T10:30:00Z"
```

### 在日誌中記錄

```
[ERROR] E-AGT-001: Agent 超時
  階段: IMPLEMENT
  視角: tdd-enforcer
  詳情: TDD 守護者執行超過 5 分鐘未完成
  時間: 2026-01-24T10:30:00Z
```

### 在報告中顯示

```markdown
## 錯誤紀錄

| 時間 | 錯誤碼 | 說明 | 處理 |
|------|--------|------|------|
| 10:30 | E-AGT-001 | Agent 超時 | 自動重試 |
| 10:35 | E-WKF-001 | 回退超限 | 人工介入 |
```

## 錯誤碼查詢

### 文檔連結

每個錯誤碼都有對應的詳細文檔：

```
docs/troubleshooting/E-AGT-001.md
docs/troubleshooting/E-WKF-001.md
...
```

### 快速查詢

```bash
# 查詢錯誤碼說明
/multi-orchestrate --error-help E-AGT-001
```

## 錯誤碼擴展

### 新增錯誤碼規則

1. 使用正確的類別前綴
2. 使用下一個可用編號
3. 更新本文檔
4. 建立對應的 troubleshooting 文檔

### 類別預留

| 前綴 | 範圍 | 說明 |
|------|------|------|
| E-AGT | 001-099 | Agent 相關 |
| E-WKF | 001-099 | Workflow 相關 |
| E-MEM | 001-099 | Memory 相關 |
| E-USR | 001-099 | 使用者輸入相關 |
| E-GIT | 001-099 | Git 相關 |
| E-ENV | 001-099 | 環境相關 |
| E-INT | 001-099 | 內部錯誤（預留） |

## 相關模組

- [錯誤格式化](./formatter.md)
- [Troubleshooting 文檔](../../docs/troubleshooting/)
- [進度顯示](../progress/display.md)
