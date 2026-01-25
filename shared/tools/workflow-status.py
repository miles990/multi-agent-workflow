#!/usr/bin/env python3
"""
工作流狀態查看器 - 顯示工作流執行進度與統計
用法: python workflow-status.py [options]
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# ─────────────────────────────────────────────────────────────────────────────
# 常數定義
# ─────────────────────────────────────────────────────────────────────────────

STAGES = ['RESEARCH', 'PLAN', 'TASKS', 'IMPLEMENT', 'REVIEW', 'VERIFY']

STAGE_WEIGHTS = {
    'RESEARCH': 0.15,
    'PLAN': 0.15,
    'TASKS': 0.10,
    'IMPLEMENT': 0.35,
    'REVIEW': 0.15,
    'VERIFY': 0.10,
}

STATUS_ICONS = {
    'pending': '⏳',
    'running': '🔄',
    'in_progress': '🔄',
    'completed': '✅',
    'failed': '❌',
    'skipped': '⏭️',
    'rollback': '🔙',
}

STATUS_COLORS = {
    'pending': '#9ca3af',     # gray
    'running': '#fbbf24',     # amber
    'in_progress': '#fbbf24',
    'completed': '#4ade80',   # green
    'failed': '#f87171',      # red
    'skipped': '#60a5fa',     # blue
}


class Colors:
    """ANSI 顏色碼"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    GRAY = '\033[0;90m'
    NC = '\033[0m'  # No Color
    BOLD = '\033[1m'


# ─────────────────────────────────────────────────────────────────────────────
# 工作流掃描與載入
# ─────────────────────────────────────────────────────────────────────────────

def find_workflows(memory_path: str) -> List[Dict[str, Any]]:
    """掃描 memory 目錄找到所有工作流"""
    workflows = []
    memory_dir = Path(memory_path)

    # 掃描 workflows 目錄
    workflows_dir = memory_dir / 'workflows'
    if workflows_dir.exists():
        for wf_dir in workflows_dir.iterdir():
            if wf_dir.is_dir():
                meta_file = wf_dir / 'meta.yaml'
                if meta_file.exists():
                    wf = load_workflow_meta(wf_dir, 'workflow')
                    if wf:
                        workflows.append(wf)

    # 掃描其他階段目錄（research, plans, implement 等）
    for stage_dir_name in ['research', 'plans', 'implement', 'tasks', 'review', 'verify']:
        stage_dir = memory_dir / stage_dir_name
        if stage_dir.exists():
            for item_dir in stage_dir.iterdir():
                if item_dir.is_dir():
                    meta_file = item_dir / 'meta.yaml'
                    if meta_file.exists():
                        wf = load_workflow_meta(item_dir, stage_dir_name)
                        if wf:
                            workflows.append(wf)

    # 按日期排序（最新在前）
    def get_sort_date(wf):
        d = wf.get('date', '')
        if isinstance(d, datetime):
            return d.strftime('%Y-%m-%d')
        elif hasattr(d, 'isoformat'):  # date object
            return d.isoformat()
        return str(d) if d else ''

    workflows.sort(key=get_sort_date, reverse=True)
    return workflows


def load_workflow_meta(wf_dir: Path, source_type: str) -> Optional[Dict[str, Any]]:
    """載入工作流的 meta.yaml"""
    meta_file = wf_dir / 'meta.yaml'
    try:
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = yaml.safe_load(f) or {}

        # 標準化欄位
        workflow = {
            'id': meta.get('id', wf_dir.name),
            'name': meta.get('topic', meta.get('name', meta.get('task', wf_dir.name))),
            'path': str(wf_dir),
            'source_type': source_type,
            'status': meta.get('status', 'unknown'),
            'date': meta.get('date', get_file_date(meta_file)),
            'quality_score': meta.get('quality_score', meta.get('quality', None)),
            'current_stage': meta.get('current_stage', detect_current_stage(wf_dir, meta)),
            'stages': meta.get('stages', {}),
            'meta': meta,
        }
        return workflow
    except Exception as e:
        return None


def get_file_date(file_path: Path) -> str:
    """取得檔案修改日期"""
    try:
        mtime = os.path.getmtime(file_path)
        return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
    except Exception:
        return ''


def detect_current_stage(wf_dir: Path, meta: Dict) -> str:
    """偵測當前執行階段"""
    if 'current_stage' in meta:
        return meta['current_stage']

    # 根據 skill 欄位判斷
    skill = meta.get('skill', '')
    if skill:
        return skill.upper()

    # 根據存在的檔案判斷
    stage_files = {
        'RESEARCH': ['synthesis.md', 'report.md'],
        'PLAN': ['implementation-plan.md', 'plan.md'],
        'TASKS': ['tasks.yaml'],
        'IMPLEMENT': ['implementation.md'],
        'REVIEW': ['review-summary.md'],
        'VERIFY': ['verification.md'],
    }

    current = 'RESEARCH'
    for stage, files in stage_files.items():
        for f in files:
            if (wf_dir / f).exists():
                idx = STAGES.index(stage)
                if idx < len(STAGES) - 1:
                    current = STAGES[idx + 1]
                else:
                    current = stage

    return current


def load_tasks(wf_dir: Path) -> List[Dict]:
    """載入任務清單"""
    tasks_file = wf_dir / 'tasks.yaml'
    if not tasks_file.exists():
        # 嘗試找 stages/tasks.yaml
        tasks_file = wf_dir / 'stages' / 'tasks.yaml'

    if not tasks_file.exists():
        return []

    try:
        with open(tasks_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if isinstance(data, dict):
            if 'tasks' in data:
                return data['tasks']
            elif 'waves' in data:
                tasks = []
                for wave in data['waves']:
                    if 'tasks' in wave:
                        tasks.extend(wave['tasks'])
                return tasks
        elif isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def find_active_workflow(memory_path: str) -> Optional[Dict[str, Any]]:
    """找到最近的活動工作流"""
    workflows = find_workflows(memory_path)

    # 優先找 running/in_progress 的
    for wf in workflows:
        if wf['status'] in ['running', 'in_progress']:
            return wf

    # 否則返回最新的
    return workflows[0] if workflows else None


def load_workflow_by_id(memory_path: str, workflow_id: str) -> Optional[Dict[str, Any]]:
    """根據 ID 載入特定工作流"""
    workflows = find_workflows(memory_path)
    for wf in workflows:
        if wf['id'] == workflow_id or workflow_id in wf['id']:
            return wf
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 進度計算
# ─────────────────────────────────────────────────────────────────────────────

def calculate_progress(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """計算工作流進度"""
    stages = workflow.get('stages', {})
    current_stage = workflow.get('current_stage', 'RESEARCH')

    # 計算各階段狀態
    stage_status = {}
    current_idx = STAGES.index(current_stage) if current_stage in STAGES else 0

    for i, stage in enumerate(STAGES):
        stage_info = stages.get(stage.lower(), {})
        if isinstance(stage_info, dict):
            status = stage_info.get('status', 'pending')
        else:
            status = 'pending'

        # 根據位置推斷狀態
        if i < current_idx:
            status = 'completed'
        elif i == current_idx:
            status = workflow.get('status', 'running')
            if status == 'completed':
                status = 'running'  # 當前階段標記為執行中
        else:
            status = 'pending'

        stage_status[stage] = status

    # 計算總進度百分比
    total_progress = 0.0
    for stage, weight in STAGE_WEIGHTS.items():
        status = stage_status.get(stage, 'pending')
        if status == 'completed':
            total_progress += weight * 1.0
        elif status in ['running', 'in_progress']:
            total_progress += weight * 0.5

    return {
        'percent': int(total_progress * 100),
        'stage_status': stage_status,
        'current_stage': current_stage,
    }


def calculate_task_progress(tasks: List[Dict]) -> Dict[str, Any]:
    """計算任務進度"""
    if not tasks:
        return {'total': 0, 'completed': 0, 'running': 0, 'pending': 0}

    completed = sum(1 for t in tasks if t.get('status') == 'completed')
    running = sum(1 for t in tasks if t.get('status') in ['running', 'in_progress'])

    return {
        'total': len(tasks),
        'completed': completed,
        'running': running,
        'pending': len(tasks) - completed - running,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ASCII 輸出
# ─────────────────────────────────────────────────────────────────────────────

def render_progress_bar(percent: int, width: int = 40) -> str:
    """繪製進度條"""
    filled = int(width * percent / 100)
    empty = width - filled
    return f"[{'█' * filled}{'░' * empty}] {percent}%"


def render_stage_flow(stage_status: Dict[str, str], current_stage: str) -> str:
    """繪製階段流程圖"""
    parts = []
    for stage in STAGES:
        status = stage_status.get(stage, 'pending')
        icon = STATUS_ICONS.get(status, '⏳')
        parts.append(f"{stage} {icon}")

    flow = ' → '.join(parts)

    # 標記當前階段
    pointer_line = ""
    if current_stage in STAGES:
        idx = STAGES.index(current_stage)
        # 計算位置
        positions = []
        pos = 0
        for i, stage in enumerate(STAGES):
            positions.append(pos + len(stage) // 2)
            pos += len(stage) + 5  # stage + icon + " → "

        spaces = positions[idx]
        pointer_line = f"\n{' ' * spaces}↑\n{' ' * (spaces - 2)}當前階段"

    return flow + pointer_line


def render_perspective_table(perspectives: List[Dict]) -> str:
    """繪製視角狀態表"""
    if not perspectives:
        return ""

    lines = []
    # 頂部邊框
    cell_width = 14
    top_border = '┌' + '┬'.join(['─' * cell_width] * len(perspectives)) + '┐'
    mid_border = '├' + '┼'.join(['─' * cell_width] * len(perspectives)) + '┤'
    bot_border = '└' + '┴'.join(['─' * cell_width] * len(perspectives)) + '┘'

    lines.append(top_border)

    # 名稱行
    names = []
    for p in perspectives:
        name = p.get('name', p.get('id', 'Unknown'))[:cell_width - 2]
        names.append(f"│ {name.center(cell_width - 2)} ")
    lines.append(''.join(names) + '│')

    # 狀態行
    statuses = []
    for p in perspectives:
        status = p.get('status', 'pending')
        icon = STATUS_ICONS.get(status, '⏳')
        statuses.append(f"│ {icon.center(cell_width - 2)} ")
    lines.append(''.join(statuses) + '│')

    # 說明行
    labels = []
    for p in perspectives:
        status = p.get('status', 'pending')
        label = {'completed': '完成', 'running': '執行中', 'in_progress': '執行中', 'pending': '等待'}.get(status, status)
        labels.append(f"│ {label.center(cell_width - 2)} ")
    lines.append(''.join(labels) + '│')

    lines.append(bot_border)
    return '\n'.join(lines)


def render_task_list(tasks: List[Dict], limit: int = 10) -> str:
    """繪製任務清單"""
    if not tasks:
        return ""

    lines = []
    for i, task in enumerate(tasks[:limit]):
        task_id = task.get('id', f'Task-{i+1}')
        title = task.get('title', task.get('subject', task.get('name', '')))[:40]
        status = task.get('status', 'pending')
        icon = STATUS_ICONS.get(status, '⏳')

        if i == 0:
            prefix = '├──'
        elif i == len(tasks[:limit]) - 1:
            prefix = '└──'
        else:
            prefix = '├──'

        lines.append(f"{prefix} {icon} {task_id}: {title}")

    if len(tasks) > limit:
        lines.append(f"    ... 還有 {len(tasks) - limit} 個任務")

    return '\n'.join(lines)


def render_workflow_status(workflow: Dict[str, Any], tasks: List[Dict]) -> str:
    """渲染工作流狀態（ASCII 格式）"""
    name = workflow.get('name', workflow.get('id', 'Unknown'))
    status = workflow.get('status', 'unknown')
    quality = workflow.get('quality_score')

    progress = calculate_progress(workflow)
    task_progress = calculate_task_progress(tasks)

    lines = []

    # 標題框
    lines.append('╭' + '─' * 58 + '╮')
    title = f"  🎯 {name}"[:56]
    lines.append(f"│{title.ljust(58)}│")

    status_line = f"  狀態: {STATUS_ICONS.get(status, '?')} {status}"
    if quality:
        status_line += f" | 品質: {quality}/100"
    lines.append(f"│{status_line.ljust(58)}│")
    lines.append('╰' + '─' * 58 + '╯')

    lines.append('')

    # 進度條
    lines.append(f"進度: {render_progress_bar(progress['percent'])}")
    lines.append('')

    # 階段流程
    lines.append(render_stage_flow(progress['stage_status'], progress['current_stage']))
    lines.append('')

    # 視角狀態（如果有）
    perspectives = workflow.get('meta', {}).get('perspectives', [])
    if isinstance(perspectives, list) and perspectives and isinstance(perspectives[0], dict):
        lines.append(render_perspective_table(perspectives))
        lines.append('')

    # 任務進度
    if task_progress['total'] > 0:
        lines.append(f"任務進度: {task_progress['completed']}/{task_progress['total']} 完成")
        lines.append(render_task_list(tasks))
        lines.append('')

    # Memory 路徑
    lines.append(f"Memory: {workflow.get('path', 'N/A')}")

    return '\n'.join(lines)


def render_workflow_list(workflows: List[Dict], limit: int = 5) -> str:
    """渲染工作流列表（ASCII 格式）"""
    lines = []

    # 標題
    lines.append('╭' + '─' * 58 + '╮')
    lines.append(f"│{'  📋 工作流歷史'.ljust(58)}│")
    lines.append('╰' + '─' * 58 + '╯')
    lines.append('')
    lines.append(f"最近 {min(limit, len(workflows))} 個工作流：")
    lines.append('')

    # 表頭
    lines.append(f"│ {'ID':<20} │ {'任務':<16} │ {'狀態':<8} │ {'品質':<5} │ {'日期':<10} │")
    lines.append('├' + '─' * 22 + '┼' + '─' * 18 + '┼' + '─' * 10 + '┼' + '─' * 7 + '┼' + '─' * 12 + '┤')

    for wf in workflows[:limit]:
        wf_id = wf.get('id', '')[:20]
        name = wf.get('name', '')[:16]
        status = wf.get('status', 'unknown')
        status_display = f"{STATUS_ICONS.get(status, '?')}{status[:6]}"
        quality = wf.get('quality_score', '-')
        quality_str = str(quality) if quality else '-'
        date_val = wf.get('date', '')
        if hasattr(date_val, 'isoformat'):
            date = date_val.isoformat()[:10]
        else:
            date = str(date_val)[:10] if date_val else ''

        lines.append(f"│ {wf_id:<20} │ {name:<16} │ {status_display:<8} │ {quality_str:<5} │ {date:<10} │")

    lines.append('')

    # 統計
    total = len(workflows)
    completed = sum(1 for w in workflows if w.get('status') == 'completed')
    failed = sum(1 for w in workflows if w.get('status') == 'failed')
    running = sum(1 for w in workflows if w.get('status') in ['running', 'in_progress'])

    qualities = [w.get('quality_score') for w in workflows if w.get('quality_score')]
    avg_quality = sum(qualities) / len(qualities) if qualities else 0

    lines.append('統計：')
    lines.append(f"  總計: {total} | 完成: {completed} | 失敗: {failed} | 執行中: {running}")
    if avg_quality:
        lines.append(f"  平均品質分數: {avg_quality:.1f}")

    return '\n'.join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Mermaid 輸出
# ─────────────────────────────────────────────────────────────────────────────

def render_stage_mermaid(progress: Dict) -> str:
    """生成階段流程的 Mermaid 圖"""
    lines = ['```mermaid', 'graph LR']

    stage_status = progress.get('stage_status', {})

    # 為每個階段生成唯一 ID
    stage_ids = {
        'RESEARCH': 'RES',
        'PLAN': 'PLN',
        'TASKS': 'TSK',
        'IMPLEMENT': 'IMP',
        'REVIEW': 'REV',
        'VERIFY': 'VER',
    }

    # 節點
    for stage in STAGES:
        status = stage_status.get(stage, 'pending')
        icon = STATUS_ICONS.get(status, '⏳')
        sid = stage_ids.get(stage, stage[:3])
        lines.append(f'    {sid}["{stage} {icon}"]')

    # 連線
    for i in range(len(STAGES) - 1):
        sid1 = stage_ids.get(STAGES[i], STAGES[i][:3])
        sid2 = stage_ids.get(STAGES[i+1], STAGES[i+1][:3])
        lines.append(f'    {sid1} --> {sid2}')

    # 樣式
    lines.append('')
    for stage in STAGES:
        status = stage_status.get(stage, 'pending')
        color = STATUS_COLORS.get(status, '#9ca3af')
        sid = stage_ids.get(stage, stage[:3])
        lines.append(f'    style {sid} fill:{color}')

    lines.append('```')
    return '\n'.join(lines)


def render_dag_mermaid(tasks: List[Dict]) -> str:
    """生成任務 DAG 的 Mermaid 圖"""
    if not tasks:
        return ''

    lines = ['```mermaid', 'graph TD']

    # 按 wave 分組
    waves = {}
    for task in tasks:
        wave = task.get('wave', 1)
        if wave not in waves:
            waves[wave] = []
        waves[wave].append(task)

    # 生成 subgraph
    for wave_num in sorted(waves.keys()):
        wave_tasks = waves[wave_num]
        lines.append(f'    subgraph Wave{wave_num}["Wave {wave_num}"]')
        for task in wave_tasks:
            task_id = task.get('id', 'unknown')
            title = task.get('title', task.get('subject', task.get('name', task_id)))[:30]
            safe_id = task_id.replace('-', '_')
            lines.append(f'        {safe_id}["{task_id}: {title}"]')
        lines.append('    end')

    # 生成依賴連線
    lines.append('')
    for task in tasks:
        task_id = task.get('id', '').replace('-', '_')
        deps = task.get('depends_on', []) or task.get('blockedBy', []) or []
        if isinstance(deps, str):
            deps = [deps]
        for dep in deps:
            dep_id = dep.replace('-', '_')
            lines.append(f'    {dep_id} --> {task_id}')

    # 樣式
    lines.append('')
    for task in tasks:
        task_id = task.get('id', '').replace('-', '_')
        status = task.get('status', 'pending')
        color = STATUS_COLORS.get(status, '#9ca3af')
        lines.append(f'    style {task_id} fill:{color}')

    lines.append('```')
    return '\n'.join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Markdown 輸出
# ─────────────────────────────────────────────────────────────────────────────

def render_workflow_markdown(workflow: Dict[str, Any], tasks: List[Dict]) -> str:
    """渲染工作流狀態（Markdown 格式）"""
    name = workflow.get('name', workflow.get('id', 'Unknown'))
    status = workflow.get('status', 'unknown')
    quality = workflow.get('quality_score')

    progress = calculate_progress(workflow)
    task_progress = calculate_task_progress(tasks)

    lines = []

    # 標題
    lines.append(f"# 🎯 {name}")
    lines.append('')

    status_line = f"**狀態**: {STATUS_ICONS.get(status, '?')} {status}"
    if quality:
        status_line += f" | **品質**: {quality}/100"
    status_line += f" | **進度**: {progress['percent']}%"
    lines.append(status_line)
    lines.append('')

    # 階段流程圖
    lines.append("## 階段進度")
    lines.append('')
    lines.append(render_stage_mermaid(progress))
    lines.append('')

    # 任務列表
    if task_progress['total'] > 0:
        lines.append("## 任務進度")
        lines.append('')
        lines.append(f"完成: {task_progress['completed']}/{task_progress['total']}")
        lines.append('')

        # 任務表格
        lines.append("| 狀態 | ID | 標題 |")
        lines.append("|------|------|------|")
        for task in tasks[:20]:
            task_id = task.get('id', 'N/A')
            title = task.get('title', task.get('subject', task.get('name', '')))[:50]
            status = task.get('status', 'pending')
            icon = STATUS_ICONS.get(status, '⏳')
            lines.append(f"| {icon} | {task_id} | {title} |")
        lines.append('')

        # 任務 DAG
        if len(tasks) > 1:
            lines.append("## 任務依賴")
            lines.append('')
            lines.append(render_dag_mermaid(tasks))
            lines.append('')

    # Memory 路徑
    lines.append("---")
    lines.append(f"*Memory: `{workflow.get('path', 'N/A')}`*")

    return '\n'.join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# HTML 輸出（從 Markdown 轉換）
# ─────────────────────────────────────────────────────────────────────────────

HTML_WRAPPER = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Workflow Dashboard - {title}</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked@9/marked.min.js"></script>
  <style>
    :root {{
      --bg-primary: #0f172a;
      --bg-secondary: #1e293b;
      --bg-card: #334155;
      --text-primary: #f1f5f9;
      --text-secondary: #94a3b8;
      --accent-green: #4ade80;
      --accent-amber: #fbbf24;
      --accent-red: #f87171;
      --accent-blue: #60a5fa;
      --accent-purple: #a78bfa;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg-primary);
      color: var(--text-primary);
      line-height: 1.7;
      padding: 2rem;
      min-height: 100vh;
    }}

    .container {{
      max-width: 1000px;
      margin: 0 auto;
    }}

    h1 {{
      font-size: 1.875rem;
      font-weight: 700;
      margin-bottom: 1.5rem;
      background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}

    h2 {{
      font-size: 1.25rem;
      font-weight: 600;
      margin: 2rem 0 1rem;
      color: var(--accent-blue);
      border-bottom: 2px solid var(--bg-card);
      padding-bottom: 0.5rem;
    }}

    p {{ margin: 0.75rem 0; }}

    strong {{
      color: var(--accent-blue);
      font-weight: 600;
    }}

    hr {{
      border: none;
      border-top: 1px solid var(--bg-card);
      margin: 2rem 0;
    }}

    pre {{
      background: var(--bg-secondary);
      padding: 1rem;
      border-radius: 8px;
      overflow-x: auto;
      margin: 1rem 0;
      border: 1px solid var(--bg-card);
    }}

    code {{
      font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
      font-size: 0.875em;
    }}

    :not(pre) > code {{
      background: var(--bg-secondary);
      padding: 0.2rem 0.4rem;
      border-radius: 4px;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 1rem 0;
      background: var(--bg-secondary);
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid var(--bg-card);
    }}

    th, td {{
      padding: 0.75rem 1rem;
      text-align: left;
      border-bottom: 1px solid var(--bg-card);
    }}

    th {{
      background: var(--bg-card);
      color: var(--accent-blue);
      font-weight: 600;
      font-size: 0.875rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: rgba(96, 165, 250, 0.05); }}

    .mermaid {{
      background: var(--bg-secondary);
      padding: 1.5rem;
      border-radius: 12px;
      margin: 1.5rem 0;
      border: 1px solid var(--bg-card);
      display: flex;
      justify-content: center;
    }}

    .mermaid svg {{
      max-width: 100%;
      height: auto;
    }}

    footer {{
      margin-top: 3rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--bg-card);
      color: var(--text-secondary);
      font-size: 0.875rem;
      text-align: center;
    }}

    em {{
      color: var(--text-secondary);
      font-style: normal;
    }}

    /* Status badge styles */
    .status-info {{
      background: var(--bg-secondary);
      padding: 1rem 1.5rem;
      border-radius: 8px;
      margin: 1rem 0;
      border-left: 4px solid var(--accent-blue);
    }}
  </style>
</head>
<body>
  <div class="container">
    <div id="content"></div>
    <footer>
      <p>Generated: {generated_time}</p>
    </footer>
  </div>

  <script>
    // Initialize mermaid with dark theme
    mermaid.initialize({{
      startOnLoad: false,
      theme: 'dark',
      themeVariables: {{
        primaryColor: '#334155',
        primaryTextColor: '#f1f5f9',
        primaryBorderColor: '#475569',
        lineColor: '#60a5fa',
        secondaryColor: '#1e293b',
        tertiaryColor: '#0f172a',
        background: '#1e293b',
        mainBkg: '#334155',
        nodeBorder: '#475569',
        clusterBkg: '#1e293b',
        clusterBorder: '#475569',
        titleColor: '#f1f5f9',
        edgeLabelBackground: '#1e293b'
      }}
    }});

    const md = {markdown_content};

    // Pre-process: extract mermaid blocks before marked parsing
    let mermaidBlocks = [];
    const processedMd = md.replace(/```mermaid\\n([\\s\\S]*?)```/g, (match, code) => {{
      const id = 'mermaid-' + mermaidBlocks.length;
      mermaidBlocks.push({{ id, code }});
      return '<div class="mermaid" id="' + id + '"></div>';
    }});

    // Parse markdown (without mermaid blocks)
    document.getElementById('content').innerHTML = marked.parse(processedMd);

    // Render mermaid diagrams
    mermaidBlocks.forEach(async ({{ id, code }}) => {{
      try {{
        const {{ svg }} = await mermaid.render(id + '-svg', code);
        document.getElementById(id).innerHTML = svg;
      }} catch (e) {{
        console.error('Mermaid render error:', e);
        document.getElementById(id).innerHTML = '<pre style="color: #f87171;">Mermaid Error: ' + e.message + '</pre>';
      }}
    }});
  </script>
</body>
</html>'''


def markdown_to_html(md_content: str, title: str) -> str:
    """將 Markdown 轉換為 HTML（使用 marked.js 在瀏覽器端轉換）"""
    import json
    # Escape markdown content for JavaScript string
    escaped_md = json.dumps(md_content, ensure_ascii=False)

    return HTML_WRAPPER.format(
        title=title,
        markdown_content=escaped_md,
        generated_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    )


# ─────────────────────────────────────────────────────────────────────────────
# JSON 輸出
# ─────────────────────────────────────────────────────────────────────────────

def render_workflow_json(workflow: Dict[str, Any], tasks: List[Dict]) -> str:
    """渲染工作流狀態（JSON 格式）"""
    progress = calculate_progress(workflow)
    task_progress = calculate_task_progress(tasks)

    output = {
        'workflow_id': workflow.get('id'),
        'name': workflow.get('name'),
        'status': workflow.get('status'),
        'quality_score': workflow.get('quality_score'),
        'progress_percent': progress['percent'],
        'current_stage': progress['current_stage'],
        'stage_status': progress['stage_status'],
        'task_progress': task_progress,
        'tasks': tasks[:50],
        'path': workflow.get('path'),
        'date': serialize_date(workflow.get('date')),
    }

    return json.dumps(output, ensure_ascii=False, indent=2)


def serialize_date(d) -> str:
    """將日期物件序列化為字串"""
    if d is None:
        return None
    if hasattr(d, 'isoformat'):
        return d.isoformat()
    return str(d)


def render_list_json(workflows: List[Dict]) -> str:
    """渲染工作流列表（JSON 格式）"""
    output = {
        'total': len(workflows),
        'workflows': [{
            'id': w.get('id'),
            'name': w.get('name'),
            'status': w.get('status'),
            'quality_score': w.get('quality_score'),
            'date': serialize_date(w.get('date')),
            'path': w.get('path'),
        } for w in workflows],
        'stats': {
            'completed': sum(1 for w in workflows if w.get('status') == 'completed'),
            'failed': sum(1 for w in workflows if w.get('status') == 'failed'),
            'running': sum(1 for w in workflows if w.get('status') in ['running', 'in_progress']),
        }
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# 主程式
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='工作流狀態查看器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
範例:
  python workflow-status.py                    # 顯示當前工作流
  python workflow-status.py --id user-auth     # 顯示特定工作流
  python workflow-status.py --list             # 列出所有工作流
  python workflow-status.py --dag              # 顯示任務 DAG
  python workflow-status.py --json             # JSON 輸出
  python workflow-status.py -o dashboard.md    # 輸出到檔案
  python workflow-status.py --html -o dash.html # HTML Dashboard
        '''
    )

    parser.add_argument('--id', help='指定工作流 ID')
    parser.add_argument('--list', action='store_true', help='列出所有工作流')
    parser.add_argument('--dag', action='store_true', help='顯示任務依賴圖（Mermaid）')
    parser.add_argument('--json', action='store_true', help='輸出 JSON 格式')
    parser.add_argument('--html', action='store_true', help='生成 HTML Dashboard')
    parser.add_argument('--markdown', action='store_true', help='生成 Markdown 報告')
    parser.add_argument('-o', '--output', help='輸出檔案路徑')
    parser.add_argument('--memory-path', default='.claude/memory/', help='Memory 目錄路徑')
    parser.add_argument('--limit', type=int, default=5, help='--list 顯示數量')

    args = parser.parse_args()

    # 確保 memory 路徑存在
    if not Path(args.memory_path).exists():
        print(f"Memory 目錄不存在: {args.memory_path}", file=sys.stderr)
        sys.exit(1)

    # 列出所有工作流
    if args.list:
        workflows = find_workflows(args.memory_path)
        if not workflows:
            print("沒有找到任何工作流")
            sys.exit(1)

        if args.json:
            output = render_list_json(workflows[:args.limit])
        else:
            output = render_workflow_list(workflows, args.limit)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"已輸出到: {args.output}")
        else:
            print(output)

        sys.exit(0)

    # 載入工作流
    if args.id:
        workflow = load_workflow_by_id(args.memory_path, args.id)
        if not workflow:
            print(f"找不到工作流: {args.id}", file=sys.stderr)
            sys.exit(2)
    else:
        workflow = find_active_workflow(args.memory_path)
        if not workflow:
            print("沒有找到活動的工作流")
            sys.exit(1)

    # 載入任務
    tasks = load_tasks(Path(workflow['path']))

    # 只顯示 DAG
    if args.dag:
        if not tasks:
            print("此工作流沒有任務資料")
            sys.exit(1)

        output = render_dag_mermaid(tasks)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"已輸出到: {args.output}")
        else:
            print(output)
        sys.exit(0)

    # 選擇輸出格式
    if args.json:
        output = render_workflow_json(workflow, tasks)
    elif args.html:
        # HTML 模式：先生成 Markdown，再轉換為 HTML
        md_content = render_workflow_markdown(workflow, tasks)
        title = workflow.get('name', workflow.get('id', 'Workflow'))
        output = markdown_to_html(md_content, title)
    elif args.markdown or (args.output and args.output.endswith('.md')):
        output = render_workflow_markdown(workflow, tasks)
    else:
        output = render_workflow_status(workflow, tasks)

    # 輸出
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"已輸出到: {args.output}")
    else:
        print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()
