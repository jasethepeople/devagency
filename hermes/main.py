"""
Hermes CLI — central orchestrator for DevAgency.

Commands:
    hermes task "description [#tag]" [--review] [--files file1,file2]
    hermes list [--status pending|done|failed]
    hermes status <task_id>
    hermes vibes on|off
    hermes voice (requires whisper)
"""
import hashlib
import json
import sys
import time
import uuid
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agents.claude_agent import ClaudeAgent
from agents.codex_agent import CodexAgent
from agents.local_swarm import LocalOrchestrator
from config import Config
from hermes.db import TaskDB
from hermes.linear_client import LinearClient
from hermes.task_router import classify_task, extract_tags
from utils.logger import get_logger
from vibes.lofi import LofiPlayer

console = Console()
logger = get_logger("hermes.main")


def _task_id_from_description(description: str) -> str:
    """Generate a deterministic short task ID from description."""
    h = hashlib.sha256(description.encode()).hexdigest()[:8]
    return f"task-{h}"


@click.group()
@click.pass_context
def cli(ctx):
    """DevAgency — The Ultimate Vibe Coding Orchestrator."""
    Config.ensure_dirs()
    ctx.ensure_object(dict)
    ctx.obj["db"] = TaskDB()
    ctx.obj["linear"] = LinearClient()


@cli.command()
@click.argument("description")
@click.option("--review", is_flag=True, help="Enable chain-of-thought review for local tasks")
@click.option("--files", default="", help="Comma-separated list of project files to include as context")
@click.pass_context
def task(ctx, description: str, review: bool, files: str):
    """Submit a new coding task."""
    db: TaskDB = ctx.obj["db"]
    linear: LinearClient = ctx.obj["linear"]

    task_id = _task_id_from_description(description)
    tags = extract_tags(description)

    console.print(Panel.fit(
        f"[bold cyan]Task:[/bold cyan] {description}\n"
        f"[bold yellow]Tags:[/bold yellow] {', '.join(tags) if tags else 'none'}\n"
        f"[bold green]ID:[/bold green] {task_id}",
        title="Hermes Orchestrator",
        border_style="blue",
    ))

    # 1. Classify
    agent_type = classify_task(description)
    console.print(f"[dim]Router decision:[/dim] [bold]{agent_type}[/bold]")

    # 2. Create Linear issue
    issue_id = ""
    if linear.api_key:
        issue_id = linear.create_issue(
            title=description[:100],
            description=f"Task ID: {task_id}\n\n{description}",
            label=agent_type,
        )
        if issue_id:
            linear.comment(issue_id, f"Agent selected: {agent_type}. Starting execution...")

    # 3. Record in DB
    db.create_task(task_id, description, tags, agent_type, issue_id)

    # 4. Build context from files
    context: dict = {}
    if files:
        file_map = {}
        for fpath in files.split(","):
            p = Path(fpath.strip())
            if p.exists():
                file_map[p.name] = p.read_text(encoding="utf-8")
            else:
                console.print(f"[yellow]Warning: file not found: {p}[/yellow]")
        context["files"] = file_map

    # 5. Dispatch to agent
    db.update_status(task_id, "in_progress")
    if issue_id:
        linear.comment(issue_id, "Status: In Progress")

    result = {}
    try:
        if agent_type == "codex":
            agent = CodexAgent()
            result = agent.execute({"id": task_id, "description": description, "tags": tags}, context)
        elif agent_type == "claude":
            agent = ClaudeAgent()
            result = agent.execute({"id": task_id, "description": description, "tags": tags}, context)
        else:  # local
            agent = LocalOrchestrator()
            result = agent.execute(
                {"id": task_id, "description": description, "tags": tags, "review": review},
                context,
            )

        # 6. Update DB + Linear
        if result.get("success"):
            db.update_status(task_id, "done", result=result)
            if issue_id:
                linear.comment(issue_id, f"Completed.\n\nModel: {result.get('model_used', 'unknown')}\nFiles: {len(result.get('files', []))}")
            console.print(Panel.fit(
                f"[bold green]Success![/bold green]\n"
                f"Model: {result.get('model_used', 'unknown')}\n"
                f"Files: {len(result.get('files', []))}\n"
                f"Workspace: {result.get('workspace_path', 'N/A')}",
                title="Task Complete",
                border_style="green",
            ))
        else:
            error = result.get("error", "Unknown error")
            db.update_status(task_id, "failed", error=error)
            if issue_id:
                linear.comment(issue_id, f"Failed: {error}")
            console.print(Panel.fit(f"[bold red]Failed:[/bold red] {error}", title="Error", border_style="red"))

    except Exception as e:
        db.update_status(task_id, "failed", error=str(e))
        if issue_id:
            linear.comment(issue_id, f"Exception: {e}")
        console.print(Panel.fit(f"[bold red]Exception:[/bold red] {e}", title="Error", border_style="red"))
        raise


@cli.command()
@click.option("--status", default=None, help="Filter by status: pending, in_progress, done, failed")
@click.pass_context
def list(ctx, status: Optional[str]):
    """List all tasks."""
    db: TaskDB = ctx.obj["db"]
    tasks = db.list_tasks(status=status, limit=50)

    table = Table(title="DevAgency Tasks")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Agent", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Description", style="white")
    table.add_column("Created", style="dim")

    for t in tasks:
        table.add_row(
            t["id"],
            t["agent"],
            t["status"],
            t["description"][:60],
            t["created_at"][:19] if t["created_at"] else "",
        )

    console.print(table)


@cli.command()
@click.argument("task_id")
@click.pass_context
def status(ctx, task_id: str):
    """Check detailed status of a task."""
    db: TaskDB = ctx.obj["db"]
    task = db.get_task(task_id)

    if not task:
        console.print(f"[red]Task {task_id} not found[/red]")
        return

    console.print(Panel.fit(
        f"[bold]ID:[/bold] {task['id']}\n"
        f"[bold]Agent:[/bold] {task['agent']}\n"
        f"[bold]Status:[/bold] {task['status']}\n"
        f"[bold]Description:[/bold] {task['description']}\n"
        f"[bold]Model:[/bold] {task.get('model_used', 'N/A')}\n"
        f"[bold]Linear Issue:[/bold] {task.get('linear_issue_id', 'N/A')}",
        title="Task Status",
    ))

    if task.get("result_json"):
        result = json.loads(task["result_json"])
        console.print(f"\n[bold]Files generated:[/bold]")
        for f in result.get("files", []):
            console.print(f"  - {f['filename']}")
        if result.get("comments"):
            console.print(f"\n[bold]Comments:[/bold]")
            for c in result["comments"][:3]:
                console.print(f"  • {c[:100]}...")

    if task.get("error"):
        console.print(f"\n[red]Error: {task['error']}[/red]")


@cli.command()
@click.argument("action", type=click.Choice(["on", "off"]))
def vibes(action: str):
    """Toggle lo-fi background music."""
    player = LofiPlayer()
    if action == "on":
        if player.start():
            console.print("[green]Lo-fi vibes ON[/green]")
        else:
            console.print("[red]Failed to start lo-fi. Is mpv installed?[/red]")
    else:
        if player.stop():
            console.print("[yellow]Lo-fi vibes OFF[/yellow]")


@cli.command()
def voice():
    """Record voice input and transcribe (requires whisper)."""
    console.print("[yellow]Voice input not yet implemented.[/yellow]")
    console.print("Install whisper and sounddevice, then run:")
    console.print("  [dim]hermes voice[/dim]")
    console.print("\nTo use voice, ensure these are in requirements.txt:")
    console.print("  openai-whisper, sounddevice, numpy")


if __name__ == "__main__":
    cli()
