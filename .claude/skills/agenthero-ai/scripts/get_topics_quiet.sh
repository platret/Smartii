#!/usr/bin/env bash
# Wrapper to run topic_manager.py in quiet mode
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1
QUIET=1 python topic_manager.py get_active_topics_summary 2>&1 || exit 0
