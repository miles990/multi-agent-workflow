# Troubleshooting 指南

> Multi-Agent Workflow 錯誤排除文檔索引

## 概述

本目錄包含所有錯誤碼的詳細排除指南。每個錯誤碼都有對應的文檔，提供：
- 詳細說明
- 常見場景
- 解決步驟
- 預防措施

## 錯誤碼索引

### E-AGT: Agent 執行錯誤

| 錯誤碼 | 名稱 | 文檔 |
|--------|------|------|
| [E-AGT-001](./E-AGT-001.md) | Agent 超時 | ✅ |
| [E-AGT-002](./E-AGT-002.md) | Agent 格式錯誤 | ✅ |
| E-AGT-003 | Agent 衝突 | - |
| E-AGT-004 | Agent 啟動失敗 | - |
| E-AGT-005 | Agent 崩潰 | - |

### E-WKF: Workflow 流程錯誤

| 錯誤碼 | 名稱 | 文檔 |
|--------|------|------|
| [E-WKF-001](./E-WKF-001.md) | 回退超限 | ✅ |
| [E-WKF-002](./E-WKF-002.md) | 階段缺失 | ✅ |
| E-WKF-003 | 依賴缺失 | - |
| E-WKF-004 | 階段順序錯誤 | - |

### E-MEM: Memory 存取錯誤

| 錯誤碼 | 名稱 | 文檔 |
|--------|------|------|
| [E-MEM-001](./E-MEM-001.md) | 讀取失敗 | ✅ |
| E-MEM-002 | 寫入失敗 | - |
| E-MEM-003 | 寫入衝突 | - |

### E-USR: User 輸入錯誤

| 錯誤碼 | 名稱 | 文檔 |
|--------|------|------|
| [E-USR-001](./E-USR-001.md) | 參數錯誤 | ✅ |
| E-USR-002 | 缺少輸入 | - |

### E-GIT: Git 操作錯誤

| 錯誤碼 | 名稱 | 文檔 |
|--------|------|------|
| [E-GIT-001](./E-GIT-001.md) | Worktree 建立失敗 | ✅ |
| E-GIT-003 | 合併衝突 | - |

## 快速診斷

### 常見問題排查流程

```
錯誤發生
    ↓
記下錯誤碼（E-XXX-NNN）
    ↓
查閱對應文檔
    ↓
按照「快速修復」步驟嘗試
    ↓
若仍未解決，參考「深入分析」
    ↓
若需要幫助，提供錯誤日誌尋求支援
```

### 日誌收集

遇到問題時，請收集以下資訊：

```bash
# 1. 錯誤訊息完整內容
# 2. 工作流 ID
# 3. 相關 Memory 檔案
ls -la .claude/memory/metrics/{workflow-id}/

# 4. Git 狀態
git status
git log --oneline -5
```

## 取得協助

如果本文檔無法解決您的問題：

1. 確認已閱讀對應的錯誤碼文檔
2. 收集完整的錯誤日誌
3. 在 GitHub Issues 提交問題報告

## 相關資源

- [錯誤碼定義](../../shared/errors/error-codes.md)
- [錯誤格式化](../../shared/errors/formatter.md)
- [進度顯示](../../shared/progress/display.md)
