# Claude Code Plugin 設計模式最佳實踐 - 匯總報告

## 摘要

多視角研究確認了 Claude Code Plugin 設計的 4 個核心原則：模組化共用設計、零依賴架構、Map-Reduce 並行框架、視角驅動設計。

## 方法

- **視角**：架構分析師、業界實踐研究員
- **日期**：2025-01-24
- **模式**：quick（2 視角）

## 強共識 (★★★★)

### 1. 模組化共用設計
Plugin 應將可重用邏輯提取到 shared/ 目錄：
- coordination/ - Map-Reduce 協調
- synthesis/ - 交叉驗證 + 矛盾解決
- perspectives/ - 視角定義

### 2. 零依賴架構
只依賴 Claude Code 內建工具：
- Task API（並行執行）
- 檔案系統（Memory 存儲）
- 內建工具（WebSearch、Bash、Git）

### 3. Map-Reduce 並行框架
標準 6 階段執行流程：
1. 目標錨定
2. Memory 搜尋
3. 視角分解
4. MAP（並行執行）
5. REDUCE（整合匯總）
6. Memory 存檔

### 4. 視角驅動設計
每個視角定義：id、name、role、focus_areas、research_method、priority_weight

## 獨特洞察

- **架構分析師**：Worktree 隔離設計確保 main 分支穩定
- **業界實踐**：Skills 與 MCP 分離、Hook 作為品質閘門

## 行動建議

1. 新增 Skill 遵循標準結構（SKILL.md + 00-quickstart + 01-perspectives）
2. 聲明使用共用模組而非重複實作
3. 使用 Hooks 作為品質閘門
4. 補充自動化測試
