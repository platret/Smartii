#!/usr/bin/env python3
"""
Finalize Topic - Update state after all tasks complete (V2.0)

Usage:
    python finalize_topic.py <topic-slug>

This script should be called after all sub-agents complete to:
1. Check all task states
2. Update topics.json (single source of truth)
3. Mark topic as completed if all tasks done
"""

import sys
import json
import os
from datetime import datetime
from pathlib import Path

def finalize_topic(topic_slug):
    """Finalize topic state after all tasks complete (V2.0 structure)"""

    base_path = Path(".claude/agents/state/agenthero-ai/topics") / topic_slug

    if not base_path.exists():
        print(f"[ERROR] Topic '{topic_slug}' not found")
        return False

    # 1. Check all task states
    task_files = list(base_path.glob("task-*.json"))
    total_tasks = len(task_files)
    completed_tasks = 0
    task_summaries = []

    print(f"Found {total_tasks} tasks for topic '{topic_slug}'")

    for task_file in sorted(task_files):
        with open(task_file, 'r') as f:
            task_data = json.load(f)

        status = task_data.get('status', 'unknown')
        task_id = task_file.stem
        agent_name = task_data.get('agentName', task_data.get('assignedTo', 'unknown'))
        focus_area = task_data.get('focusArea', task_data.get('description', 'Unknown'))
        progress = task_data.get('progress', 0)

        print(f"  - {task_id}: {status} ({progress}%)")

        if status == 'completed':
            completed_tasks += 1

        # Build lightweight task summary for topics.json
        task_summaries.append({
            "id": task_id,
            "name": focus_area,
            "agent": agent_name,
            "status": status,
            "progress": progress
        })

    all_completed = (completed_tasks == total_tasks and total_tasks > 0)
    progress_percent = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0

    # 2. Update topics.json (single source of truth in V2.0)
    topics_file = Path(".claude/agents/state/agenthero-ai/topics.json")

    if not topics_file.exists():
        print(f"[ERROR] topics.json not found at {topics_file}")
        return False

    with open(topics_file, 'r') as f:
        topics_data = json.load(f)

    # Find the topic in the topics array
    topic_found = False
    for topic in topics_data.get('topics', []):
        if topic['slug'] == topic_slug:
            topic_found = True

            # Update topic metadata
            topic['status'] = 'completed' if all_completed else 'in_progress'
            topic['currentPhase'] = 'completed' if all_completed else topic.get('currentPhase', 'ready-for-execution')
            topic['totalTasks'] = total_tasks
            topic['completedTasks'] = completed_tasks
            topic['progress'] = progress_percent
            topic['lastActiveAt'] = datetime.now().isoformat()

            # Update completedAt timestamp if completed
            if all_completed and not topic.get('completedAt'):
                topic['completedAt'] = datetime.now().isoformat()

            # Update task summaries (lightweight task info)
            topic['tasks'] = task_summaries

            print(f"[OK] Updated topic in topics.json: status={'completed' if all_completed else 'in_progress'}")
            break

    if not topic_found:
        print(f"[ERROR] Topic '{topic_slug}' not found in topics.json registry")
        return False

    # Update lastUpdated timestamp
    topics_data['lastUpdated'] = datetime.now().isoformat()

    # Write updated topics.json
    with open(topics_file, 'w') as f:
        json.dump(topics_data, f, indent=2)

    print(f"[OK] Saved topics.json with updated state")

    # 3. Summary
    print(f"\n{'='*50}")
    print(f"Topic '{topic_slug}' finalized successfully!")
    print(f"Status: {'COMPLETED' if all_completed else 'IN PROGRESS'}")
    print(f"Tasks: {completed_tasks}/{total_tasks} ({progress_percent}%)")
    print(f"{'='*50}")

    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python finalize_topic.py <topic-slug>")
        sys.exit(1)

    topic_slug = sys.argv[1]
    success = finalize_topic(topic_slug)
    sys.exit(0 if success else 1)
