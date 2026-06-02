#!/usr/bin/env python3
"""
Topic Manager - Topic lifecycle management (V2.0)
Part of: Hierarchical Multi-Agent Orchestration System v2.0.0 (Python)
"""

import sys
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Optional

# Import utilities
from utils import (
    log_info, log_warn, log_error,
    timestamp_iso, atomic_write, ensure_directory,
    read_json_file, slugify, validate_json, find_project_root
)


# Find project root and set absolute paths
PROJECT_ROOT = find_project_root()
STATE_DIR = PROJECT_ROOT / ".claude/agents/state/agenthero-ai"
TOPICS_DIR = STATE_DIR / "topics"
ARCHIVE_DIR = STATE_DIR / "archive"
TOPICS_FILE = STATE_DIR / "topics.json"


def init_topics_registry() -> None:
    """Initialize topics registry if it doesn't exist (V2.0 structure)"""
    if not TOPICS_FILE.exists():
        ensure_directory(STATE_DIR)
        ensure_directory(TOPICS_DIR)
        ensure_directory(ARCHIVE_DIR)
        atomic_write(TOPICS_FILE, {
            "version": "2.0.0",
            "lastUpdated": timestamp_iso(),
            "topics": []
        })
        log_info("Initialized topics registry (V2.0)")


def create_topic(title: str, description: str = "", user_request: str = "") -> Optional[str]:
    """
    Create new topic (V2.0 - single topics.json entry)

    Args:
        title: Topic title
        description: Optional topic description
        user_request: Optional original user request

    Returns:
        Topic slug if successful, None otherwise
    """
    init_topics_registry()

    slug = slugify(title)
    topic_dir = TOPICS_DIR / slug
    timestamp = timestamp_iso()

    # Check if topic already exists
    if topic_dir.exists():
        log_error(f"Topic already exists: {slug}")
        return None

    # Create topic directory (for task files)
    ensure_directory(topic_dir)

    # Create messages queue (for multi-agent communication)
    messages_file = topic_dir / "messages.json"
    atomic_write(messages_file, [])

    # Add to topics.json (single source of truth in V2.0)
    registry_data = read_json_file(TOPICS_FILE)
    if registry_data is None:
        return None

    topic_entry = {
        "slug": slug,
        "title": title,
        "description": description,
        "status": "in_progress",
        "currentPhase": "requirements-analysis",
        "createdAt": timestamp,
        "lastActiveAt": timestamp,
        "completedAt": None,
        "userRequest": user_request or title,
        "tasks": [],
        "totalTasks": 0,
        "completedTasks": 0,
        "progress": 0.0,
        "files": {
            "topicPlan": f"Project-tasks/{slug}/topicplan.md",
            "spec": f"Project-tasks/{slug}/spec/original-spec.md",
            "deliverables": f"Project-tasks/{slug}/deliverables/",
            "qaReport": f"Project-tasks/{slug}/QA-REPORT.md"
        },
        "tokenUsage": {
            "total": 0,
            "pmAgent": 0,
            "subAgents": {},
            "estimated": 0,
            "savings": 0,
            "savingsPercent": 0
        }
    }

    registry_data["topics"].append(topic_entry)
    registry_data["lastUpdated"] = timestamp
    atomic_write(TOPICS_FILE, registry_data)

    log_info(f"Created topic: {slug}")
    return slug


def list_active_topics() -> List[Dict]:
    """
    List all active topics (V2.0 - filter from topics array)

    Returns:
        List of active topic dicts
    """
    init_topics_registry()

    data = read_json_file(TOPICS_FILE)
    if data is None or 'topics' not in data:
        return []

    # Filter for non-completed topics
    return [t for t in data['topics'] if t.get('status') != 'completed']


def list_completed_topics() -> List[Dict]:
    """
    List all completed topics (V2.0 - filter from topics array)

    Returns:
        List of completed topic dicts
    """
    init_topics_registry()

    data = read_json_file(TOPICS_FILE)
    if data is None or 'topics' not in data:
        return []

    # Filter for completed topics
    return [t for t in data['topics'] if t.get('status') == 'completed']


def get_topic_status(slug: str) -> Optional[Dict]:
    """
    Get topic status (V2.0 - read from topics.json)

    Args:
        slug: Topic slug

    Returns:
        Topic dict or None if not found
    """
    data = read_json_file(TOPICS_FILE)
    if data is None or 'topics' not in data:
        return None

    for topic in data['topics']:
        if topic['slug'] == slug:
            return topic

    log_error(f"Topic not found: {slug}")
    return None


def touch_topic(slug: str) -> bool:
    """
    Update topic last active time (V2.0 - update topics.json)

    Args:
        slug: Topic slug

    Returns:
        True if successful, False otherwise
    """
    timestamp = timestamp_iso()

    registry_data = read_json_file(TOPICS_FILE)
    if registry_data is None:
        return False

    topic_found = False
    for topic in registry_data.get("topics", []):
        if topic["slug"] == slug:
            topic["lastActiveAt"] = timestamp
            topic_found = True
            break

    if not topic_found:
        log_error(f"Topic not found: {slug}")
        return False

    registry_data["lastUpdated"] = timestamp
    atomic_write(TOPICS_FILE, registry_data)
    log_info(f"Updated topic activity: {slug}")
    return True


def update_topic_progress(slug: str) -> bool:
    """
    Update topic progress based on completed tasks (V2.0 - read task files)

    Args:
        slug: Topic slug

    Returns:
        True if successful, False otherwise
    """
    topic_dir = TOPICS_DIR / slug

    if not topic_dir.exists():
        log_error(f"Topic directory not found: {slug}")
        return False

    # Read all task files to calculate progress
    task_files = list(topic_dir.glob("task-*.json"))
    total_tasks = len(task_files)
    completed_tasks = 0
    task_summaries = []

    for task_file in sorted(task_files):
        task_data = read_json_file(task_file)
        if task_data is None:
            continue

        status = task_data.get('status', 'unknown')
        if status == 'completed':
            completed_tasks += 1

        # Build task summary
        task_summaries.append({
            "id": task_file.stem,
            "name": task_data.get('focusArea', task_data.get('description', 'Unknown')),
            "agent": task_data.get('agentName', task_data.get('assignedTo', 'unknown')),
            "status": status,
            "progress": task_data.get('progress', 0)
        })

    progress = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0

    # Update topics.json
    registry_data = read_json_file(TOPICS_FILE)
    if registry_data is None:
        return False

    topic_found = False
    for topic in registry_data.get("topics", []):
        if topic["slug"] == slug:
            topic["progress"] = progress
            topic["completedTasks"] = completed_tasks
            topic["totalTasks"] = total_tasks
            topic["tasks"] = task_summaries
            topic["lastActiveAt"] = timestamp_iso()
            topic_found = True
            break

    if not topic_found:
        log_error(f"Topic not found in registry: {slug}")
        return False

    registry_data["lastUpdated"] = timestamp_iso()
    atomic_write(TOPICS_FILE, registry_data)
    log_info(f"Updated topic progress: {slug} ({progress}%)")
    return True


def archive_topic(slug: str) -> bool:
    """
    Archive completed topic (V2.0 - move directory, keep in topics.json)

    Args:
        slug: Topic slug

    Returns:
        True if successful, False otherwise
    """
    topic_dir = TOPICS_DIR / slug
    archive_dir = ARCHIVE_DIR / slug

    if not topic_dir.exists():
        log_error(f"Topic not found: {slug}")
        return False

    # Ensure archive directory exists
    ensure_directory(ARCHIVE_DIR)

    try:
        # Move topic directory to archive
        shutil.move(str(topic_dir), str(archive_dir))

        # Topic stays in topics.json but marked as completed
        # (Dashboard can filter by status)

        log_info(f"Archived topic: {slug}")
        return True

    except Exception as e:
        log_error(f"Failed to archive topic: {e}")
        # Attempt rollback
        if archive_dir.exists() and not topic_dir.exists():
            shutil.move(str(archive_dir), str(topic_dir))
        return False


def resume_topic(slug: str) -> Optional[Dict]:
    """
    Resume topic (update last active and return status)

    Args:
        slug: Topic slug

    Returns:
        Topic dict or None if failed
    """
    topic_dir = TOPICS_DIR / slug

    if not topic_dir.exists():
        log_error(f"Topic not found: {slug}")
        return None

    # Touch topic to update last active
    touch_topic(slug)

    # Return topic status
    return get_topic_status(slug)


def get_active_topics_summary() -> str:
    """
    Get summary of active topics for session start (V2.0)

    Returns:
        Summary string (always returns a message)
    """
    active_topics = list_active_topics()

    if not active_topics:
        return "No pending topics - ready for new work!"

    summary = [f"Found {len(active_topics)} active topic(s):"]
    for topic in active_topics:
        title = topic.get("title", "Unknown")
        progress = topic.get("progress", 0)
        completed = topic.get("completedTasks", 0)
        total = topic.get("totalTasks", 0)
        summary.append(f"  • {title} ({progress}% complete, {completed}/{total} tasks)")

    return "\n".join(summary)


def complete_topic(slug: str) -> bool:
    """
    Mark topic as completed (V2.0 - update topics.json)

    Args:
        slug: Topic slug

    Returns:
        True if successful, False otherwise
    """
    timestamp = timestamp_iso()

    registry_data = read_json_file(TOPICS_FILE)
    if registry_data is None:
        return False

    topic_found = False
    for topic in registry_data.get("topics", []):
        if topic["slug"] == slug:
            topic["status"] = "completed"
            topic["currentPhase"] = "completed"
            topic["completedAt"] = timestamp
            topic["lastActiveAt"] = timestamp
            topic["progress"] = 100.0
            topic_found = True
            break

    if not topic_found:
        log_error(f"Topic not found: {slug}")
        return False

    registry_data["lastUpdated"] = timestamp
    atomic_write(TOPICS_FILE, registry_data)

    log_info(f"Marked topic as completed: {slug}")

    # Archive after completion
    return archive_topic(slug)


def delete_topic(slug: str, force: bool = False) -> bool:
    """
    Delete topic (use with caution) (V2.0 - remove from topics.json)

    Args:
        slug: Topic slug
        force: If True, skip confirmation

    Returns:
        True if successful, False otherwise
    """
    topic_dir = TOPICS_DIR / slug

    if not topic_dir.exists():
        log_error(f"Topic not found: {slug}")
        return False

    if not force:
        try:
            response = input(f"Are you sure you want to delete topic '{slug}'? (yes/no): ")
            if response.lower() != "yes":
                log_info("Topic deletion cancelled")
                return False
        except EOFError:
            # Non-interactive environment - require --force flag
            log_error("Cannot confirm deletion in non-interactive environment. Use --force flag.")
            return False

    # Remove from topics.json
    registry_data = read_json_file(TOPICS_FILE)
    if registry_data is None:
        return False

    registry_data["topics"] = [
        t for t in registry_data.get("topics", [])
        if t["slug"] != slug
    ]

    registry_data["lastUpdated"] = timestamp_iso()
    atomic_write(TOPICS_FILE, registry_data)

    # Delete directory
    shutil.rmtree(topic_dir)

    log_info(f"Deleted topic: {slug}")
    return True


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Topic Manager - Topic lifecycle management (V2.0)"
    )
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # create_topic
    p = subparsers.add_parser('create_topic', help='Create new topic')
    p.add_argument('title', help='Topic title')
    p.add_argument('--description', default='', help='Topic description')
    p.add_argument('--user-request', default='', help='Original user request')

    # list_active_topics
    subparsers.add_parser('list_active_topics', help='List all active topics')

    # list_completed_topics
    subparsers.add_parser('list_completed_topics', help='List all completed topics')

    # get_topic_status
    p = subparsers.add_parser('get_topic_status', help='Get topic status')
    p.add_argument('slug', help='Topic slug')

    # touch_topic
    p = subparsers.add_parser('touch_topic', help='Update last active time')
    p.add_argument('slug', help='Topic slug')

    # update_topic_progress
    p = subparsers.add_parser('update_topic_progress', help='Update topic progress')
    p.add_argument('slug', help='Topic slug')

    # archive_topic
    p = subparsers.add_parser('archive_topic', help='Archive completed topic')
    p.add_argument('slug', help='Topic slug')

    # resume_topic
    p = subparsers.add_parser('resume_topic', help='Resume topic')
    p.add_argument('slug', help='Topic slug')

    # get_active_topics_summary
    subparsers.add_parser('get_active_topics_summary', help='Get summary for session')

    # complete_topic
    p = subparsers.add_parser('complete_topic', help='Mark as completed')
    p.add_argument('slug', help='Topic slug')

    # delete_topic
    p = subparsers.add_parser('delete_topic', help='Delete topic')
    p.add_argument('slug', help='Topic slug')
    p.add_argument('--force', action='store_true', help='Skip confirmation')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    if args.command == 'create_topic':
        slug = create_topic(
            args.title,
            args.description if hasattr(args, 'description') else '',
            args.user_request if hasattr(args, 'user_request') else ''
        )
        if slug:
            print(slug)
            return 0
        return 1

    elif args.command == 'list_active_topics':
        topics = list_active_topics()
        if topics:
            for topic in topics:
                print(f"{topic['slug']} | {topic['title']} | {topic.get('progress', 0)}% | "
                      f"{topic.get('completedTasks', 0)}/{topic.get('totalTasks', 0)} tasks")
        else:
            print("No active topics")
        return 0

    elif args.command == 'list_completed_topics':
        topics = list_completed_topics()
        if topics:
            for topic in topics:
                print(f"{topic['slug']} | {topic['title']} | "
                      f"Completed: {topic.get('completedAt', 'N/A')}")
        else:
            print("No completed topics")
        return 0

    elif args.command == 'get_topic_status':
        status = get_topic_status(args.slug)
        if status:
            import json
            print(json.dumps(status, indent=2))
            return 0
        return 1

    elif args.command == 'touch_topic':
        return 0 if touch_topic(args.slug) else 1

    elif args.command == 'update_topic_progress':
        return 0 if update_topic_progress(args.slug) else 1

    elif args.command == 'archive_topic':
        return 0 if archive_topic(args.slug) else 1

    elif args.command == 'resume_topic':
        status = resume_topic(args.slug)
        if status:
            import json
            print(json.dumps(status, indent=2))
            return 0
        return 1

    elif args.command == 'get_active_topics_summary':
        summary = get_active_topics_summary()
        if summary:
            print(summary)
        return 0  # No topics is not an error

    elif args.command == 'complete_topic':
        return 0 if complete_topic(args.slug) else 1

    elif args.command == 'delete_topic':
        return 0 if delete_topic(args.slug, args.force) else 1

    else:
        log_error(f"Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
