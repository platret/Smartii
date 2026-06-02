#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Orchestration Monitor Dashboard (Python Version)
Real-time monitoring of active topics and sub-agent tasks with interactive controls
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Force UTF-8 encoding for Windows
if sys.platform == "win32":
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, TextColumn
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: 'rich' library not found. Install with: pip install rich")
    print("Falling back to basic display...")

# Constants
STATE_DIR = Path(".claude/agents/state/agenthero-ai")
TOPICS_DIR = STATE_DIR / "topics"
TOPICS_FILE = STATE_DIR / "topics.json"
DEFAULT_INTERVAL = 6  # seconds

# Status icons
STATUS_ICONS = {
    "completed": "✓",
    "in_progress": "⟳",
    "pending": "○",
    "blocked": "⚠",
    "failed": "✗"
}

# Status colors (for rich)
STATUS_COLORS = {
    "completed": "green",
    "in_progress": "yellow",
    "pending": "blue",
    "blocked": "red",
    "failed": "red"
}


def time_ago(timestamp_str: Optional[str]) -> str:
    """Convert ISO timestamp to human-readable time ago format."""
    if not timestamp_str or timestamp_str == "null":
        return "N/A"

    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
        diff = (now - timestamp).total_seconds()

        if diff < 60:
            return f"{int(diff)}s ago"
        elif diff < 3600:
            return f"{int(diff / 60)}m ago"
        elif diff < 86400:
            return f"{int(diff / 3600)}h ago"
        else:
            return f"{int(diff / 86400)}d ago"
    except Exception:
        return "N/A"


def load_json_file(file_path: Path) -> Optional[Dict]:
    """Load and parse JSON file."""
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}", file=sys.stderr)
    return None


def get_progress_bar(progress: int, width: int = 20) -> str:
    """Generate ASCII progress bar."""
    filled = int(progress * width / 100)
    empty = width - filled
    return "█" * filled + "░" * empty


def get_topic_data(topic_slug: str) -> Optional[Dict]:
    """Get topic metadata and task progress."""
    topic_dir = TOPICS_DIR / topic_slug
    if not topic_dir.is_dir():
        return None

    # Load topic metadata
    topic_json = topic_dir / "topic.json"
    topic_data = load_json_file(topic_json)
    if not topic_data:
        return None

    # Load PM state with all tasks
    pm_state_file = topic_dir / "pm-state.json"
    pm_state = load_json_file(pm_state_file)

    # Count tasks and calculate progress
    total_tasks = 0
    completed_tasks = 0
    in_progress_tasks = 0
    tasks = []

    if pm_state and "tasks" in pm_state:
        tasks_list = pm_state.get("tasks", [])

        # Handle case where tasks might be a JSON string (double-encoded)
        if isinstance(tasks_list, str):
            try:
                tasks_list = json.loads(tasks_list)
            except json.JSONDecodeError:
                tasks_list = []

        total_tasks = len(tasks_list)

        for task_data in tasks_list:
            status = task_data.get("status", "pending")
            if status == "completed":
                completed_tasks += 1
            elif status == "in_progress":
                in_progress_tasks += 1

            # Transform task data to match old format for display
            transformed_task = {
                "taskId": task_data.get("id", "unknown"),
                "agentName": task_data.get("agent", ""),
                "focusArea": task_data.get("description", "Unknown"),
                "status": status,
                "progress": 100 if status == "completed" else 50 if status == "in_progress" else 0,
                "dependencies": task_data.get("dependencies", []),
                "startedAt": task_data.get("createdAt"),
                "currentOperation": task_data.get("description", ""),
                "logs": [],
                "filesCreated": [],
                "filesModified": [],
                "waitingFor": [],
                "canStart": len(task_data.get("dependencies", [])) == 0
            }
            tasks.append(transformed_task)

    # Calculate progress
    progress = (completed_tasks * 100 // total_tasks) if total_tasks > 0 else 0

    return {
        "title": topic_data.get("title", "Unknown"),
        "slug": topic_slug,
        "status": topic_data.get("status", "active"),
        "created": topic_data.get("createdAt"),
        "last_active": topic_data.get("lastActiveAt"),
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "progress": progress,
        "tasks": tasks
    }


def create_basic_display(topics_data: List[Dict]) -> str:
    """Create basic text display (fallback when rich is not available)."""
    output = []
    output.append("=" * 64)
    output.append("Project Orchestration Dashboard")
    output.append("Real-time monitoring of parallel sub-agent tasks")
    output.append("=" * 64)
    output.append("")

    if not topics_data:
        output.append("No active topics.")
        output.append("")
        output.append("Run: python .claude/skills/agenthero-ai/scripts/topic_manager.py create_topic \"Your Topic\" --description \"Description\"")
        return "\n".join(output)

    output.append(f"Active Topics: {len(topics_data)} | Press 'r' to refresh, 'q' to quit")
    output.append("")

    for topic in topics_data:
        output.append(f"📋 Topic: {topic['title']}")
        output.append(f"   Slug: {topic['slug']}")
        output.append(f"   Created: {time_ago(topic['created'])}")
        output.append(f"   Last Active: {time_ago(topic['last_active'])}")
        output.append(f"   Progress: {get_progress_bar(topic['progress'])} {topic['progress']}% ({topic['completed_tasks']}/{topic['total_tasks']} tasks)")
        output.append("")
        output.append("   Sub-Agent Tasks:")
        output.append("")

        for task in topic['tasks']:
            task_id = task.get("taskId", "unknown")
            agent_name = task.get("agentName", "")
            focus = task.get("focusArea", "Unknown")
            status = task.get("status", "unknown")
            progress = task.get("progress", 0)
            current_op = task.get("currentOperation", "N/A")
            started = task.get("startedAt")
            logs = task.get("logs", [])
            files_created = len(task.get("filesCreated", []))
            dependencies = task.get("dependencies", [])
            waiting_for = task.get("waitingFor", [])
            files_modified = len(task.get("filesModified", []))

            latest_log = logs[-1].get("message", "No logs yet") if logs else "No logs yet"
            latest_time = logs[-1].get("timestamp") if logs else None

            icon = STATUS_ICONS.get(status, "?")
            output.append(f"   {icon} {task_id} ({focus})")
            if agent_name:
                output.append(f"      Agent: {agent_name}")
            output.append(f"      Status: {status} {get_progress_bar(progress)} {progress}%")

            if waiting_for:
                output.append(f"      Waiting for: {', '.join(waiting_for)}")

            if status in ["in_progress", "completed"]:
                output.append(f"      Current: {current_op}")
                output.append(f"      Started: {time_ago(started)}")
                output.append(f"      Latest: {latest_log} ({time_ago(latest_time)})")

            files_info = f"Logs: {len(logs)} | Files: +{files_created} ~{files_modified}"
            if dependencies:
                files_info += f" | Deps: {len(dependencies)}"
            output.append(f"      {files_info}")
            output.append("")

        output.append("-" * 64)
        output.append("")

    output.append(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("")
    output.append("Controls: [r] Refresh  [q] Quit  [+] Faster  [-] Slower")

    return "\n".join(output)


def create_rich_display(topics_data: List[Dict]) -> Layout:
    """Create rich terminal display with panels and tables."""
    console = Console()
    layout = Layout()

    # Header
    header = Panel(
        "[bold cyan]Project Orchestration Dashboard[/bold cyan]\n"
        "[dim]Real-time monitoring of parallel sub-agent tasks[/dim]",
        border_style="cyan"
    )

    if not topics_data:
        content = Panel(
            "[yellow]No active topics.[/yellow]\n\n"
            "Run: [cyan]python .claude/skills/agenthero-ai/scripts/topic_manager.py create_topic \"Your Topic\" --description \"Description\"[/cyan]",
            border_style="yellow"
        )
        layout.split_column(
            Layout(header, size=5),
            Layout(content)
        )
        return layout

    # Topics content
    topics_panels = []
    for topic in topics_data:
        # Topic header
        topic_header = Text()
        topic_header.append("📋 Topic: ", style="bold magenta")
        topic_header.append(topic['title'], style="bold")

        # Topic info
        topic_info = Table.grid(padding=(0, 2))
        topic_info.add_row("[dim]Slug:[/dim]", topic['slug'])
        topic_info.add_row("[dim]Created:[/dim]", time_ago(topic['created']))
        topic_info.add_row("[dim]Last Active:[/dim]", time_ago(topic['last_active']))

        # Progress bar
        progress_bar = get_progress_bar(topic['progress'])
        progress_color = "green" if topic['progress'] == 100 else "yellow" if topic['progress'] > 0 else "dim"
        progress_text = f"[{progress_color}]{progress_bar}[/{progress_color}] {topic['progress']}% [dim]({topic['completed_tasks']}/{topic['total_tasks']} tasks)[/dim]"
        topic_info.add_row("[dim]Progress:[/dim]", progress_text)

        # Tasks table
        tasks_table = Table(show_header=True, header_style="bold cyan", border_style="dim")
        tasks_table.add_column("Status", width=6)
        tasks_table.add_column("Task", width=22)
        tasks_table.add_column("Progress", width=20)
        tasks_table.add_column("Details", width=42)

        for task in topic['tasks']:
            task_id = task.get("taskId", "unknown")
            agent_name = task.get("agentName", "")
            focus = task.get("focusArea", "Unknown")
            status = task.get("status", "unknown")
            progress = task.get("progress", 0)
            logs = task.get("logs", [])
            files_created = len(task.get("filesCreated", []))
            files_modified = len(task.get("filesModified", []))
            dependencies = task.get("dependencies", [])
            waiting_for = task.get("waitingFor", [])
            can_start = task.get("canStart", True)

            latest_log = logs[-1].get("message", "No logs yet") if logs else "No logs yet"
            latest_time = logs[-1].get("timestamp") if logs else None

            # Status icon with color
            icon = STATUS_ICONS.get(status, "?")
            color = STATUS_COLORS.get(status, "white")
            status_cell = f"[{color}]{icon}[/{color}]"

            # Task name with agent
            task_cell = f"[bold]{task_id}[/bold]\n[dim]{focus}[/dim]"
            if agent_name:
                task_cell += f"\n[cyan dim]→ {agent_name}[/cyan dim]"

            # Progress bar
            progress_bar = get_progress_bar(progress)
            progress_color = "green" if progress == 100 else "yellow" if progress > 0 else "dim"
            progress_cell = f"[{progress_color}]{progress_bar}[/{progress_color}] {progress}%"

            # Add dependency info if waiting
            if waiting_for:
                progress_cell += f"\n[yellow]⏸ Waiting: {', '.join(waiting_for)}[/yellow]"

            # Details
            details = f"[dim]Logs:[/dim] {len(logs)} | [dim]Files:[/dim] +{files_created} ~{files_modified}"
            if dependencies:
                details += f" | [dim]Deps:[/dim] {len(dependencies)}"
            details += "\n"
            if latest_log and len(latest_log) > 50:
                details += f"[dim]{latest_log[:47]}...[/dim]"
            else:
                details += f"[dim]{latest_log}[/dim]"

            tasks_table.add_row(status_cell, task_cell, progress_cell, details)

        # Combine into panel
        topic_content = Table.grid()
        topic_content.add_row(topic_header)
        topic_content.add_row("")
        topic_content.add_row(topic_info)
        topic_content.add_row("")
        topic_content.add_row("[bold cyan]Sub-Agent Tasks:[/bold cyan]")
        topic_content.add_row(tasks_table)

        panel = Panel(topic_content, border_style="magenta")
        topics_panels.append(panel)

    # Footer
    footer = Panel(
        f"[dim]Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]\n"
        "[cyan]Controls:[/cyan] [bold]r[/bold]=Refresh | [bold]q[/bold]=Quit | [bold]+[/bold]=Faster | [bold]-[/bold]=Slower",
        border_style="dim"
    )

    # Combine all
    content_layout = Layout()
    for panel in topics_panels:
        content_layout = Layout(panel)

    layout.split_column(
        Layout(header, size=5),
        Layout(content_layout),
        Layout(footer, size=4)
    )

    return layout


def get_all_topics() -> List[Dict]:
    """Get all active topics with their data."""
    if not TOPICS_FILE.exists():
        return []

    topics_json = load_json_file(TOPICS_FILE)
    if not topics_json:
        return []

    active_topics = topics_json.get("active", [])
    topics_data = []

    for topic_entry in active_topics:
        slug = topic_entry.get("slug")
        if slug:
            topic_data = get_topic_data(slug)
            if topic_data:
                topics_data.append(topic_data)

    return topics_data


def main():
    """Main dashboard function."""
    import argparse

    parser = argparse.ArgumentParser(description="Project Orchestration Monitor Dashboard")
    parser.add_argument("-w", "--watch", action="store_true", help="Watch mode (continuous updates)")
    parser.add_argument("-i", "--interval", type=int, default=DEFAULT_INTERVAL, help=f"Update interval in seconds (default: {DEFAULT_INTERVAL})")
    parser.add_argument("--no-rich", action="store_true", help="Disable rich UI (use basic display)")
    parser.add_argument("--topic", type=str, help="Show only specific topic (by slug)")

    args = parser.parse_args()

    use_rich = RICH_AVAILABLE and not args.no_rich

    if not args.watch:
        # Single snapshot
        topics_data = get_all_topics()

        # Filter to specific topic if requested
        if args.topic:
            filtered_topics = [t for t in topics_data if t.get('slug') == args.topic]
            if not filtered_topics:
                print(f"Topic not found: {args.topic}")
                return
            topics_data = filtered_topics

        if use_rich:
            console = Console()
            console.print(create_rich_display(topics_data))
        else:
            print(create_basic_display(topics_data))
        return

    # Watch mode
    interval = args.interval

    if use_rich:
        console = Console()
        console.print(f"[green]Starting watch mode (refresh every {interval}s)...[/green]")
        console.print("[dim]Press Ctrl+C to exit[/dim]\n")
        time.sleep(1)

        try:
            while True:
                topics_data = get_all_topics()

                # Filter to specific topic if requested
                if args.topic:
                    filtered_topics = [t for t in topics_data if t.get('slug') == args.topic]
                    topics_data = filtered_topics if filtered_topics else []

                console.clear()
                console.print(create_rich_display(topics_data))
                time.sleep(interval)
        except KeyboardInterrupt:
            console.print("\n[yellow]Monitor stopped.[/yellow]")
    else:
        print(f"Starting watch mode (refresh every {interval}s)...")
        print("Press Ctrl+C to exit\n")

        try:
            while True:
                topics_data = get_all_topics()

                # Filter to specific topic if requested
                if args.topic:
                    filtered_topics = [t for t in topics_data if t.get('slug') == args.topic]
                    topics_data = filtered_topics if filtered_topics else []

                os.system('cls' if os.name == 'nt' else 'clear')
                print(create_basic_display(topics_data))
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitor stopped.")


if __name__ == "__main__":
    main()
