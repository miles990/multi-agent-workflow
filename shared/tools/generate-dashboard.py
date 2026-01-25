#!/usr/bin/env python3
"""
Dashboard 生成器 - 生成工作流執行報告 Dashboard
用法: python generate-dashboard.py <output_dir>
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

def load_workflow_data(output_dir: str) -> dict:
    """載入工作流數據"""
    data = {
        'workflow_id': os.path.basename(output_dir),
        'task_name': '未知任務',
        'start_time': datetime.now().isoformat(),
        'end_time': datetime.now().isoformat(),
        'status': '完成',
        'quality_score': 0,
        'decisions': [],
        'metrics': {},
        'resources': {}
    }

    # 嘗試載入 metadata
    metadata_file = os.path.join(output_dir, 'metadata.json')
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
            data.update(loaded)

    return data

def generate_stage_flow(data: dict) -> str:
    """生成階段流程圖"""
    stages = ['RESEARCH', 'PLAN', 'TASKS', 'IMPLEMENT', 'REVIEW', 'VERIFY']
    stage_status = data.get('stage_status', {})

    flow_parts = []
    for stage in stages:
        status = stage_status.get(stage, 'pending')
        if status == 'completed':
            flow_parts.append(f"{stage} ✅")
        elif status == 'failed':
            flow_parts.append(f"{stage} ❌")
        elif status == 'in_progress':
            flow_parts.append(f"{stage} ⏳")
        else:
            flow_parts.append(f"{stage} ⬜")

    return ' ─→ '.join(flow_parts)

def format_decisions(decisions: list) -> str:
    """格式化決策列表"""
    if not decisions:
        return "（暫無決策記錄）"

    lines = []
    for i, dec in enumerate(decisions, 1):
        status = dec.get('status', '✅')
        desc = dec.get('description', dec.get('decision', ''))
        lines.append(f"{i}. {status} {desc}")

    return '\n'.join(lines)

def format_metrics(metrics: dict) -> str:
    """格式化指標表格"""
    rows = []

    default_metrics = {
        'TDD 遵循率': {'value': '-', 'status': '⬜'},
        '測試覆蓋率': {'value': '-', 'status': '⬜'},
        '安全檢查': {'value': '-', 'status': '⬜'},
        '回退次數': {'value': '0', 'status': '✅'}
    }

    for name, default in default_metrics.items():
        if name in metrics:
            m = metrics[name]
            value = m.get('value', default['value'])
            status = m.get('status', default['status'])
        else:
            value = default['value']
            status = default['status']

        rows.append(f"| {name} | {value} | {status} |")

    return '\n'.join(rows)

def generate_dashboard(output_dir: str) -> str:
    """生成 Dashboard 內容"""
    data = load_workflow_data(output_dir)

    dashboard = f"""# 🎯 工作流執行報告

## 基本資訊

| 項目 | 內容 |
|------|------|
| **工作流 ID** | {data['workflow_id']} |
| **任務** | {data['task_name']} |
| **開始時間** | {data['start_time']} |
| **結束時間** | {data['end_time']} |
| **狀態** | {data['status']} |
| **品質分數** | {data['quality_score']}/100 |

## 執行摘要

```
{generate_stage_flow(data)}
```

## 關鍵決策

{format_decisions(data.get('decisions', []))}

## 品質指標

| 指標 | 數值 | 狀態 |
|------|------|------|
{format_metrics(data.get('metrics', {}))}

## 資源使用

| 資源 | 使用量 |
|------|--------|
| Token | {data.get('resources', {}).get('tokens', '-')} |
| API 成本 | ${data.get('resources', {}).get('cost', '0.00')} |
| Agents | {data.get('resources', {}).get('agents', '-')} 個 |
| Tools | {data.get('resources', {}).get('tools', '-')} 次 |

## 詳細報告連結

- [完整時間線](./timeline.md)
- [所有決策](./decisions.md)
- [品質報告](./quality-report.md)

---
*報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    return dashboard

def main():
    if len(sys.argv) < 2:
        print("用法: python generate-dashboard.py <output_dir>")
        sys.exit(1)

    output_dir = sys.argv[1]

    dashboard_content = generate_dashboard(output_dir)

    output_file = os.path.join(output_dir, 'dashboard.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(dashboard_content)

    print(f"  ✅ Dashboard 已生成: {output_file}")

if __name__ == "__main__":
    main()
