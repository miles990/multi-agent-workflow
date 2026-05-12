#!/usr/bin/env python3
"""
DAG 驗證器 - 檢查任務依賴的正確性
用法: python dag-validator.py <tasks_file>
"""

import argparse
import sys
import yaml
from collections import defaultdict
from typing import Dict, List, Set, Tuple

class Colors:
    """ANSI 顏色碼"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def log_error(msg: str) -> None:
    print(f"{Colors.RED}❌ {msg}{Colors.NC}")

def log_success(msg: str) -> None:
    print(f"{Colors.GREEN}✅ {msg}{Colors.NC}")

def log_warning(msg: str) -> None:
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.NC}")

def log_info(msg: str) -> None:
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.NC}")

def load_tasks(tasks_file: str) -> List[Dict]:
    """載入任務檔案"""
    with open(tasks_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # 支援不同的結構
    if isinstance(data, dict):
        if 'tasks' in data:
            return data['tasks']
        elif 'waves' in data:
            # 展開 waves 結構
            tasks = []
            for wave in data['waves']:
                if 'tasks' in wave:
                    tasks.extend(wave['tasks'])
            return tasks
    elif isinstance(data, list):
        return data

    return []

def validate_dag(tasks_file: str) -> bool:
    """
    驗證任務 DAG 的正確性

    檢查項目：
    1. 依賴指向不存在的任務
    2. 循環依賴
    3. TDD 對應（TEST-* 是否 block T-F-*）
    """
    print("═══════════════════════════════════════════")
    print(f"🔍 DAG 驗證中: {tasks_file}")
    print("═══════════════════════════════════════════")

    try:
        tasks = load_tasks(tasks_file)
    except Exception as e:
        log_error(f"無法載入任務檔案: {e}")
        return False

    if not tasks:
        log_error("任務列表為空")
        return False

    # 建立依賴圖
    graph: Dict[str, List[str]] = defaultdict(list)
    all_ids: Set[str] = set()
    task_map: Dict[str, Dict] = {}

    for task in tasks:
        task_id = task.get('id', '')
        if not task_id:
            continue

        all_ids.add(task_id)
        task_map[task_id] = task

        # 支援 depends_on 和 blockedBy
        deps = task.get('depends_on', []) or task.get('blockedBy', []) or []
        if isinstance(deps, str):
            deps = [deps]

        for dep in deps:
            graph[dep].append(task_id)

    log_info(f"載入 {len(all_ids)} 個任務")

    errors = []
    warnings = []

    # 1. 檢查依賴指向不存在的任務
    print("\n📋 檢查依賴有效性...")
    for task in tasks:
        task_id = task.get('id', '')
        deps = task.get('depends_on', []) or task.get('blockedBy', []) or []
        if isinstance(deps, str):
            deps = [deps]

        for dep in deps:
            if dep not in all_ids:
                errors.append(f"任務 {task_id} 依賴不存在的任務: {dep}")

    if errors:
        for err in errors:
            log_error(err)
    else:
        log_success("所有依賴都指向有效任務")

    # 2. 檢查循環依賴
    print("\n🔄 檢查循環依賴...")

    def find_cycle(node: str, visited: Set[str], rec_stack: Set[str], path: List[str]) -> Tuple[bool, List[str]]:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                cycle_found, cycle_path = find_cycle(neighbor, visited, rec_stack, path)
                if cycle_found:
                    return True, cycle_path
            elif neighbor in rec_stack:
                cycle_start = path.index(neighbor)
                return True, path[cycle_start:] + [neighbor]

        path.pop()
        rec_stack.remove(node)
        return False, []

    visited: Set[str] = set()
    cycles_found = []

    for task_id in all_ids:
        if task_id not in visited:
            cycle_found, cycle_path = find_cycle(task_id, visited, set(), [])
            if cycle_found:
                cycle_str = ' → '.join(cycle_path)
                cycles_found.append(cycle_str)

    if cycles_found:
        for cycle in cycles_found:
            log_error(f"發現循環依賴: {cycle}")
        errors.extend([f"循環依賴: {c}" for c in cycles_found])
    else:
        log_success("無循環依賴")

    # 3. 檢查 TDD 對應
    print("\n🧪 檢查 TDD 對應...")
    tdd_issues = []

    for task in tasks:
        task_id = task.get('id', '')
        if task_id.startswith('T-F-'):
            # 找對應的 TEST-*
            test_id = task_id.replace('T-F-', 'TEST-')

            if test_id in all_ids:
                # 檢查 TEST-* 是否在 depends_on 中
                deps = task.get('depends_on', []) or task.get('blockedBy', []) or []
                if isinstance(deps, str):
                    deps = [deps]

                if test_id not in deps:
                    tdd_issues.append(f"{task_id} 應該依賴 {test_id}")
            else:
                tdd_issues.append(f"{task_id} 缺少對應的測試任務 {test_id}")

    if tdd_issues:
        for issue in tdd_issues:
            log_warning(f"TDD: {issue}")
        warnings.extend(tdd_issues)
    else:
        log_success("TDD 對應正確")

    # 4. 檢查孤立任務
    print("\n🔗 檢查孤立任務...")

    # 建立入度和出度
    in_degree: Dict[str, int] = defaultdict(int)
    out_degree: Dict[str, int] = defaultdict(int)

    for task in tasks:
        task_id = task.get('id', '')
        deps = task.get('depends_on', []) or task.get('blockedBy', []) or []
        if isinstance(deps, str):
            deps = [deps]

        out_degree[task_id] = 0  # 初始化
        for dep in deps:
            in_degree[task_id] += 1
            out_degree[dep] += 1

    orphans = [tid for tid in all_ids if in_degree[tid] == 0 and out_degree[tid] == 0]

    # 排除起始任務（通常 ID 較小的是起始）
    orphans = [o for o in orphans if not o.startswith('SETUP-') and not o.startswith('INIT-')]

    if orphans and len(orphans) < len(all_ids):  # 不是只有一個任務的情況
        for orphan in orphans:
            log_warning(f"孤立任務（無入無出）: {orphan}")
    else:
        log_success("無孤立任務")

    # 總結
    print("\n═══════════════════════════════════════════")
    print("📊 驗證總結")
    print("───────────────────────")
    print(f"總任務數: {len(all_ids)}")
    print(f"錯誤數: {len(errors)}")
    print(f"警告數: {len(warnings)}")

    if not errors:
        log_success("DAG 驗證通過")
        print("═══════════════════════════════════════════")
        return True
    else:
        log_error("DAG 驗證失敗")
        print("═══════════════════════════════════════════")
        return False

def generate_mermaid(tasks_file: str, output_file: str = None) -> str:
    """
    生成任務 DAG 的 Mermaid 圖表

    Args:
        tasks_file: 任務檔案路徑
        output_file: 輸出檔案路徑（可選）

    Returns:
        Mermaid 圖表字串
    """
    try:
        tasks = load_tasks(tasks_file)
    except Exception as e:
        print(f"無法載入任務檔案: {e}", file=sys.stderr)
        return ""

    if not tasks:
        print("任務列表為空", file=sys.stderr)
        return ""

    # 狀態顏色
    STATUS_COLORS = {
        'pending': '#9ca3af',     # gray
        'running': '#fbbf24',     # amber
        'in_progress': '#fbbf24',
        'completed': '#4ade80',   # green
        'failed': '#f87171',      # red
    }

    STATUS_ICONS = {
        'pending': '⏳',
        'running': '🔄',
        'in_progress': '🔄',
        'completed': '✅',
        'failed': '❌',
    }

    lines = ['```mermaid', 'graph TD']

    # 按 wave 分組
    waves: Dict[int, List[Dict]] = defaultdict(list)
    for task in tasks:
        wave = task.get('wave', 1)
        waves[wave].append(task)

    # 生成 subgraph
    for wave_num in sorted(waves.keys()):
        wave_tasks = waves[wave_num]
        lines.append(f'    subgraph Wave{wave_num}["Wave {wave_num}"]')
        for task in wave_tasks:
            task_id = task.get('id', 'unknown')
            title = task.get('title', task.get('subject', task.get('name', task_id)))
            # 截斷標題
            title = title[:35] + '...' if len(title) > 35 else title
            # 安全的 ID（Mermaid 不支援連字號在某些情況）
            safe_id = task_id.replace('-', '_')
            status = task.get('status', 'pending')
            icon = STATUS_ICONS.get(status, '⏳')
            lines.append(f'        {safe_id}["{icon} {task_id}<br/>{title}"]')
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

    mermaid_output = '\n'.join(lines)

    # 輸出
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(mermaid_output)
        print(f"已輸出到: {output_file}")
    else:
        print(mermaid_output)

    return mermaid_output


def main():
    parser = argparse.ArgumentParser(
        description='DAG 驗證器 - 檢查任務依賴的正確性',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
範例:
  python dag-validator.py tasks.yaml              # 驗證 DAG
  python dag-validator.py tasks.yaml --mermaid    # 生成 Mermaid 圖
  python dag-validator.py tasks.yaml --mermaid -o dag.md  # 輸出到檔案
        '''
    )

    parser.add_argument('tasks_file', help='任務檔案路徑')
    parser.add_argument('--mermaid', action='store_true', help='生成 Mermaid 圖表')
    parser.add_argument('-o', '--output', help='輸出檔案路徑（僅 --mermaid 使用）')

    args = parser.parse_args()

    if args.mermaid:
        result = generate_mermaid(args.tasks_file, args.output)
        sys.exit(0 if result else 1)
    else:
        success = validate_dag(args.tasks_file)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
