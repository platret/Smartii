#!/usr/bin/env python3
"""
Utility functions for project orchestration
Part of: Hierarchical Multi-Agent Orchestration System v2.0.0 (Python)
"""

import json
import re
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import tempfile
import shutil


# ANSI color codes for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def find_project_root() -> Path:
    """
    Find project root by looking for .claude directory

    Returns:
        Path to project root
    """
    current = Path.cwd()

    # Check current directory and parents
    for parent in [current] + list(current.parents):
        if (parent / ".claude").exists():
            return parent

    # Fallback: use current directory
    return current


def log_info(message: str) -> None:
    """Log info message to stderr"""
    if not os.environ.get('QUIET'):
        print(f"{Colors.GREEN}[INFO]{Colors.NC} {message}", file=sys.stderr)


def log_warn(message: str) -> None:
    """Log warning message to stderr"""
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {message}", file=sys.stderr)


def log_error(message: str) -> None:
    """Log error message to stderr"""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}", file=sys.stderr)


def slugify(text: str) -> str:
    """
    Convert text to URL-safe slug

    Args:
        text: Text to slugify (e.g., "Add JWT Authentication")

    Returns:
        Slugified text (e.g., "add-jwt-authentication")
    """
    # Convert to lowercase
    slug = text.lower()
    # Replace non-alphanumeric with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


def generate_task_id(topic_slug: Optional[str] = None) -> str:
    """
    Generate unique task ID

    Args:
        topic_slug: Optional topic slug to scope the ID

    Returns:
        Task ID like "task-001", "task-002", etc.
    """
    if not topic_slug:
        # Fallback: timestamp-based ID
        return f"task-{int(datetime.now().timestamp())}"

    state_dir = Path(".claude/agents/state")
    topic_dir = state_dir / topic_slug

    if not topic_dir.exists():
        return "task-001"

    # Count existing task files
    task_files = list(topic_dir.glob("task-*.json"))
    next_id = len(task_files) + 1

    return f"task-{next_id:03d}"


def timestamp_iso() -> str:
    """
    Get ISO 8601 timestamp with timezone

    Returns:
        ISO timestamp like "2025-10-22T10:30:00+00:00"
    """
    return datetime.now(timezone.utc).astimezone().isoformat()


def atomic_write(file_path: str | Path, content: str | dict | list) -> bool:
    """
    Atomic file write (prevents corruption)

    Args:
        file_path: Path to file
        content: String content, dict, or list (will be JSON encoded)

    Returns:
        True if successful, False otherwise
    """
    file_path = Path(file_path)

    # Convert dict or list to JSON string
    if isinstance(content, (dict, list)):
        try:
            content = json.dumps(content, indent=2)
        except (TypeError, ValueError) as e:
            log_error(f"Failed to serialize content: {e}")
            return False

    # Create temp file in same directory
    temp_fd, temp_path = tempfile.mkstemp(
        dir=file_path.parent,
        prefix=f".{file_path.name}.",
        suffix=".tmp"
    )

    try:
        # Write to temp file
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            f.write(content)

        # Validate JSON if it's a JSON file
        if file_path.suffix == '.json':
            try:
                with open(temp_path, 'r', encoding='utf-8') as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                log_error(f"Invalid JSON content for {file_path}: {e}")
                os.unlink(temp_path)
                return False

        # Atomic move (on Windows, need to remove dest first if exists)
        if os.name == 'nt' and file_path.exists():
            file_path.unlink()

        shutil.move(temp_path, file_path)
        return True

    except Exception as e:
        log_error(f"Failed to write {file_path}: {e}")
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        return False


def ensure_directory(dir_path: str | Path) -> None:
    """
    Ensure directory exists, create if needed

    Args:
        dir_path: Directory path
    """
    dir_path = Path(dir_path)
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        log_info(f"Created directory: {dir_path}")


def validate_json(file_path: str | Path) -> bool:
    """
    Validate JSON file

    Args:
        file_path: Path to JSON file

    Returns:
        True if valid, False otherwise
    """
    file_path = Path(file_path)

    if not file_path.exists():
        log_error(f"File not found: {file_path}")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)
        return True
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON in file {file_path}: {e}")
        return False
    except Exception as e:
        log_error(f"Failed to read {file_path}: {e}")
        return False


def read_json_file(file_path: str | Path) -> Optional[Dict[str, Any]]:
    """
    Read and parse JSON file

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON dict or None if failed
    """
    file_path = Path(file_path)

    if not file_path.exists():
        log_error(f"File not found: {file_path}")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        log_error(f"Failed to read {file_path}: {e}")
        return None


def read_json_field(file_path: str | Path, field_path: str) -> Any:
    """
    Read specific field from JSON file using dot notation

    Args:
        file_path: Path to JSON file
        field_path: Dot-notation path (e.g., ".status", ".user.name")

    Returns:
        Field value or None if not found
    """
    data = read_json_file(file_path)
    if data is None:
        return None

    # Remove leading dot if present
    field_path = field_path.lstrip('.')

    # Navigate nested fields
    current = data
    for key in field_path.split('.'):
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None

    return current


def update_json_field(file_path: str | Path, field_path: str, value: Any) -> bool:
    """
    Update specific field in JSON file

    Args:
        file_path: Path to JSON file
        field_path: Dot-notation path (e.g., ".status", ".user.name")
        value: New value to set

    Returns:
        True if successful, False otherwise
    """
    data = read_json_file(file_path)
    if data is None:
        return False

    # Remove leading dot if present
    field_path = field_path.lstrip('.')
    keys = field_path.split('.')

    # Navigate to parent of target field
    current = data
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    # Set the value
    current[keys[-1]] = value

    return atomic_write(file_path, data)


def append_json_array(file_path: str | Path, array_field: str, new_item: Any) -> bool:
    """
    Append item to JSON array field

    Args:
        file_path: Path to JSON file
        array_field: Dot-notation path to array (e.g., ".logs")
        new_item: Item to append

    Returns:
        True if successful, False otherwise
    """
    data = read_json_file(file_path)
    if data is None:
        return False

    # Remove leading dot if present
    array_field = array_field.lstrip('.')
    keys = array_field.split('.')

    # Navigate to parent of target field
    current = data
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    # Ensure target is an array
    field_name = keys[-1]
    if field_name not in current:
        current[field_name] = []
    elif not isinstance(current[field_name], list):
        log_error(f"Field {array_field} is not an array")
        return False

    # Append item
    current[field_name].append(new_item)

    return atomic_write(file_path, data)


def get_active_topic() -> Optional[str]:
    """
    Get most recently active topic slug

    Returns:
        Topic slug or None if no active topics
    """
    topics_file = Path(".claude/agents/state/topics.json")

    if not topics_file.exists():
        return None

    data = read_json_file(topics_file)
    if not data or 'active' not in data or not data['active']:
        return None

    # Sort by lastActiveAt and get most recent
    active_topics = sorted(
        data['active'],
        key=lambda t: t.get('lastActiveAt', ''),
        reverse=True
    )

    return active_topics[0]['slug'] if active_topics else None


if __name__ == '__main__':
    # Simple test
    print("Utils module loaded successfully")
    print(f"Test slugify: {slugify('Add JWT Authentication')}")
    print(f"Test timestamp: {timestamp_iso()}")
    print(f"Test task ID: {generate_task_id()}")
