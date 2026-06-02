#!/usr/bin/env python3
"""
Multi-Topic Dashboard - Show all active topics with ability to switch
Part of: Hierarchical Multi-Agent Orchestration System v2.1.0
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Optional

# Fix Windows console encoding
if sys.platform == "win32":
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich import box

# Find project root (where .claude directory is)
def find_project_root() -> Path:
    """Find project root by looking for .claude directory"""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude").exists():
            return current
        current = current.parent
    return Path.cwd()

# Change to project root
PROJECT_ROOT = find_project_root()
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT / ".claude/skills/agenthero-ai/scripts"))

# Now import utilities
from utils import read_json_file, log_info, log_error
from topic_manager import list_active_topics, get_topic_status

STATE_DIR = PROJECT_ROOT / ".claude/agents/state/agenthero-ai"
TOPICS_DIR = STATE_DIR / "topics"
TOPICS_FILE = STATE_DIR / "topics.json"

console = Console()


def get_all_topics() -> Dict[str, List[Dict]]:
    """
    Get all topics (active and completed)

    Returns:
        Dict with 'active' and 'completed' lists
    """
    if not TOPICS_FILE.exists():
        return {"active": [], "completed": []}

    data = read_json_file(TOPICS_FILE)
    if not data:
        return {"active": [], "completed": []}

    return {
        "active": data.get("active", []),
        "completed": data.get("completed", [])
    }


def get_topic_status(slug: str) -> Optional[Dict]:
    """
    Get topic status from topics.json

    Args:
        slug: Topic slug

    Returns:
        Topic data dict or None
    """
    topics_data = get_all_topics()
    active = topics_data.get("active", [])

    for topic in active:
        if topic.get("slug") == slug:
            return topic

    return None


def get_topic_tasks(slug: str) -> Dict:
    """
    Get task information for a topic

    Args:
        slug: Topic slug

    Returns:
        Dict with task counts and details
    """
    pm_state_file = TOPICS_DIR / slug / "pm-state.json"
    if not pm_state_file.exists():
        return {"tasks": [], "total": 0, "completed": 0, "in_progress": 0, "pending": 0}

    pm_data = read_json_file(pm_state_file)
    if not pm_data:
        return {"tasks": [], "total": 0, "completed": 0, "in_progress": 0, "pending": 0}

    tasks = pm_data.get("tasks", [])

    # Handle case where tasks might be a JSON string (double-encoded)
    if isinstance(tasks, str):
        try:
            tasks = json.loads(tasks)
        except json.JSONDecodeError:
            tasks = []

    # Count by status
    counts = {"completed": 0, "in_progress": 0, "pending": 0, "failed": 0}
    for task in tasks:
        status = task.get("status", "pending")
        counts[status] = counts.get(status, 0) + 1

    return {
        "tasks": tasks,
        "total": len(tasks),
        "completed": counts.get("completed", 0),
        "in_progress": counts.get("in_progress", 0),
        "pending": counts.get("pending", 0),
        "failed": counts.get("failed", 0)
    }


def display_multi_topic_dashboard():
    """Display dashboard showing all topics"""
    topics_data = get_all_topics()
    active_topics = topics_data.get("active", [])
    completed_topics = topics_data.get("completed", [])

    # Header
    console.print("\n[bold cyan]📋 Multi-Topic Dashboard[/bold cyan]")
    console.print("[dim]Switch between topics and manage multiple projects[/dim]\n")

    if not active_topics and not completed_topics:
        console.print("[yellow]No topics found. Create a new topic to get started.[/yellow]\n")
        return

    # Active Topics Table
    if active_topics:
        table = Table(
            title="Active Topics",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )

        table.add_column("No", style="bold cyan", width=5, justify="center")
        table.add_column("Topic", style="cyan", no_wrap=False, width=32)
        table.add_column("Progress", justify="center", width=16)
        table.add_column("Tasks", justify="center", width=18)
        table.add_column("Status", justify="center", width=18)
        table.add_column("Last Active", justify="right", width=12)

        for idx, topic in enumerate(active_topics, 1):
            slug = topic.get("slug", "")
            title = topic.get("title", "Unknown")
            progress = topic.get("progress", 0)
            completed = topic.get("completedTasks", 0)
            total = topic.get("totalTasks", 0)
            last_active = topic.get("lastActiveAt", "N/A")

            # Debug: print to see what we're processing
            # console.print(f"DEBUG: idx={idx}, title={title}")

            # Get detailed task info
            task_info = get_topic_tasks(slug)
            in_progress = task_info.get("in_progress", 0)
            pending = task_info.get("pending", 0)

            # Progress bar
            progress_bar = f"[green]{'█' * (progress // 10)}[/green]"
            progress_bar += f"[dim]{'░' * (10 - progress // 10)}[/dim]"
            progress_str = f"{progress_bar} {progress}%"

            # Tasks breakdown
            tasks_str = f"✅ {completed}/{total}"
            if in_progress > 0:
                tasks_str += f" 🔄 {in_progress}"
            if pending > 0:
                tasks_str += f" ⏳ {pending}"

            # Status
            if progress == 100:
                status_str = "[green]✓ Complete[/green]"
            elif in_progress > 0:
                status_str = f"[yellow]🔄 Active ({in_progress})[/yellow]"
            elif total > 0:
                status_str = "[cyan]⏸ Paused[/cyan]"
            else:
                status_str = "[dim]📝 Planning[/dim]"

            # Last active (relative time)
            if last_active and last_active != "N/A":
                from datetime import datetime
                try:
                    last_dt = datetime.fromisoformat(last_active.replace('+02:00', '+00:00'))
                    now = datetime.now(last_dt.tzinfo)
                    delta = now - last_dt

                    if delta.days > 0:
                        time_str = f"{delta.days}d ago"
                    elif delta.seconds > 3600:
                        time_str = f"{delta.seconds // 3600}h ago"
                    elif delta.seconds > 60:
                        time_str = f"{delta.seconds // 60}m ago"
                    else:
                        time_str = "just now"
                except:
                    time_str = "N/A"
            else:
                time_str = "N/A"

            # Format topic title (limit length)
            topic_display = f"[bold]{title[:28]}[/bold]"
            if len(title) > 28:
                topic_display += "..."

            table.add_row(
                f"[bold]{idx}[/bold]",
                topic_display,
                progress_str,
                tasks_str,
                status_str,
                time_str
            )

        console.print(table)
        console.print()

    # Completed Topics (if any)
    if completed_topics:
        console.print(f"\n[bold green]✓ Completed Topics:[/bold green] {len(completed_topics)}")
        for topic in completed_topics[:5]:  # Show max 5
            title = topic.get("title", "Unknown")
            completed_at = topic.get("completedAt", "N/A")
            console.print(f"  • [dim]{title}[/dim] ({completed_at})")
        if len(completed_topics) > 5:
            console.print(f"  [dim]... and {len(completed_topics) - 5} more[/dim]")
        console.print()

    # Instructions
    console.print("[bold]Actions:[/bold]")
    console.print("  1-9    → Switch to topic by number")
    console.print("  [cyan]n[/cyan]      → Create new topic")
    console.print("  [cyan]a[/cyan]      → Archive completed topics")
    console.print("  [cyan]q[/cyan]      → Quit dashboard\n")


def display_topic_summary(slug: str):
    """
    Display detailed summary for a specific topic

    Args:
        slug: Topic slug
    """
    topic_data = get_topic_status(slug)
    if not topic_data:
        console.print(f"[red]Topic not found: {slug}[/red]")
        return

    task_info = get_topic_tasks(slug)

    # Header
    title = topic_data.get("title", "Unknown")
    console.print(f"\n[bold cyan]📌 Topic: {title}[/bold cyan]")
    console.print(f"[dim]Slug: {slug}[/dim]\n")

    # Stats
    stats_table = Table(box=box.SIMPLE, show_header=False)
    stats_table.add_column("Label", style="dim")
    stats_table.add_column("Value", style="bold")

    progress = topic_data.get("progress", 0)
    total_tasks = task_info.get("total", 0)
    completed_tasks = task_info.get("completed", 0)
    in_progress_tasks = task_info.get("in_progress", 0)
    pending_tasks = task_info.get("pending", 0)

    stats_table.add_row("Progress", f"{progress}%")
    stats_table.add_row("Total Tasks", str(total_tasks))
    stats_table.add_row("Completed", f"[green]{completed_tasks}[/green]")
    stats_table.add_row("In Progress", f"[yellow]{in_progress_tasks}[/yellow]")
    stats_table.add_row("Pending", f"[cyan]{pending_tasks}[/cyan]")

    console.print(stats_table)
    console.print()

    # Task List
    if task_info.get("tasks"):
        console.print("[bold]Tasks:[/bold]")
        for task in task_info["tasks"][:10]:  # Show max 10
            task_id = task.get("id", "unknown")
            agent = task.get("agent", "unknown")
            desc = task.get("description", "No description")
            status = task.get("status", "pending")

            status_icon = {
                "completed": "✅",
                "in_progress": "🔄",
                "pending": "⏳",
                "failed": "❌"
            }.get(status, "❓")

            console.print(f"  {status_icon} [{task_id}] {agent}: {desc}")

        if len(task_info["tasks"]) > 10:
            console.print(f"  [dim]... and {len(task_info['tasks']) - 10} more tasks[/dim]")
        console.print()


def interactive_menu():
    """
    Interactive menu system - handle user input and perform actions
    """
    from topic_manager import create_topic, archive_topic, touch_topic

    while True:
        # Clear screen (optional - comment out if you don't want this)
        # console.clear()

        # Show dashboard
        display_multi_topic_dashboard()

        # Get topics for number selection
        topics_data = get_all_topics()
        active = topics_data.get("active", [])

        # Get user input
        console.print()
        user_input = console.input("[bold cyan]Choose an action:[/bold cyan] ").strip().lower()

        # Handle quit
        if user_input == 'q':
            console.print("\n[green]Goodbye![/green]\n")
            break

        # Handle new topic
        elif user_input == 'n':
            console.print("\n[bold]Create New Topic[/bold]")
            title = console.input("Topic title: ").strip()
            if not title:
                console.print("[yellow]Cancelled - no title provided[/yellow]")
                console.input("\nPress Enter to continue...")
                continue

            description = console.input("Description (optional): ").strip()

            # Create topic
            slug = create_topic(title, description)
            if slug:
                console.print(f"[green]✓ Created topic: {slug}[/green]")
            else:
                console.print("[red]✗ Failed to create topic[/red]")

            console.input("\nPress Enter to continue...")

        # Handle archive
        elif user_input == 'a':
            completed = topics_data.get("completed", [])
            if not completed:
                console.print("\n[yellow]No completed topics to archive[/yellow]")
                console.input("\nPress Enter to continue...")
                continue

            console.print("\n[bold]Completed Topics:[/bold]")
            for i, topic in enumerate(completed, 1):
                console.print(f"{i}. {topic.get('title')} - {topic.get('completedAt', 'N/A')}")

            console.print("\n[dim]Archive functionality coming soon...[/dim]")
            console.input("\nPress Enter to continue...")

        # Handle topic selection (1-9)
        elif user_input.isdigit():
            topic_num = int(user_input)
            if 1 <= topic_num <= len(active):
                topic = active[topic_num - 1]
                slug = topic.get('slug')

                # Touch topic (update last active)
                touch_topic(slug)

                # Launch monitor dashboard for this topic
                console.print(f"\n[bold cyan]📊 Loading dashboard for: {topic.get('title')}[/bold cyan]")
                console.print(f"[dim]Topic: {slug}[/dim]\n")

                import subprocess
                monitor_script = PROJECT_ROOT / ".claude/skills/agenthero-ai/scripts/monitor-dashboard.py"

                try:
                    # Launch monitor dashboard with --no-rich for basic mode
                    result = subprocess.run(
                        [sys.executable, str(monitor_script), "--topic", slug, "--no-rich"],
                        cwd=str(PROJECT_ROOT),
                        capture_output=False
                    )
                except KeyboardInterrupt:
                    console.print("\n[yellow]Dashboard closed[/yellow]")
                except Exception as e:
                    console.print(f"\n[red]Error launching dashboard: {e}[/red]")
                    console.print("[dim]Falling back to basic view...[/dim]\n")

                    # Fallback: show basic summary
                    display_topic_summary(slug)
                    task_info = get_topic_tasks(slug)

                    if task_info.get("tasks"):
                        console.print("\n[bold]📋 Task List:[/bold]")
                        for task in task_info["tasks"]:
                            task_id = task.get("id", "unknown")
                            agent = task.get("agent", "unknown")
                            desc = task.get("description", "No description")
                            status = task.get("status", "pending")

                            status_icon = {
                                "completed": "✅",
                                "in_progress": "🔄",
                                "pending": "⏳",
                                "failed": "❌"
                            }.get(status, "❓")

                            console.print(f"  {status_icon} [{task_id}] {agent}: {desc}")
                    else:
                        console.print("\n[dim]📝 No tasks in this topic yet[/dim]")

                # Get task info for menu options
                task_info = get_topic_tasks(slug)

                # Ask what to do
                console.print("\n[bold]What would you like to do?[/bold]")
                console.print("  [cyan]r[/cyan] - Return to main menu")
                console.print("  [cyan]c[/cyan] - Continue working (invoke agent)")

                action = console.input("\nAction: ").strip().lower()

                if action == 'c':
                    # Continue working - prepare to invoke agent
                    task_count = task_info.get("total", 0)

                    console.print(f"\n[bold cyan]📋 Preparing to resume work on: {topic.get('title')}[/bold cyan]")

                    if task_count == 0:
                        console.print("[yellow]⚠️  No tasks in this topic yet.[/yellow]")
                        console.print("[dim]The agent will ask you what you want to accomplish and create tasks.[/dim]\n")
                    else:
                        pending = task_info.get("pending", 0)
                        in_progress = task_info.get("in_progress", 0)
                        console.print(f"[green]✓ Found {task_count} task(s)[/green]")
                        if in_progress > 0:
                            console.print(f"  • {in_progress} in progress")
                        if pending > 0:
                            console.print(f"  • {pending} pending")
                        console.print()

                    # Create resume signal file
                    resume_file = STATE_DIR / "resume.json"
                    resume_data = {
                        "slug": slug,
                        "title": topic.get("title"),
                        "timestamp": topic.get("lastActiveAt"),
                        "taskCount": task_count
                    }

                    try:
                        import json
                        with open(resume_file, 'w') as f:
                            json.dump(resume_data, f, indent=2)
                        console.print(f"[green]✓ Resume signal created[/green]\n")
                    except Exception as e:
                        console.print(f"[yellow]⚠️  Could not create resume signal: {e}[/yellow]\n")

                    console.print("[bold]Next steps:[/bold]")
                    console.print("1. Exit this menu (it will exit automatically)")
                    console.print("2. In Claude CLI, invoke the agenthero-ai agent:")
                    console.print(f"   [cyan]\"Resume work on: {topic.get('title')}\"[/cyan]")
                    console.print()
                    console.print("[dim]The PM agent will load this topic and execute tasks via sub-agents.[/dim]")
                    console.print()

                    input_confirm = console.input("[bold]Press Enter to exit and invoke agent (or 'r' to return to menu): [/bold]").strip().lower()

                    if input_confirm != 'r':
                        # Exit the menu - user will invoke agent
                        console.print("\n[green]✓ Exiting menu. Ready to invoke agent in Claude CLI.[/green]\n")
                        return  # Exit the while loop, which exits the interactive menu
                    # else: continue loop (return to main menu)

                # 'r' or any other key returns to main menu
            else:
                console.print(f"\n[red]Invalid topic number. Please choose 1-{len(active)}[/red]")
                console.input("\nPress Enter to continue...")

        # Invalid input
        else:
            console.print(f"\n[red]Invalid option: {user_input}[/red]")
            console.print("[yellow]Please choose: 1-9 (topic number), n (new), a (archive), or q (quit)[/yellow]")
            console.input("\nPress Enter to continue...")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Multi-Topic Dashboard")
    parser.add_argument("--topic", help="Show specific topic details")
    parser.add_argument("--list", action="store_true", help="List all topics")
    parser.add_argument("--interactive", action="store_true", help="Interactive menu mode")

    args = parser.parse_args()

    if args.topic:
        display_topic_summary(args.topic)
    elif args.list:
        topics_data = get_all_topics()
        active = topics_data.get("active", [])
        for topic in active:
            console.print(f"{topic.get('slug')} - {topic.get('title')}")
    elif args.interactive:
        interactive_menu()
    else:
        # Default: show dashboard once (non-interactive)
        # For interactive mode, use --interactive flag
        display_multi_topic_dashboard()
