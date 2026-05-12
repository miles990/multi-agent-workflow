#!/usr/bin/env python3
"""
Action Log Viewer - 行動級日誌查詢工具

用途：
  查詢和分析 .claude/workflow/{workflow-id}/logs/actions.jsonl

範例：
  # 查看所有失敗的行動
  ./action-log-viewer.py --failed

  # 查看特定 Agent 的行動
  ./action-log-viewer.py --agent agent_architecture

  # 查看執行時間超過 5 秒的行動
  ./action-log-viewer.py --slow 5000

  # 查看特定工具的行動
  ./action-log-viewer.py --tool Bash

  # 組合條件
  ./action-log-viewer.py --stage IMPLEMENT --failed --tool Edit

  # 輸出統計資訊
  ./action-log-viewer.py --stats
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterator


def find_action_logs() -> list[Path]:
    """尋找所有 actions.jsonl 檔案"""
    base_paths = [
        Path(".claude/workflow"),
        Path.home() / ".claude/workflow",
    ]

    log_files = []
    for base in base_paths:
        if base.exists():
            log_files.extend(base.glob("**/logs/actions.jsonl"))

    return sorted(log_files, key=lambda p: p.stat().st_mtime, reverse=True)


def read_jsonl(path: Path) -> Iterator[dict]:
    """讀取 JSONL 檔案"""
    if not path.exists():
        return

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                print(f"警告: {path}:{line_num} JSON 解析錯誤: {e}", file=sys.stderr)


def filter_actions(
    actions: Iterator[dict],
    failed: bool = False,
    agent: str | None = None,
    slow: int | None = None,
    tool: str | None = None,
    stage: str | None = None,
    since: datetime | None = None,
    workflow: str | None = None,
) -> Iterator[dict]:
    """根據條件過濾行動"""
    for action in actions:
        # 失敗過濾
        if failed and action.get("status") != "failed":
            continue

        # Agent 過濾
        if agent and action.get("agent_id") != agent:
            continue

        # 慢行動過濾
        if slow is not None:
            duration = action.get("duration_ms", 0)
            if duration < slow:
                continue

        # 工具過濾
        if tool and action.get("tool") != tool:
            continue

        # 階段過濾
        if stage and action.get("stage") != stage.upper():
            continue

        # 時間過濾
        if since:
            ts_str = action.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts < since:
                    continue
            except ValueError:
                continue

        # 工作流過濾
        if workflow and action.get("workflow_id") != workflow:
            continue

        yield action


def format_action(action: dict, verbose: bool = False) -> str:
    """格式化單個行動記錄"""
    status = action.get("status", "unknown")
    status_icon = {"success": "✓", "failed": "✗", "timeout": "⏱", "skipped": "○"}.get(
        status, "?"
    )

    tool = action.get("tool", "unknown")
    agent = action.get("agent_id", "unknown")
    stage = action.get("stage", "?")
    duration = action.get("duration_ms", 0)
    timestamp = action.get("timestamp", "")[:19]  # 截取到秒

    # 基本資訊
    line = f"[{status_icon}] {timestamp} | {stage:10} | {agent:20} | {tool:10} | {duration:>6}ms"

    if verbose:
        # 詳細資訊
        lines = [line]

        # 輸入
        input_data = action.get("input", {})
        if input_data:
            for key, value in input_data.items():
                value_str = str(value)
                if len(value_str) > 80:
                    value_str = value_str[:77] + "..."
                lines.append(f"    {key}: {value_str}")

        # 錯誤
        error = action.get("error")
        if error:
            lines.append(f"    ERROR: {error}")

        stderr = action.get("stderr")
        if stderr:
            stderr_preview = stderr[:200] + "..." if len(stderr) > 200 else stderr
            lines.append(f"    STDERR: {stderr_preview}")

        lines.append("")
        return "\n".join(lines)

    return line


def calculate_stats(actions: list[dict]) -> dict[str, Any]:
    """計算統計資訊"""
    if not actions:
        return {"total": 0}

    # 基本統計
    total = len(actions)
    by_status = {}
    by_tool = {}
    by_stage = {}
    by_agent = {}
    total_duration = 0
    slowest = []

    for action in actions:
        # 狀態
        status = action.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1

        # 工具
        tool = action.get("tool", "unknown")
        if tool not in by_tool:
            by_tool[tool] = {"count": 0, "failed": 0, "total_ms": 0}
        by_tool[tool]["count"] += 1
        if status == "failed":
            by_tool[tool]["failed"] += 1
        by_tool[tool]["total_ms"] += action.get("duration_ms", 0)

        # 階段
        stage = action.get("stage", "unknown")
        if stage not in by_stage:
            by_stage[stage] = {"count": 0, "failed": 0}
        by_stage[stage]["count"] += 1
        if status == "failed":
            by_stage[stage]["failed"] += 1

        # Agent
        agent = action.get("agent_id", "unknown")
        by_agent[agent] = by_agent.get(agent, 0) + 1

        # 時間
        duration = action.get("duration_ms", 0)
        total_duration += duration
        slowest.append((duration, action))

    # 排序找出最慢的
    slowest.sort(key=lambda x: x[0], reverse=True)
    top_slowest = [
        {"duration_ms": d, "tool": a.get("tool"), "agent": a.get("agent_id")}
        for d, a in slowest[:10]
    ]

    return {
        "total": total,
        "by_status": by_status,
        "by_tool": by_tool,
        "by_stage": by_stage,
        "by_agent": by_agent,
        "total_duration_sec": round(total_duration / 1000, 2),
        "avg_duration_ms": round(total_duration / total, 2) if total > 0 else 0,
        "top_10_slowest": top_slowest,
    }


def print_stats(stats: dict[str, Any]) -> None:
    """列印統計資訊"""
    print("\n" + "=" * 60)
    print("行動日誌統計")
    print("=" * 60)

    print(f"\n總行動數: {stats['total']}")
    print(f"總執行時間: {stats.get('total_duration_sec', 0)} 秒")
    print(f"平均執行時間: {stats.get('avg_duration_ms', 0)} ms")

    # 狀態分佈
    print("\n--- 狀態分佈 ---")
    for status, count in stats.get("by_status", {}).items():
        pct = round(count / stats["total"] * 100, 1) if stats["total"] > 0 else 0
        icon = {"success": "✓", "failed": "✗", "timeout": "⏱"}.get(status, "?")
        print(f"  {icon} {status}: {count} ({pct}%)")

    # 工具統計
    print("\n--- 工具統計 ---")
    for tool, data in sorted(
        stats.get("by_tool", {}).items(), key=lambda x: x[1]["count"], reverse=True
    ):
        fail_rate = (
            round(data["failed"] / data["count"] * 100, 1) if data["count"] > 0 else 0
        )
        avg_ms = (
            round(data["total_ms"] / data["count"], 1) if data["count"] > 0 else 0
        )
        print(
            f"  {tool:12}: {data['count']:>4} 次, 失敗 {data['failed']:>2} ({fail_rate:>5.1f}%), 平均 {avg_ms:>6.1f}ms"
        )

    # 階段統計
    print("\n--- 階段統計 ---")
    stage_order = ["RESEARCH", "PLAN", "TASKS", "IMPLEMENT", "REVIEW", "VERIFY"]
    for stage in stage_order:
        if stage in stats.get("by_stage", {}):
            data = stats["by_stage"][stage]
            fail_rate = (
                round(data["failed"] / data["count"] * 100, 1)
                if data["count"] > 0
                else 0
            )
            print(
                f"  {stage:12}: {data['count']:>4} 次, 失敗 {data['failed']:>2} ({fail_rate:>5.1f}%)"
            )

    # 最慢行動
    print("\n--- 最慢的 10 個行動 ---")
    for i, item in enumerate(stats.get("top_10_slowest", []), 1):
        print(
            f"  {i:>2}. {item['duration_ms']:>6}ms - {item['tool']:10} ({item['agent']})"
        )

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Action Log Viewer - 行動級日誌查詢工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  %(prog)s --failed                    # 查看所有失敗的行動
  %(prog)s --agent agent_architecture  # 查看特定 Agent 的行動
  %(prog)s --slow 5000                 # 查看執行時間超過 5 秒的行動
  %(prog)s --tool Bash --stage IMPLEMENT  # 組合條件查詢
  %(prog)s --stats                     # 顯示統計資訊
        """,
    )

    # 過濾選項
    parser.add_argument("--failed", action="store_true", help="只顯示失敗的行動")
    parser.add_argument("--agent", type=str, help="過濾特定 Agent")
    parser.add_argument("--slow", type=int, metavar="MS", help="過濾執行時間超過 N 毫秒的行動")
    parser.add_argument(
        "--tool",
        type=str,
        choices=["Read", "Edit", "Write", "Bash", "Task", "Glob", "Grep", "WebFetch"],
        help="過濾特定工具",
    )
    parser.add_argument(
        "--stage",
        type=str,
        choices=["RESEARCH", "PLAN", "TASKS", "IMPLEMENT", "REVIEW", "VERIFY"],
        help="過濾特定階段",
    )
    parser.add_argument("--workflow", type=str, help="過濾特定工作流 ID")
    parser.add_argument(
        "--since",
        type=str,
        metavar="HOURS",
        help="只顯示最近 N 小時內的行動",
    )

    # 輸出選項
    parser.add_argument("-v", "--verbose", action="store_true", help="顯示詳細資訊")
    parser.add_argument("--stats", action="store_true", help="顯示統計資訊")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式輸出")
    parser.add_argument(
        "--limit", type=int, default=100, help="限制輸出行數 (預設: 100)"
    )

    # 輸入選項
    parser.add_argument("--file", type=Path, help="指定 actions.jsonl 檔案路徑")

    args = parser.parse_args()

    # 決定要讀取的檔案
    if args.file:
        log_files = [args.file] if args.file.exists() else []
    else:
        log_files = find_action_logs()

    if not log_files:
        print("找不到 actions.jsonl 檔案", file=sys.stderr)
        print("提示: 請確認在正確的專案目錄中，或使用 --file 指定檔案路徑", file=sys.stderr)
        sys.exit(1)

    # 處理 since 參數
    since_dt = None
    if args.since:
        try:
            hours = float(args.since)
            since_dt = datetime.now().astimezone() - timedelta(hours=hours)
        except ValueError:
            print(f"錯誤: --since 參數必須是數字 (小時)", file=sys.stderr)
            sys.exit(1)

    # 讀取所有日誌
    all_actions = []
    for log_file in log_files:
        actions = read_jsonl(log_file)
        filtered = filter_actions(
            actions,
            failed=args.failed,
            agent=args.agent,
            slow=args.slow,
            tool=args.tool,
            stage=args.stage,
            since=since_dt,
            workflow=args.workflow,
        )
        all_actions.extend(filtered)

    # 按時間排序
    all_actions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    # 統計模式
    if args.stats:
        stats = calculate_stats(all_actions)
        if args.json:
            print(json.dumps(stats, indent=2, ensure_ascii=False))
        else:
            print_stats(stats)
        return

    # 列表模式
    if args.json:
        # JSON 輸出
        output = all_actions[: args.limit] if args.limit else all_actions
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        # 表格輸出
        if not all_actions:
            print("沒有符合條件的行動記錄")
            return

        print(f"\n找到 {len(all_actions)} 筆記錄" + (f"（顯示前 {args.limit} 筆）" if len(all_actions) > args.limit else ""))
        print("-" * 90)
        print(f"{'狀態':^4} | {'時間':^19} | {'階段':^10} | {'Agent':^20} | {'工具':^10} | {'耗時':>8}")
        print("-" * 90)

        for action in all_actions[: args.limit]:
            print(format_action(action, verbose=args.verbose))


if __name__ == "__main__":
    main()
