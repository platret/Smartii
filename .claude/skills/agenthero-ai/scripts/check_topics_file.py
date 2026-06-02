#!/usr/bin/env python3
"""
Check Topics File - Verify topics.json exists and optionally display content
Part of: Hierarchical Multi-Agent Orchestration System v2.0.0 (Python)

Cross-platform replacement for:
  if exist "topics.json" (type "topics.json") else (echo "No topics.json found")
"""

import sys
import argparse
from pathlib import Path

# Import utilities
from utils import read_json_file, log_info, log_warn, log_error


STATE_DIR = Path(".claude/agents/state/agenthero-ai")
TOPICS_FILE = STATE_DIR / "topics.json"


def check_topics_file(show_content: bool = False, summary: bool = False) -> int:
    """
    Check if topics.json exists and optionally display content

    Args:
        show_content: If True, display entire file content (JSON)
        summary: If True, display summary stats only

    Returns:
        0 if file exists, 1 if not found
    """
    if not TOPICS_FILE.exists():
        log_warn(f"No topics.json found - will be created when first topic is added")
        log_info(f"Expected location: {TOPICS_FILE}")
        return 1

    # File exists
    log_info(f"✓ topics.json found: {TOPICS_FILE}")

    if show_content:
        # Display full content
        data = read_json_file(TOPICS_FILE)
        if data:
            import json
            print(json.dumps(data, indent=2))
        return 0

    if summary:
        # Display summary
        data = read_json_file(TOPICS_FILE)
        if data and 'topics' in data:
            topics = data['topics']
            total = len(topics)

            # Count by status
            statuses = {}
            for topic in topics:
                status = topic.get('status', 'unknown')
                statuses[status] = statuses.get(status, 0) + 1

            print(f"\nTopics Summary:")
            print(f"  Total topics: {total}")
            if statuses:
                print(f"  By status:")
                for status, count in sorted(statuses.items()):
                    print(f"    - {status}: {count}")
            print()
        return 0

    # Just confirm it exists
    return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Check if topics.json exists and optionally display content'
    )
    parser.add_argument(
        '--show', '-s',
        action='store_true',
        help='Display full file content as JSON'
    )
    parser.add_argument(
        '--summary', '-u',
        action='store_true',
        help='Display summary statistics'
    )

    args = parser.parse_args()

    # Run check
    exit_code = check_topics_file(
        show_content=args.show,
        summary=args.summary
    )

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
