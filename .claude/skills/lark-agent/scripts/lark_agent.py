#!/usr/bin/env python3
"""
Lark Agent - Main Entry Point
Orchestrates the complete end-to-end workflow: Markdown -> JSON -> Lark Tasks -> Verification

This script processes markdown test files, creates hierarchical Lark tasks,
and verifies the creation. It's designed to be called by Claude Code with
proper tool integration for Lark MCP.
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Import our modules
from markdown_parser import MarkdownParser
from lark_batch_executor import LarkBatchExecutor

class LarkAgent:
    """Main orchestrator for the Lark Agent workflow"""
    
    def __init__(self):
        self.default_options = {
            'owner': 'Test User',
            'target_date': self._calculate_default_target_date(),
            'start_date': self._calculate_default_start_date(),
            'priority': 'medium',
            'timezone': 'UTC'
        }
    
    def _calculate_default_target_date(self) -> str:
        """Calculate default target date (14 days from now)"""
        target = datetime.now() + timedelta(days=14)
        return target.strftime('%Y-%m-%d')
    
    def _calculate_default_start_date(self) -> str:
        """Calculate default start date (today)"""
        return datetime.now().strftime('%Y-%m-%d')
    
    def validate_input_file(self, file_path: str) -> Path:
        """Validate that the input file exists and is a markdown file"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if path.suffix.lower() not in ['.md', '.markdown']:
            raise ValueError(f"Invalid file type: {path.suffix}. Expected .md or .markdown")
        
        return path
    
    def generate_output_path(self, input_path: Path) -> Path:
        """Generate output JSON file path from input markdown path"""
        return input_path.with_suffix('.json')
    
    def parse_markdown(self, file_path: Path, options: Dict[str, Any]) -> Path:
        """
        Step 1: Parse markdown file and generate JSON structure
        """
        print(f"\n{'='*70}")
        print(f"🔍 LARK AGENT - STEP 1: PARSING MARKDOWN FILE")
        print(f"{'='*70}")
        print(f"📄 Input file: {file_path}")
        print(f"🔄 Processing markdown structure...")

        # Read markdown content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Use the MarkdownParser module
        parser = MarkdownParser()
        json_data = parser.parse_file(content, options)

        # Add metadata from options
        json_data['testOverview']['owner'] = options.get('owner', self.default_options['owner'])
        json_data['testOverview']['targetDate'] = options.get('target_date', self.default_options['target_date'])
        json_data['testOverview']['startDate'] = options.get('start_date', self.default_options['start_date'])
        json_data['testOverview']['priority'] = options.get('priority', self.default_options['priority'])

        # Generate output path
        output_path = self.generate_output_path(file_path)

        # Save JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ PARSING COMPLETE!")
        print(f"   📋 Test Title: {json_data['testOverview']['title']}")
        print(f"   🎯 Scenarios: {len(json_data['scenarios'])}")
        total_tasks = sum(len(s.get('tasks', [])) for s in json_data['scenarios'])
        print(f"   📝 Total Tasks: {total_tasks}")
        print(f"   💾 JSON Output: {output_path}")

        return output_path

    def create_lark_tasks_batch(self, json_path: Path, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 2: Generate batch execution plan for Lark tasks

        Returns a compact batch plan for Claude Code to execute ALL tasks at once
        """
        print(f"\n{'='*70}")
        print(f"🏗️  LARK AGENT - STEP 2: GENERATING BATCH EXECUTION PLAN")
        print(f"{'='*70}")
        print(f"📂 JSON Input: {json_path}")
        print(f"🔄 Generating compact batch plan...")

        # Use the LarkBatchExecutor module
        executor = LarkBatchExecutor()
        result = executor.execute(json_path, options)

        print(f"\n✅ BATCH PLAN GENERATED!")
        print(f"   📊 MCP Calls: {len(result['plan']['mcp_calls'])}")
        print(f"   🎯 Execution Mode: BATCH (all at once)")
        print(f"   💡 Token Efficient: YES")

        return result['plan']

    def display_summary(self, json_path: Path, batch_plan: Dict[str, Any]):
        """Display execution summary"""
        print(f"\n{'='*70}")
        print("📊 LARK AGENT - EXECUTION SUMMARY")
        print(f"{'='*70}")

        summary = batch_plan.get('summary', {})

        print(f"\n📋 Test Overview:")
        print(f"   Title: {summary.get('test_title', 'N/A')}")
        print(f"   Owner: {summary.get('owner', 'N/A')}")
        print(f"   Target Date: {summary.get('target_date', 'N/A')}")

        print(f"\n🎯 Scenarios: {summary.get('scenarios_count', 0)}")
        print(f"   Total Tasks: {summary.get('tasks_count', 0)}")

        print(f"\n📁 Files:")
        print(f"   JSON: {json_path}")

        print(f"\n🔄 Execution Mode:")
        print(f"   ✅ BATCH (all tasks created at once)")
        print(f"   ✅ Token efficient")
        print(f"   ✅ Fast execution")

        print(f"\n{'='*60}")
        print("✅ Lark Agent batch plan ready for execution!")
        print(f"{'='*60}\n")
    
    def execute(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        Execute the complete end-to-end workflow:
        1. Parse Markdown → Generate JSON
        2. Generate Batch Execution Plan
        3. Return compact plan for Claude Code to execute
        """
        print(f"\n{'='*70}")
        print("🚀 LARK AGENT SKILL - BATCH EXECUTION MODE")
        print(f"{'='*70}\n")

        try:
            # Merge options
            options = {**self.default_options}
            if args.owner:
                options['owner'] = args.owner
            if args.target_date:
                options['target_date'] = args.target_date
            if args.start_date:
                options['start_date'] = args.start_date
            if args.priority:
                options['priority'] = args.priority
            if args.timezone:
                options['timezone'] = args.timezone

            print("📋 Configuration:")
            print(f"   📄 Input File: {args.input_file}")
            print(f"   👤 Owner: {options['owner']}")
            print(f"   📅 Target Date: {options['target_date']}")
            print(f"   📅 Start Date: {options['start_date']}")
            print(f"   ⚡ Priority: {options['priority']}")
            print(f"   🌍 Timezone: {options['timezone']}")

            # Validate input file
            input_path = self.validate_input_file(args.input_file)

            # STEP 1: Parse markdown and generate JSON
            json_path = self.parse_markdown(input_path, options)

            # STEP 2: Generate batch execution plan
            batch_plan = self.create_lark_tasks_batch(json_path, options)

            # Display summary
            self.display_summary(json_path, batch_plan)

            # Return compact batch plan for Claude Code to execute
            return {
                'success': True,
                'execution_mode': 'batch',
                'execute_immediately': True,
                'input_file': str(input_path),
                'json_file': str(json_path),
                'batch_plan': batch_plan,
                'options': options,
                'instructions_for_claude_code': [
                    'Execute ALL mcp_calls in batch_plan.mcp_calls',
                    'Replace template variables ({{tasklist_guid}}, etc.) with actual values',
                    'Update JSON file with task IDs after execution',
                    'Show final summary only'
                ]
            }

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Lark Agent - Convert markdown test files to Lark tasks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python lark_agent.py test.md
  python lark_agent.py test.md --owner="QA Team" --target-date="2025-12-31"
  python lark_agent.py test.md --priority=high --timezone="America/New_York"
        """
    )
    
    parser.add_argument('input_file', help='Input markdown test file')
    parser.add_argument('--owner', help='Assign owner to tasks (default: "Test User")')
    parser.add_argument('--target-date', help='Target completion date YYYY-MM-DD (default: 14 days from now)')
    parser.add_argument('--start-date', help='Start date YYYY-MM-DD (default: today)')
    parser.add_argument('--priority', choices=['low', 'medium', 'high'], help='Task priority (default: medium)')
    parser.add_argument('--timezone', help='Timezone for date calculations (default: UTC)')
    
    args = parser.parse_args()
    
    agent = LarkAgent()
    result = agent.execute(args)
    
    # Output result as JSON for Claude Code to process
    print("\n" + "="*60)
    print("📤 Workflow Request for Claude Code:")
    print("="*60)
    print(json.dumps(result, indent=2))
    
    sys.exit(0 if result['success'] else 1)

if __name__ == '__main__':
    main()

