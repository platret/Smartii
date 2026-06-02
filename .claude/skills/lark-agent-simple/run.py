#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lark Agent Simple - Entry Point
This script is invoked by Claude Code when /lark-agent-simple command is used
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


def main():
    """Main entry point - delegates to lark_agent_simple.py"""
    from lark_agent_simple import main as parser_main

    # Simply delegate to the parser
    parser_main()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
