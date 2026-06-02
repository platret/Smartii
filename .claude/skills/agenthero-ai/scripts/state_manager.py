#!/usr/bin/env python3
"""
State Manager - CRUD operations for orchestration state files
Part of: Hierarchical Multi-Agent Orchestration System v2.0.0 (Python)
"""

import sys
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import utilities
from utils import (
    log_info, log_warn, log_error,
    timestamp_iso, atomic_write, ensure_directory,
    read_json_file, read_json_field, update_json_field, append_json_array,
    validate_json, find_project_root
)


# Find project root and set absolute paths
PROJECT_ROOT = find_project_root()
SCRIPT_DIR = Path(__file__).parent
TEMPLATES_DIR = SCRIPT_DIR.parent / "templates"
STATE_DIR = PROJECT_ROOT / ".claude/agents/state"


def get_template(template_name: str) -> Optional[Dict[str, Any]]:
    """
    Get state template by name

    Args:
        template_name: Name of template (e.g., "task-state", "topic", "pm-state")

    Returns:
        Template dict or None if not found
    """
    templates_file = TEMPLATES_DIR / "state-templates.json"

    if not templates_file.exists():
        log_error(f"Templates file not found: {templates_file}")
        return None

    data = read_json_file(templates_file)
    if not data or 'templates' not in data:
        log_error("Invalid templates file structure")
        return None

    if template_name not in data['templates']:
        log_error(f"Template not found: {template_name}")
        return None

    return data['templates'][template_name]


def create_state_file(file_path: str, template_name: str) -> bool:
    """
    Create state file from template

    Args:
        file_path: Path to create state file
        template_name: Name of template to use

    Returns:
        True if successful, False otherwise
    """
    file_path = Path(file_path)

    # Ensure parent directory exists
    ensure_directory(file_path.parent)

    # Get template
    template = get_template(template_name)
    if template is None:
        return False

    # Check if file already exists
    if file_path.exists():
        log_warn(f"State file already exists: {file_path}")
        return True

    # Write template to file
    if atomic_write(file_path, template):
        log_info(f"Created state file: {file_path}")
        return True
    return False


def read_state(file_path: str, field: str) -> Any:
    """
    Read state field

    Args:
        file_path: Path to state file
        field: Field path (e.g., ".status", ".user.name")

    Returns:
        Field value or None
    """
    return read_json_field(file_path, field)


def update_state(file_path: str, field: str, value: Any) -> bool:
    """
    Update state field

    Args:
        file_path: Path to state file
        field: Field path (e.g., ".status")
        value: New value

    Returns:
        True if successful, False otherwise
    """
    return update_json_field(file_path, field, value)


def append_log(file_path: str, level: str, message: str) -> bool:
    """
    Append log entry to task state

    Args:
        file_path: Path to state file
        level: Log level (info, warn, error)
        message: Log message

    Returns:
        True if successful, False otherwise
    """
    file_path = Path(file_path)

    if not file_path.exists():
        log_error(f"State file not found: {file_path}")
        return False

    # Create log entry
    log_entry = {
        "timestamp": timestamp_iso(),
        "level": level,
        "message": message
    }

    # Append to logs array
    if not append_json_array(file_path, ".logs", log_entry):
        return False

    # Update current operation
    if not update_json_field(file_path, ".currentOperation", message):
        log_warn("Failed to update currentOperation")

    log_info(f"Appended log: [{level}] {message}")
    return True


def set_task_status(file_path: str, status: str) -> bool:
    """
    Set task status and update timestamps

    Args:
        file_path: Path to state file
        status: New status (pending, in_progress, completed, failed, blocked)

    Returns:
        True if successful, False otherwise
    """
    file_path = Path(file_path)

    # Update status
    if not update_json_field(file_path, ".status", status):
        return False

    # Update timestamps based on status
    if status == "in_progress":
        # Set startedAt if not already set
        started_at = read_json_field(file_path, ".startedAt")
        if started_at is None or started_at == "null":
            update_json_field(file_path, ".startedAt", timestamp_iso())

    elif status in ["completed", "failed"]:
        update_json_field(file_path, ".completedAt", timestamp_iso())

    log_info(f"Updated task status: {status}")
    return True


def track_file_change(state_path: str, file_path: str, change_type: str) -> bool:
    """
    Track file creation or modification

    Args:
        state_path: Path to state file
        file_path: Path to created/modified file
        change_type: "created" or "modified"

    Returns:
        True if successful, False otherwise
    """
    if change_type not in ["created", "modified"]:
        log_error(f"Invalid change type: {change_type}")
        return False

    field = ".filesCreated" if change_type == "created" else ".filesModified"

    file_info = {
        "path": file_path,
        "timestamp": timestamp_iso()
    }

    if append_json_array(state_path, field, file_info):
        log_info(f"Tracked file change: {change_type} - {file_path}")
        return True
    return False


def set_blocking_question(file_path: str, question: str, context: str = "") -> bool:
    """
    Set blocking question in state

    Args:
        file_path: Path to state file
        question: Question text
        context: Optional context for the question

    Returns:
        True if successful, False otherwise
    """
    file_path = Path(file_path)

    question_obj = {
        "question": question,
        "context": context,
        "timestamp": timestamp_iso(),
        "answered": False,
        "answer": None
    }

    data = read_json_file(file_path)
    if data is None:
        return False

    data["blockingQuestion"] = question_obj
    data["status"] = "blocked"

    if atomic_write(file_path, data):
        log_info("Set blocking question")
        return True
    return False


def answer_question(file_path: str, answer: str) -> bool:
    """
    Answer blocking question

    Args:
        file_path: Path to state file
        answer: Answer text

    Returns:
        True if successful, False otherwise
    """
    file_path = Path(file_path)

    data = read_json_file(file_path)
    if data is None:
        return False

    if "blockingQuestion" not in data or data["blockingQuestion"] is None:
        log_error("No blocking question to answer")
        return False

    data["blockingQuestion"]["answered"] = True
    data["blockingQuestion"]["answer"] = answer
    data["status"] = "in_progress"

    if atomic_write(file_path, data):
        log_info("Answered blocking question")
        return True
    return False


def update_progress(file_path: str, progress: int) -> bool:
    """
    Update task progress percentage

    Args:
        file_path: Path to state file
        progress: Progress percentage (0-100)

    Returns:
        True if successful, False otherwise
    """
    if not isinstance(progress, int) or progress < 0 or progress > 100:
        log_error(f"Invalid progress value: {progress} (must be 0-100)")
        return False

    if update_json_field(file_path, ".progress", progress):
        log_info(f"Updated progress: {progress}%")
        return True
    return False


def set_task_result(file_path: str, summary: str, files_created: List[str] = None,
                     files_modified: List[str] = None) -> bool:
    """
    Set task result and mark as completed

    Args:
        file_path: Path to state file
        summary: Result summary
        files_created: List of created file paths
        files_modified: List of modified file paths

    Returns:
        True if successful, False otherwise
    """
    file_path = Path(file_path)

    files_created = files_created or []
    files_modified = files_modified or []

    result_obj = {
        "summary": summary,
        "filesCreated": files_created,
        "filesModified": files_modified
    }

    data = read_json_file(file_path)
    if data is None:
        return False

    data["result"] = result_obj
    data["status"] = "completed"
    data["completedAt"] = timestamp_iso()
    data["progress"] = 100

    if atomic_write(file_path, data):
        log_info("Set task result")
        return True
    return False


def validate_state(file_path: str) -> bool:
    """
    Validate state file structure

    Args:
        file_path: Path to state file

    Returns:
        True if valid, False otherwise
    """
    return validate_json(file_path)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="State Manager - CRUD operations for orchestration state files"
    )
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # create_state_file
    p = subparsers.add_parser('create_state_file', help='Create new state file')
    p.add_argument('path', help='State file path')
    p.add_argument('template', help='Template name')

    # read_state
    p = subparsers.add_parser('read_state', help='Read state field')
    p.add_argument('path', help='State file path')
    p.add_argument('field', help='Field path (e.g., .status)')

    # update_state
    p = subparsers.add_parser('update_state', help='Update state field')
    p.add_argument('path', help='State file path')
    p.add_argument('field', help='Field path')
    p.add_argument('value', help='New value')

    # append_log
    p = subparsers.add_parser('append_log', help='Append log entry')
    p.add_argument('path', help='State file path')
    p.add_argument('level', help='Log level (info, warn, error)')
    p.add_argument('message', help='Log message')

    # set_task_status
    p = subparsers.add_parser('set_task_status', help='Update task status')
    p.add_argument('path', help='State file path')
    p.add_argument('status', help='New status')

    # track_file_change
    p = subparsers.add_parser('track_file_change', help='Track file change')
    p.add_argument('path', help='State file path')
    p.add_argument('file', help='File path')
    p.add_argument('type', help='Change type (created/modified)')

    # update_progress
    p = subparsers.add_parser('update_progress', help='Update progress')
    p.add_argument('path', help='State file path')
    p.add_argument('percentage', type=int, help='Progress percentage (0-100)')

    # validate_state
    p = subparsers.add_parser('validate_state', help='Validate state file')
    p.add_argument('path', help='State file path')

    # set_blocking_question
    p = subparsers.add_parser('set_blocking_question', help='Set blocking question')
    p.add_argument('path', help='State file path')
    p.add_argument('question', help='Question text')
    p.add_argument('--context', default='', help='Question context (optional)')

    # answer_question
    p = subparsers.add_parser('answer_question', help='Answer blocking question')
    p.add_argument('path', help='State file path')
    p.add_argument('answer', help='Answer text')

    # set_task_result
    p = subparsers.add_parser('set_task_result', help='Set task completion result')
    p.add_argument('path', help='State file path')
    p.add_argument('summary', help='Result summary')
    p.add_argument('--files-created', default='[]', help='JSON array of created files')
    p.add_argument('--files-modified', default='[]', help='JSON array of modified files')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    if args.command == 'create_state_file':
        return 0 if create_state_file(args.path, args.template) else 1
    elif args.command == 'read_state':
        value = read_state(args.path, args.field)
        if value is not None:
            print(value)
            return 0
        return 1
    elif args.command == 'update_state':
        return 0 if update_state(args.path, args.field, args.value) else 1
    elif args.command == 'append_log':
        return 0 if append_log(args.path, args.level, args.message) else 1
    elif args.command == 'set_task_status':
        return 0 if set_task_status(args.path, args.status) else 1
    elif args.command == 'track_file_change':
        return 0 if track_file_change(args.path, args.file, args.type) else 1
    elif args.command == 'update_progress':
        return 0 if update_progress(args.path, args.percentage) else 1
    elif args.command == 'validate_state':
        return 0 if validate_state(args.path) else 1
    elif args.command == 'set_blocking_question':
        return 0 if set_blocking_question(args.path, args.question, args.context) else 1
    elif args.command == 'answer_question':
        return 0 if answer_question(args.path, args.answer) else 1
    elif args.command == 'set_task_result':
        import json
        files_created = json.loads(args.files_created) if args.files_created else []
        files_modified = json.loads(args.files_modified) if args.files_modified else []
        return 0 if set_task_result(args.path, args.summary, files_created, files_modified) else 1
    else:
        log_error(f"Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
