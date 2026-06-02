#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lark Agent - Main Entry Point for Claude Code
This script is invoked by Claude Code when /lark-agent command is used
"""

import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add scripts directory to path
SCRIPT_DIR = Path(__file__).parent / 'scripts'
sys.path.insert(0, str(SCRIPT_DIR))

def print_banner():
    """Print the Lark Agent skill activation banner"""
    print("\n")
    print("=" * 70)
    print("=" * 70)
    print("||                                                              ||")
    print("||          🚀 LARK AGENT SKILL ACTIVATED 🚀                   ||")
    print("||                                                              ||")
    print("||      Interactive Test Planning & Lark Task Creation         ||")
    print("||      Powered by: .claude/skills/lark-agent                  ||")
    print("||                                                              ||")
    print("=" * 70)
    print("=" * 70)
    print("\n")

def main():
    """Main entry point"""
    print_banner()
    
    # Check if arguments provided
    if len(sys.argv) > 1:
        # Direct mode - pass to lark_agent.py
        print("📋 Mode: DIRECT (arguments provided)")
        print("🔄 Invoking: lark_agent.py\n")
        
        from lark_agent import LarkAgent
        import argparse
        
        # Parse arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('input_file', help='Markdown test file')
        parser.add_argument('--owner', default='Test User')
        parser.add_argument('--priority', default='medium')
        parser.add_argument('--task-list-id', default=None)
        parser.add_argument('--target-date', default=None)
        parser.add_argument('--start-date', default=None)
        parser.add_argument('--timezone', default='UTC')
        
        args = parser.parse_args()
        
        # Execute
        agent = LarkAgent()
        result = agent.execute(args)
        
        return result
    else:
        # Interactive mode - use interactive script
        print("📋 Mode: INTERACTIVE (no arguments)")
        print("🔄 Invoking: lark_agent_interactive.py\n")
        
        from lark_agent_interactive import InteractiveLarkAgent
        
        agent = InteractiveLarkAgent()
        result = agent.execute()
        
        return result

if __name__ == '__main__':
    try:
        result = main()
        
        # Print result for Claude Code to process
        import json
        print("\n" + "="*70)
        print("📤 WORKFLOW OUTPUT FOR CLAUDE CODE")
        print("="*70)
        print(json.dumps(result, indent=2))
        
        sys.exit(0 if result.get('success') else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

