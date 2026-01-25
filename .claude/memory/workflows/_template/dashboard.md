# 🎯 工作流執行報告

## 基本資訊

| 項目 | 內容 |
|------|------|
| **工作流 ID** | {workflow_id} |
| **任務** | {task_name} |
| **開始時間** | {start_time} |
| **結束時間** | {end_time} |
| **狀態** | {status} |
| **品質分數** | {quality_score}/100 |

## 執行摘要

```
{stage_flow_diagram}
```

## 關鍵決策

{decisions_list}

## 品質指標

| 指標 | 數值 | 狀態 |
|------|------|------|
| TDD 遵循率 | {tdd_rate}% | {tdd_status} |
| 測試覆蓋率 | {coverage}% | {coverage_status} |
| 安全檢查 | {security_result} | {security_status} |
| 回退次數 | {rollback_count} | {rollback_status} |

## 資源使用

| 資源 | 使用量 |
|------|--------|
| Token | {token_count} |
| API 成本 | ${api_cost} |
| Agents | {agent_count} 個 |
| Tools | {tool_count} 次 |

## 詳細報告連結

- [完整時間線](./timeline.md)
- [所有決策](./decisions.md)
- [品質報告](./quality-report.md)
