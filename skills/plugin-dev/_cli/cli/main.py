"""
Multi-Agent Workflow CLI 入口

使用 Typer 建立命令行介面

命令：
- maw run "需求"              執行完整工作流
- maw run "需求" --start-from PLAN  從指定階段開始
- maw run "需求" --mode quick       快速模式
- maw current                  查看當前執行狀態
- maw status [workflow_id]     查看工作流狀態
- maw logs <workflow_id>       查看日誌
- maw list                     列出工作流
- maw validate <workflow_id>   驗證工作流
"""

from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from . import __version__
from .config.models import StageID, WorkflowMode
from .config.stages import STAGE_ORDER
from .io.memory import get_memory
from .io.state import read_current_state

app = typer.Typer(
    name="maw",
    help="Multi-Agent Workflow CLI - 混合架構編排器",
    add_completion=False,
)

console = Console()


# ─────────────────────────────────────────────────────────────────────────────
# 版本
# ─────────────────────────────────────────────────────────────────────────────


def version_callback(value: bool):
    if value:
        console.print(f"maw version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="顯示版本",
    ),
):
    """Multi-Agent Workflow CLI"""
    pass


# ─────────────────────────────────────────────────────────────────────────────
# run 命令
# ─────────────────────────────────────────────────────────────────────────────


@app.command()
def run(
    topic: str = typer.Argument(..., help="工作流主題/需求描述"),
    start_from: Optional[str] = typer.Option(
        None,
        "--start-from",
        "-s",
        help="從指定階段開始 (RESEARCH/PLAN/TASKS/IMPLEMENT/REVIEW/VERIFY)",
    ),
    skip: Optional[List[str]] = typer.Option(
        None,
        "--skip",
        help="跳過的階段",
    ),
    mode: str = typer.Option(
        "normal",
        "--mode",
        "-m",
        help="執行模式 (quick/normal/deep)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="只顯示計劃，不執行",
    ),
):
    """
    執行完整工作流

    Example:
        maw run "建立用戶認證系統"
        maw run "優化效能" --start-from IMPLEMENT
        maw run "新增功能" --mode quick
    """
    from .orchestrator.workflow import create_workflow

    console.print(Panel(f"[bold blue]Multi-Agent Workflow[/bold blue]\n{topic}"))

    # 驗證參數
    if start_from:
        try:
            StageID(start_from.upper())
        except ValueError:
            console.print(f"[red]無效的階段: {start_from}[/red]")
            console.print(f"有效階段: {', '.join(s.value for s in StageID)}")
            raise typer.Exit(1)

    if mode not in ["quick", "normal", "deep"]:
        console.print(f"[red]無效的模式: {mode}[/red]")
        console.print("有效模式: quick, normal, deep")
        raise typer.Exit(1)

    if dry_run:
        _show_plan(topic, start_from, skip, mode)
        return

    # 建立並執行工作流
    workflow = create_workflow(
        topic=topic,
        mode=mode,
        start_from=start_from,
        skip_stages=skip,
    )

    console.print(f"[dim]Workflow ID: {workflow.workflow_id}[/dim]")
    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("執行工作流...", total=None)

        result = workflow.run()

        progress.update(task, completed=True)

    # 顯示結果
    if result.success:
        console.print(Panel(
            f"[green]工作流完成[/green]\n"
            f"品質分數: {result.quality_score:.1f}\n"
            f"執行時間: {result.duration_seconds:.1f}s\n"
            f"迭代次數: {result.total_iterations}",
            title="Result",
        ))
    else:
        console.print(Panel(
            f"[red]工作流失敗[/red]\n"
            f"狀態: {result.final_status.value}\n"
            f"錯誤: {', '.join(result.errors)}",
            title="Result",
        ))
        raise typer.Exit(1)


def _show_plan(
    topic: str,
    start_from: Optional[str],
    skip: Optional[List[str]],
    mode: str,
):
    """顯示執行計劃"""
    console.print("\n[bold]執行計劃[/bold]\n")

    table = Table(show_header=True)
    table.add_column("階段", style="cyan")
    table.add_column("狀態", style="green")
    table.add_column("視角數")

    from .config.perspectives import STAGE_PERSPECTIVES, QUICK_MODE_PERSPECTIVES

    start_idx = 0
    if start_from:
        start_idx = [s.value for s in STAGE_ORDER].index(start_from.upper())

    skip_set = set(s.upper() for s in (skip or []))
    perspectives_map = QUICK_MODE_PERSPECTIVES if mode == "quick" else STAGE_PERSPECTIVES

    for i, stage in enumerate(STAGE_ORDER):
        if i < start_idx:
            status = "跳過 (start-from)"
        elif stage.value in skip_set:
            status = "跳過"
        else:
            status = "執行"

        perspectives = perspectives_map.get(stage, [])
        table.add_row(stage.value, status, str(len(perspectives)))

    console.print(table)
    console.print("\n[dim]使用 --dry-run=False 執行工作流[/dim]")


# ─────────────────────────────────────────────────────────────────────────────
# current 命令
# ─────────────────────────────────────────────────────────────────────────────


@app.command()
def current():
    """查看當前執行狀態"""
    memory = get_memory()
    workflow = memory.get_active_workflow()

    if not workflow:
        console.print("[yellow]沒有活動的工作流[/yellow]")
        return

    workflow_id = workflow.get("id", "unknown")

    try:
        state = read_current_state(workflow_id)
    except Exception:
        console.print("[yellow]無法讀取狀態[/yellow]")
        return

    # 顯示狀態
    console.print(Panel(
        f"[bold]{state['workflow'].get('topic', 'Unknown')}[/bold]",
        title=f"Workflow: {workflow_id}",
    ))

    # 階段資訊
    if stage := state.get("stage"):
        console.print(f"\n[cyan]Stage {stage['index']}/{stage['total']}:[/cyan] {stage['name']}")
        console.print(f"[dim]{stage['description']}[/dim]")

    # Agent 狀態
    if agents := state.get("agents"):
        console.print("\n[bold]Agents:[/bold]")

        table = Table(show_header=True, show_lines=False)
        table.add_column("ID", style="cyan")
        table.add_column("Name")
        table.add_column("Status")
        table.add_column("Task", max_width=40)

        status_icons = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
        }

        for agent in agents:
            icon = status_icons.get(agent.get("status", "pending"), "?")
            table.add_row(
                agent.get("id", ""),
                agent.get("name", ""),
                f"{icon} {agent.get('status', '')}",
                agent.get("task", "")[:40] if agent.get("task") else "",
            )

        console.print(table)

    # 進度
    progress = state.get("progress", {})
    completed = progress.get("agents_completed", 0)
    total = progress.get("agents_total", 0)
    if total > 0:
        console.print(f"\n[bold]Progress:[/bold] {completed}/{total} agents completed")


# ─────────────────────────────────────────────────────────────────────────────
# status 命令
# ─────────────────────────────────────────────────────────────────────────────


@app.command()
def status(
    workflow_id: Optional[str] = typer.Argument(None, help="工作流 ID"),
):
    """查看工作流狀態"""
    memory = get_memory()

    if workflow_id:
        # 查找特定工作流
        workflows = memory.list_workflows(limit=100)
        workflow = next(
            (w for w in workflows if workflow_id in w.get("id", "")),
            None,
        )
        if not workflow:
            console.print(f"[red]找不到工作流: {workflow_id}[/red]")
            raise typer.Exit(1)
    else:
        workflow = memory.get_active_workflow()
        if not workflow:
            console.print("[yellow]沒有活動的工作流[/yellow]")
            return

    # 顯示詳細狀態
    _show_workflow_status(workflow)


def _show_workflow_status(workflow: dict):
    """顯示工作流詳細狀態"""
    console.print(Panel(
        f"[bold]{workflow.get('topic', 'Unknown')}[/bold]\n"
        f"狀態: {workflow.get('status', 'unknown')}\n"
        f"階段: {workflow.get('current_stage', 'N/A')}\n"
        f"品質: {workflow.get('quality_score', 'N/A')}",
        title=f"Workflow: {workflow.get('id', 'unknown')}",
    ))

    # 階段狀態
    if stages := workflow.get("stages"):
        console.print("\n[bold]Stages:[/bold]")

        status_icons = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
        }

        for stage_id in [s.value for s in STAGE_ORDER]:
            stage_info = stages.get(stage_id.lower(), {})
            status = stage_info.get("status", "pending")
            icon = status_icons.get(status, "?")
            console.print(f"  {icon} {stage_id}")


# ─────────────────────────────────────────────────────────────────────────────
# list 命令
# ─────────────────────────────────────────────────────────────────────────────


@app.command(name="list")
def list_workflows(
    limit: int = typer.Option(10, "--limit", "-n", help="顯示數量"),
):
    """列出工作流"""
    memory = get_memory()
    workflows = memory.list_workflows(limit=limit)

    if not workflows:
        console.print("[yellow]沒有找到工作流[/yellow]")
        return

    table = Table(show_header=True)
    table.add_column("ID", style="cyan")
    table.add_column("Topic")
    table.add_column("Status")
    table.add_column("Quality")
    table.add_column("Date")

    status_icons = {
        "initialized": "⏳",
        "running": "🔄",
        "completed": "✅",
        "failed": "❌",
        "human_intervention": "👤",
    }

    for wf in workflows:
        status = wf.get("status", "unknown")
        icon = status_icons.get(status, "?")
        quality = wf.get("quality_score")
        quality_str = f"{quality:.1f}" if quality else "-"

        table.add_row(
            wf.get("id", "")[:25],
            (wf.get("topic", "") or "")[:30],
            f"{icon} {status}",
            quality_str,
            str(wf.get("date", ""))[:10],
        )

    console.print(table)


# ─────────────────────────────────────────────────────────────────────────────
# logs 命令
# ─────────────────────────────────────────────────────────────────────────────


@app.command()
def logs(
    workflow_id: str = typer.Argument(..., help="工作流 ID"),
    action: Optional[str] = typer.Option(None, "--action", "-a", help="篩選 action 類型"),
    level: Optional[str] = typer.Option(None, "--level", "-l", help="篩選 level"),
    limit: int = typer.Option(50, "--limit", "-n", help="顯示數量"),
):
    """查看工作流日誌"""
    from .io.logging import get_logger

    logger = get_logger(workflow_id)
    records = logger.get_logs(limit=limit)

    if not records:
        console.print("[yellow]沒有找到日誌[/yellow]")
        return

    # 篩選
    if action:
        records = [r for r in records if r.get("action") == action]
    if level:
        records = [r for r in records if r.get("level") == level]

    # 顯示
    level_colors = {
        "info": "white",
        "warning": "yellow",
        "error": "red",
    }

    for record in records[-limit:]:
        timestamp = record.get("timestamp", "")[:19]
        lvl = record.get("level", "info")
        act = record.get("action", "")
        details = record.get("details", {})

        color = level_colors.get(lvl, "white")

        # 格式化 details
        details_str = ""
        if details:
            key_values = [f"{k}={v}" for k, v in list(details.items())[:3]]
            details_str = " | " + ", ".join(key_values)

        console.print(f"[dim]{timestamp}[/dim] [{color}]{lvl:7}[/{color}] {act}{details_str}")


# ─────────────────────────────────────────────────────────────────────────────
# validate 命令
# ─────────────────────────────────────────────────────────────────────────────


@app.command()
def validate(
    workflow_id: str = typer.Argument(..., help="工作流 ID"),
    stage: Optional[str] = typer.Option(None, "--stage", "-s", help="驗證特定階段"),
):
    """驗證工作流"""
    memory = get_memory()

    workflow_dir = memory.get_workflow_dir(workflow_id)
    if not workflow_dir:
        console.print(f"[red]找不到工作流: {workflow_id}[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]驗證工作流: {workflow_id}[/bold]\n")

    # 檢查目錄結構
    console.print("[cyan]目錄結構:[/cyan]")
    required_dirs = ["stages", "agents", "logs"]
    for d in required_dirs:
        exists = (workflow_dir / d).exists()
        icon = "✅" if exists else "❌"
        console.print(f"  {icon} {d}/")

    # 檢查必要檔案
    console.print("\n[cyan]必要檔案:[/cyan]")
    required_files = ["meta.yaml", "current.json", "logs/actions.jsonl"]
    for f in required_files:
        exists = (workflow_dir / f).exists()
        icon = "✅" if exists else "❌"
        console.print(f"  {icon} {f}")

    # 驗證 meta.yaml
    meta = memory.read_yaml(workflow_dir / "meta.yaml")
    if meta:
        console.print("\n[cyan]Meta 驗證:[/cyan]")
        required_meta = ["id", "topic", "status"]
        for field in required_meta:
            exists = field in meta
            icon = "✅" if exists else "❌"
            console.print(f"  {icon} {field}")

    console.print("\n[green]驗證完成[/green]")


# ─────────────────────────────────────────────────────────────────────────────
# resume 命令
# ─────────────────────────────────────────────────────────────────────────────


@app.command()
def resume(
    workflow_id: str = typer.Argument(..., help="工作流 ID"),
    from_stage: Optional[str] = typer.Option(
        None,
        "--from",
        "-f",
        help="從指定階段恢復",
    ),
):
    """恢復中斷的工作流"""
    console.print(f"[bold]恢復工作流: {workflow_id}[/bold]")

    # TODO: 實作恢復邏輯
    console.print("[yellow]功能開發中...[/yellow]")


if __name__ == "__main__":
    app()
