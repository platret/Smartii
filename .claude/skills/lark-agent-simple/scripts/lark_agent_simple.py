#!/usr/bin/env python3
"""
Lark Agent Simple - Minimal Parser
Parses markdown test files and outputs compact JSON data only (no workflow instructions)

This is the token-efficient version that outputs minimal data for Claude Code to process directly.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import the markdown parser from the same directory
from markdown_parser import MarkdownParser


class LarkAgentSimple:
    """Minimal markdown parser that outputs compact JSON data"""

    def __init__(self):
        self.parser = MarkdownParser()

    def calculate_default_dates(self, start_offset_days: int = 0, duration_days: int = 14) -> Dict[str, str]:
        """Calculate default start and due dates"""
        start_date = datetime.now() + timedelta(days=start_offset_days)
        due_date = start_date + timedelta(days=duration_days)

        return {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'due_date': due_date.strftime('%Y-%m-%d')
        }

    def parse_file(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse markdown file and return minimal JSON data

        Returns:
            Compact JSON with test data and structure (no workflow instructions)
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if path.suffix.lower() not in ['.md', '.markdown']:
            raise ValueError(f"Invalid file type: {path.suffix}. Expected .md or .markdown")

        # Read markdown content
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse markdown structure
        parsed_data = self.parser.parse_file(content, options)

        # Calculate dates if not provided
        if 'start_date' not in options or 'due_date' not in options:
            dates = self.calculate_default_dates()
            if 'start_date' not in options:
                options['start_date'] = dates['start_date']
            if 'due_date' not in options:
                options['due_date'] = dates['due_date']

        # Build minimal output structure
        output = {
            'test': {
                'title': parsed_data['testOverview']['title'],
                'description': parsed_data['testOverview'].get('description', ''),
                'owner': options.get('owner', 'Test User'),
                'start_date': options.get('start_date'),
                'due_date': options.get('due_date', options.get('target_date'))
            },
            'scenarios': [],
            'metadata': {
                'total_scenarios': len(parsed_data['scenarios']),
                'total_tasks': sum(len(s.get('tasks', [])) for s in parsed_data['scenarios']),
                'source_file': str(path),
                'parsed_at': datetime.now().isoformat()
            }
        }

        # Process scenarios
        for scenario in parsed_data['scenarios']:
            scenario_data = {
                'id': scenario['scenarioId'],
                'title': scenario['title'],
                'description': scenario.get('description', ''),
                'tasks': []
            }

            # Process tasks within scenario
            for task in scenario.get('tasks', []):
                task_data = {
                    'id': task['taskId'],
                    'title': task['title'],
                    'description': task['description'],
                    'expected_result': task.get('expectedResult', '')
                }
                scenario_data['tasks'].append(task_data)

            output['scenarios'].append(scenario_data)

        return output

    def execute(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Execute the parser and return compact JSON"""
        try:
            options = {
                'owner': args.owner,
                'start_date': args.start_date,
                'due_date': args.due_date or args.target_date
            }

            # Remove None values
            options = {k: v for k, v in options.items() if v is not None}

            # Parse file
            result = self.parse_file(args.input_file, options)

            return {
                'success': True,
                'data': result
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Lark Agent Simple - Parse markdown test files to compact JSON',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python lark_agent_simple.py test.md
  python lark_agent_simple.py test.md --owner="QA Team" --due-date="2025-12-31"
        """
    )

    parser.add_argument('input_file', help='Input markdown test file')
    parser.add_argument('--owner', default='Test User', help='Task owner (default: Test User)')
    parser.add_argument('--start-date', help='Start date YYYY-MM-DD (default: today)')
    parser.add_argument('--due-date', help='Due date YYYY-MM-DD (default: 14 days from now)')
    parser.add_argument('--target-date', help='Alias for --due-date')
    parser.add_argument('--compact', action='store_true', help='Output compact JSON (one line)')

    args = parser.parse_args()

    # Execute parser
    agent = LarkAgentSimple()
    result = agent.execute(args)

    # Output JSON
    if args.compact:
        print(json.dumps(result, separators=(',', ':')))
    else:
        print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
