# plugin-dev 視角配置

> 工具型 Skill - 無並行視角

## 說明

plugin-dev 是**工具型 Skill**，不採用 MAP-REDUCE 框架：

- 單一領域操作（Plugin 開發）
- 無需多視角並行分析
- 保持簡單性優先

## 與工作流型 Skill 對比

| 特性 | 工作流型（research/plan） | 工具型（plugin-dev） |
|------|-------------------------|---------------------|
| 並行視角 | 4 個 | 無 |
| MAP-REDUCE | 是 | 否 |
| Context | fork | shared |
| 模型 | sonnet/haiku 混合 | haiku |
| 輸出 | 報告文檔 | 操作結果 |

## 執行模式

plugin-dev 使用單一執行路徑：

```
用戶輸入 → 命令解析 → Python CLI → 結果輸出
```

無需視角分派或結果匯總。

## 相關配置

視角設定：不適用

命令配置：`config/commands.yaml`
