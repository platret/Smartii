#!/usr/bin/env python3
"""
Lark Agent CLI - Main Entry Point
Handles both interactive and direct modes

Usage:
  python lark_agent_cli.py --interactive          # Interactive mode
  python lark_agent_cli.py                        # Interactive mode (default)
  python lark_agent_cli.py test.md [options]      # Direct mode
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lark_agent_interactive import InteractiveLarkAgent
from lark_agent import LarkAgent

def main():
    """Main CLI entry point"""
    
    # Check if running in interactive mode
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ['--interactive', '-i']):
        # Interactive mode
        agent = InteractiveLarkAgent()
        result = agent.execute()
        
        # If topic mode, we need Claude Code to generate the test plan
        if result.get('mode') == 'topic':
            print("\n" + "="*70)
            print("🤖 REQUESTING CLAUDE CODE TO GENERATE TEST PLAN")
            print("="*70)
            print("\nClaude Code will now:")
            print("  1. Generate comprehensive test plan from topic")
            print("  2. Save as markdown file")
            print("  3. Process the markdown file")
            print("  4. Create Lark tasks")
            print("  5. Verify and report\n")
            
            # Return the request for Claude Code
            print(json.dumps(result, indent=2))
            return result
        
        # If file mode, process the file with collected configuration
        else:
            print("\n" + "="*70)
            print("🚀 PROCESSING MARKDOWN FILE")
            print("="*70)
            
            # Create args namespace from config
            args = argparse.Namespace(
                input_file=result['file_path'],
                owner=result['config']['owner'],
                target_date=result['config']['target_date'],
                start_date=None,
                priority=result['config']['priority'],
                timezone='UTC',
                task_list_id=result['config'].get('task_list_id')
            )
            
            # Execute the standard workflow
            agent = LarkAgent()
            workflow_result = agent.execute(args)
            
            # Merge results
            workflow_result['interactive_config'] = result['config']
            
            print("\n" + "="*70)
            print("📤 WORKFLOW COMPLETE")
            print("="*70)
            print(json.dumps(workflow_result, indent=2))
            
            return workflow_result
    
    else:
        # Direct mode - parse arguments
        parser = argparse.ArgumentParser(
            description='Lark Agent - Convert markdown test files to Lark tasks',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Interactive mode
  python lark_agent_cli.py --interactive
  
  # Direct mode
  python lark_agent_cli.py tests/manual/test.md --owner="QA Team"
  python lark_agent_cli.py tests/manual/test.md --target-date="2025-12-31" --priority=high
            """
        )
        
        parser.add_argument(
            'input_file',
            nargs='?',
            help='Path to markdown test file'
        )
        
        parser.add_argument(
            '--interactive', '-i',
            action='store_true',
            help='Run in interactive mode'
        )
        
        parser.add_argument(
            '--owner',
            type=str,
            help='Assign owner to tasks (default: Test User)'
        )
        
        parser.add_argument(
            '--target-date',
            type=str,
            help='Target completion date YYYY-MM-DD (default: 14 days from now)'
        )
        
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date YYYY-MM-DD (default: today)'
        )
        
        parser.add_argument(
            '--priority',
            type=str,
            choices=['low', 'medium', 'high'],
            help='Task priority (default: medium)'
        )
        
        parser.add_argument(
            '--timezone',
            type=str,
            help='Timezone for date calculations (default: UTC)'
        )
        
        parser.add_argument(
            '--task-list-id',
            type=str,
            help='Existing Lark task list ID to use'
        )
        
        args = parser.parse_args()
        
        # Validate input file
        if not args.input_file:
            print("❌ Error: No input file specified")
            print("\nUse --interactive for interactive mode, or provide a markdown file path")
            print("Example: python lark_agent_cli.py tests/manual/test.md")
            sys.exit(1)
        
        # Execute direct mode
        agent = LarkAgent()
        result = agent.execute(args)
        
        print("\n" + "="*70)
        print("📤 WORKFLOW COMPLETE")
        print("="*70)
        print(json.dumps(result, indent=2))
        
        return result

if __name__ == '__main__':
    try:
        result = main()
        sys.exit(0 if result.get('success') else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

