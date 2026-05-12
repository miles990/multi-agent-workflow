#!/usr/bin/env python3
"""
指標計算器 - 計算工作流執行統計
用法: python calculate-metrics.py <output_dir>
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

def calculate_metrics(output_dir: str) -> dict:
    """計算各項指標"""
    metrics = {
        'total_tokens': 0,
        'total_cost': 0.0,
        'agent_count': 0,
        'tool_count': 0,
        'stage_durations': {},
        'tdd_compliance': 0,
        'test_coverage': 0,
        'rollback_count': 0,
        'quality_score': 0
    }

    # 掃描 tools 目錄中的日誌
    tools_dir = os.path.join(output_dir, 'tools')
    if os.path.exists(tools_dir):
        tool_log = os.path.join(tools_dir, 'tool-usage.jsonl')
        if os.path.exists(tool_log):
            with open(tool_log, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        metrics['tool_count'] += 1
                        # 估算 token 使用
                        output_size = entry.get('output_size', 0)
                        metrics['total_tokens'] += output_size // 4
                    except:
                        pass

    # 掃描 agents 目錄
    agents_dir = os.path.join(output_dir, 'agents')
    if os.path.exists(agents_dir):
        agent_files = list(Path(agents_dir).glob('*.yaml')) + list(Path(agents_dir).glob('*.json'))
        metrics['agent_count'] = len(agent_files)

    # 計算成本（粗略估算）
    # Claude 3 Sonnet: ~$0.003 per 1K input tokens, ~$0.015 per 1K output tokens
    metrics['total_cost'] = (metrics['total_tokens'] / 1000) * 0.01  # 平均估算

    # 載入其他指標（如果存在）
    metrics_file = os.path.join(output_dir, 'metrics.yaml')
    if os.path.exists(metrics_file):
        try:
            import yaml
            with open(metrics_file, 'r', encoding='utf-8') as f:
                loaded = yaml.safe_load(f) or {}
                metrics.update(loaded)
        except ImportError:
            # 如果 yaml 未安裝，跳過
            pass

    return metrics

def save_metrics(output_dir: str, metrics: dict):
    """保存指標"""
    # 嘗試保存 YAML 格式
    metrics_file = os.path.join(output_dir, 'metrics.yaml')
    try:
        import yaml
        with open(metrics_file, 'w', encoding='utf-8') as f:
            yaml.dump(metrics, f, allow_unicode=True, default_flow_style=False)
    except ImportError:
        # 如果 yaml 未安裝，改用 JSON
        metrics_file = os.path.join(output_dir, 'metrics.json')
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)

    # 更新 metadata.json
    metadata_file = os.path.join(output_dir, 'metadata.json')
    metadata = {}
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

    metadata['resources'] = {
        'tokens': f"{metrics['total_tokens']:,}",
        'cost': f"{metrics['total_cost']:.2f}",
        'agents': metrics['agent_count'],
        'tools': metrics['tool_count']
    }
    metadata['quality_score'] = metrics.get('quality_score', 0)

    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"  ✅ 指標已計算並保存")
    print(f"     - Token: {metrics['total_tokens']:,}")
    print(f"     - 成本: ${metrics['total_cost']:.2f}")
    print(f"     - Agents: {metrics['agent_count']}")
    print(f"     - Tools: {metrics['tool_count']}")

def main():
    if len(sys.argv) < 2:
        print("用法: python calculate-metrics.py <output_dir>")
        sys.exit(1)

    output_dir = sys.argv[1]

    metrics = calculate_metrics(output_dir)
    save_metrics(output_dir, metrics)

if __name__ == "__main__":
    main()
