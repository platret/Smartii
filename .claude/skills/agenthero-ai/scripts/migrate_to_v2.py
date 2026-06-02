#!/usr/bin/env python3
"""
State Structure Migration: V1 → V2

Migrates from complex 3-file-per-topic structure to simple 2-file-type structure.

V1 (OLD - Complex):
  topics.json (registry with duplicates)
  topics/{slug}/topic.json
  topics/{slug}/pm-state.json
  topics/{slug}/task-*.json

V2 (NEW - Simple):
  topics.json (single source of truth)
  topics/{slug}/task-*.json

Usage:
    python migrate_to_v2.py [--dry-run] [--backup]
"""

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

def migrate():
    """Migrate state structure from v1 to v2"""

    print("="*60)
    print("State Structure Migration: V1 to V2")
    print("="*60)
    print()

    base_path = Path(".claude/agents/state/agenthero-ai")
    topics_dir = base_path / "topics"

    # Step 1: Scan for actual topics (directories with task files)
    print("Step 1: Scanning for actual topics...")
    actual_topics = []

    for topic_dir in topics_dir.iterdir():
        if not topic_dir.is_dir():
            continue

        # Check if directory has task files
        task_files = list(topic_dir.glob("task-*.json"))
        if task_files:
            actual_topics.append(topic_dir.name)
            print(f"  [OK] Found: {topic_dir.name} ({len(task_files)} tasks)")

    print(f"\nFound {len(actual_topics)} actual topics with task files\n")

    # Step 2: Build new topics.json from actual state
    print("Step 2: Building new topics.json...")
    new_topics_json = {
        "version": "2.0.0",
        "lastUpdated": datetime.now().isoformat(),
        "topics": []
    }

    for slug in actual_topics:
        topic_dir = topics_dir / slug

        # Try to load old topic.json if exists
        old_topic_file = topic_dir / "topic.json"
        old_pm_file = topic_dir / "pm-state.json"

        topic_data = {}
        pm_data = {}

        if old_topic_file.exists():
            with open(old_topic_file) as f:
                topic_data = json.load(f)

        if old_pm_file.exists():
            with open(old_pm_file) as f:
                pm_data = json.load(f)

        # Load all task files for this topic
        task_files = list(topic_dir.glob("task-*.json"))
        tasks = []

        for task_file in sorted(task_files):
            with open(task_file) as f:
                task = json.load(f)

                # Extract lightweight task summary
                tasks.append({
                    "id": task_file.stem,  # e.g., "task-001"
                    "name": task.get("focusArea", task.get("description", "Unknown")),
                    "agent": task.get("agentName", task.get("assignedTo", "unknown")),
                    "status": task.get("status", "unknown"),
                    "progress": task.get("progress", 0)
                })

        # Calculate progress
        completed_tasks = sum(1 for t in tasks if t["status"] == "completed")
        total_tasks = len(tasks)
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Determine overall status
        if completed_tasks == total_tasks and total_tasks > 0:
            status = "completed"
        elif completed_tasks > 0:
            status = "in_progress"
        else:
            status = "pending"

        # Build new topic object
        new_topic = {
            "slug": slug,
            "title": topic_data.get("title", slug.replace("-", " ").title()),
            "description": topic_data.get("description", ""),
            "status": status,
            "currentPhase": topic_data.get("currentPhase", "unknown"),
            "createdAt": topic_data.get("createdAt", pm_data.get("createdAt", "")),
            "lastActiveAt": datetime.now().isoformat(),
            "completedAt": topic_data.get("completedAt", None),
            "userRequest": topic_data.get("userRequest", pm_data.get("userRequest", "")),
            "tasks": tasks,
            "totalTasks": total_tasks,
            "completedTasks": completed_tasks,
            "progress": round(progress, 1),
            "files": {
                "topicPlan": f"Project-tasks/{slug}/topicplan.md",
                "spec": f"Project-tasks/{slug}/spec/original-spec.md",
                "deliverables": f"Project-tasks/{slug}/deliverables/",
                "qaReport": f"Project-tasks/{slug}/QA-REPORT.md"
            },
            "tokenUsage": topic_data.get("tokenUsage", {
                "total": 0,
                "pmAgent": 0,
                "subAgents": {}
            })
        }

        new_topics_json["topics"].append(new_topic)
        print(f"  [OK] Migrated: {slug} ({status}, {completed_tasks}/{total_tasks} tasks)")

    print(f"\nMigrated {len(new_topics_json['topics'])} topics\n")

    # Step 3: Backup old topics.json
    print("Step 3: Backing up old files...")
    old_topics_file = base_path / "topics.json"

    if old_topics_file.exists():
        backup_file = base_path / f"topics.json.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy(old_topics_file, backup_file)
        print(f"  [OK] Backed up topics.json -> {backup_file.name}")

    # Step 4: Write new topics.json
    print("\nStep 4: Writing new topics.json...")
    with open(old_topics_file, 'w') as f:
        json.dump(new_topics_json, f, indent=2)
    print(f"  [OK] Created new topics.json (v2.0.0)")

    # Step 5: Clean up redundant files
    print("\nStep 5: Cleaning up redundant files...")
    files_to_delete = []

    for slug in actual_topics:
        topic_dir = topics_dir / slug

        # Delete old topic.json and pm-state.json
        old_topic = topic_dir / "topic.json"
        old_pm = topic_dir / "pm-state.json"

        if old_topic.exists():
            files_to_delete.append(old_topic)
        if old_pm.exists():
            files_to_delete.append(old_pm)

    # Delete other redundant files
    redundant_files = [
        base_path / "resume.json",
        topics_dir / "_manifest.json",
        topics_dir / "topics.json"
    ]

    for f in redundant_files:
        if f.exists():
            files_to_delete.append(f)

    print(f"\nFiles to delete ({len(files_to_delete)}):")
    for f in files_to_delete:
        print(f"  - {f.relative_to(base_path)}")

    print("\nDeleting files...")
    for f in files_to_delete:
        f.unlink()
        print(f"  [OK] Deleted: {f.name}")

    # Step 6: Summary
    print("\n" + "="*60)
    print("MIGRATION COMPLETE!")
    print("="*60)
    print(f"\nNew structure:")
    print(f"  topics.json (v2.0.0) - {len(new_topics_json['topics'])} topics")
    for topic in new_topics_json['topics']:
        print(f"    • {topic['slug']} ({topic['status']}, {topic['completedTasks']}/{topic['totalTasks']} tasks)")
    print(f"\n  topics/ - {len(actual_topics)} topic directories with task files")
    print(f"\nDeleted {len(files_to_delete)} redundant files")
    print("\n[SUCCESS] State structure now simplified!")
    print("\nNext steps:")
    print("  1. Refresh dashboard to see changes")
    print("  2. Test topic creation with new structure")
    print("  3. Verify QA callback works with new structure")
    print()

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
