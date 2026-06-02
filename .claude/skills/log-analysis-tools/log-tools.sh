#!/usr/bin/env bash

# log-tools.sh - Fast log analysis with modern CLI tools
# Version: 1.0.0
# Dependencies: fd (optional), ripgrep (optional), gzip, lnav (optional)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE=""
FRAMEWORK=""
TODAY=$(date +%Y-%m-%d)

# ============================================================================
# Platform Detection & Tool Availability
# ============================================================================

check_dependencies() {
    local missing_required=()
    local missing_optional=()

    # Required tools
    if ! command -v gzip &> /dev/null; then
        missing_required+=("gzip")
    fi

    # Optional but recommended tools
    if ! command -v lnav &> /dev/null; then
        missing_optional+=("lnav")
    fi

    if ! command -v fd &> /dev/null; then
        missing_optional+=("fd")
    fi

    if ! command -v rg &> /dev/null; then
        missing_optional+=("ripgrep")
    fi

    # Report missing required tools
    if [ ${#missing_required[@]} -gt 0 ]; then
        echo -e "${RED}❌ Missing required tools:${NC}"
        for tool in "${missing_required[@]}"; do
            echo "  - $tool"
        done
        echo ""
        echo "Install with:"
        echo "  Mac:    brew install ${missing_required[*]}"
        echo "  Ubuntu: sudo apt install ${missing_required[*]}"
        exit 1
    fi

    # Report missing optional tools
    if [ ${#missing_optional[@]} -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Missing optional tools (enhanced features):${NC}"
        for tool in "${missing_optional[@]}"; do
            echo "  - $tool"
        done
        echo ""
        echo "Install for better performance:"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "  brew install lnav fd ripgrep"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            echo "  sudo apt install lnav fd-find ripgrep"
        fi
        echo ""
    fi
}

# ============================================================================
# Framework Detection
# ============================================================================

detect_framework() {
    # Laravel
    if [[ -f "artisan" && -f "composer.json" ]]; then
        FRAMEWORK="laravel"
        LOG_FILE="storage/logs/laravel.log"
        return 0
    fi

    # CodeIgniter 4
    if [[ -f "spark" && -d "app/Config" ]]; then
        FRAMEWORK="codeigniter4"
        # Find latest log file
        if command -v fd &> /dev/null; then
            LOG_FILE=$(fd -e log . writable/logs | head -1)
        else
            LOG_FILE=$(find writable/logs -name "*.log" 2>/dev/null | head -1)
        fi
        return 0
    fi

    # CodeIgniter 3
    if [[ -d "application/config" && -d "application/logs" ]]; then
        FRAMEWORK="codeigniter3"
        if command -v fd &> /dev/null; then
            LOG_FILE=$(fd -e php . application/logs | head -1)
        else
            LOG_FILE=$(find application/logs -name "*.php" 2>/dev/null | head -1)
        fi
        return 0
    fi

    # Symfony
    if [[ -f "bin/console" && -f "composer.json" ]] && grep -q "symfony" composer.json 2>/dev/null; then
        FRAMEWORK="symfony"
        LOG_FILE="var/log/dev.log"
        [[ ! -f "$LOG_FILE" ]] && LOG_FILE="var/log/prod.log"
        return 0
    fi

    # Next.js
    if [[ -f "next.config.js" ]] || [[ -d ".next" ]]; then
        FRAMEWORK="nextjs"
        LOG_FILE=".next/trace"
        return 0
    fi

    # Express.js
    if [[ -f "package.json" ]] && grep -q "express" package.json 2>/dev/null; then
        FRAMEWORK="express"
        # Common Express log locations
        if [[ -d "logs" ]]; then
            if command -v fd &> /dev/null; then
                LOG_FILE=$(fd -e log . logs | head -1)
            else
                LOG_FILE=$(find logs -name "*.log" 2>/dev/null | head -1)
            fi
        fi
        return 0
    fi

    # Django
    if [[ -f "manage.py" ]]; then
        FRAMEWORK="django"
        LOG_FILE="logs/django.log"
        return 0
    fi

    # Flask
    if [[ -f "app.py" ]] && grep -q "Flask" app.py 2>/dev/null; then
        FRAMEWORK="flask"
        LOG_FILE="instance/logs/app.log"
        return 0
    fi

    # Fallback - search for common log files
    if [[ -f "storage/logs/laravel.log" ]]; then
        FRAMEWORK="laravel"
        LOG_FILE="storage/logs/laravel.log"
        return 0
    fi

    echo -e "${RED}❌ Unable to detect framework${NC}"
    echo "Please specify log file manually:"
    echo "  bash log-tools.sh view /path/to/logfile.log"
    return 1
}

# ============================================================================
# Command: View Logs
# ============================================================================

cmd_view() {
    local log_path="${1:-$LOG_FILE}"

    if [[ ! -f "$log_path" ]]; then
        echo -e "${RED}❌ Log file not found: $log_path${NC}"
        return 1
    fi

    echo -e "${GREEN}📄 Viewing logs: $log_path${NC}"
    echo -e "${BLUE}Framework: $FRAMEWORK${NC}"
    echo ""

    # Use lnav if available (best experience)
    if command -v lnav &> /dev/null; then
        echo "Opening with lnav (press 'q' to quit, 'e' for errors only, '/' to search)"
        echo ""
        lnav "$log_path"
    # Fallback to bat if available
    elif command -v bat &> /dev/null; then
        echo "Opening with bat (lnav not available - install for better experience)"
        echo ""
        bat "$log_path"
    # Final fallback to less
    else
        echo "Opening with less (install lnav for better experience)"
        echo ""
        less +F "$log_path"
    fi
}

# ============================================================================
# Command: Extract Errors (Last 24h)
# ============================================================================

cmd_errors() {
    local log_path="${1:-$LOG_FILE}"

    if [[ ! -f "$log_path" ]]; then
        echo -e "${RED}❌ Log file not found: $log_path${NC}"
        return 1
    fi

    echo -e "${GREEN}🔍 Extracting errors from: $log_path${NC}"
    echo -e "${BLUE}Date: $TODAY (last 24 hours)${NC}"
    echo "═══════════════════════════════════════════════════"
    echo ""

    # Use ripgrep if available (20x faster than grep)
    if command -v rg &> /dev/null; then
        # Extract ERROR, CRITICAL, and WARNING levels from today
        rg -i "(error|critical|warning|exception|fatal)" "$log_path" \
            | rg "$TODAY" \
            | head -100
    else
        # Fallback to grep
        grep -iE "(error|critical|warning|exception|fatal)" "$log_path" \
            | grep "$TODAY" \
            | head -100
    fi

    echo ""
    echo "═══════════════════════════════════════════════════"

    # Count errors
    local error_count=0
    if command -v rg &> /dev/null; then
        error_count=$(rg -i "(error|critical|warning|exception|fatal)" "$log_path" | rg "$TODAY" | wc -l)
    else
        error_count=$(grep -iE "(error|critical|warning|exception|fatal)" "$log_path" | grep "$TODAY" | wc -l)
    fi

    echo -e "${YELLOW}📊 Total errors found: $error_count${NC}"
}

# ============================================================================
# Command: Tail Logs (Real-Time)
# ============================================================================

cmd_tail() {
    local log_path="${1:-$LOG_FILE}"
    local level="${2:-all}"

    if [[ ! -f "$log_path" ]]; then
        echo -e "${RED}❌ Log file not found: $log_path${NC}"
        return 1
    fi

    echo -e "${GREEN}📡 Tailing logs: $log_path${NC}"
    echo -e "${BLUE}Level filter: $level${NC}"
    echo "Press Ctrl+C to stop"
    echo ""

    if [[ "$level" == "all" ]]; then
        tail -f "$log_path" | bat --paging=never -l log 2>/dev/null || tail -f "$log_path"
    else
        tail -f "$log_path" | grep -i "$level" | bat --paging=never -l log 2>/dev/null || tail -f "$log_path" | grep -i "$level"
    fi
}

# ============================================================================
# Command: Search Logs
# ============================================================================

cmd_search() {
    local pattern="$1"
    local log_path="${2:-$LOG_FILE}"
    local context="${3:-5}"

    if [[ ! -f "$log_path" ]]; then
        echo -e "${RED}❌ Log file not found: $log_path${NC}"
        return 1
    fi

    echo -e "${GREEN}🔍 Searching for: \"$pattern\"${NC}"
    echo -e "${BLUE}Log file: $log_path${NC}"
    echo -e "${BLUE}Context: $context lines before/after${NC}"
    echo "═══════════════════════════════════════════════════"
    echo ""

    # Use ripgrep if available (with context)
    if command -v rg &> /dev/null; then
        rg -C "$context" -i "$pattern" "$log_path" | bat --paging=always -l log 2>/dev/null || rg -C "$context" -i "$pattern" "$log_path"
    else
        # Fallback to grep with context
        grep -C "$context" -i "$pattern" "$log_path" | bat --paging=always -l log 2>/dev/null || grep -C "$context" -i "$pattern" "$log_path"
    fi
}

# ============================================================================
# Command: Prune Logs (Archive Old Entries)
# ============================================================================

cmd_prune() {
    local log_path="${1:-$LOG_FILE}"
    local keep_days="${2:-1}"  # Default: keep today only
    local dry_run="${3:-false}"

    if [[ ! -f "$log_path" ]]; then
        echo -e "${RED}❌ Log file not found: $log_path${NC}"
        return 1
    fi

    local log_dir=$(dirname "$log_path")
    local log_name=$(basename "$log_path")
    local archive_dir="$log_dir/archive"

    # Create archive directory
    mkdir -p "$archive_dir"

    # Calculate cutoff date
    local cutoff_date
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Mac date command
        cutoff_date=$(date -v-${keep_days}d +%Y-%m-%d)
    else
        # Linux date command
        cutoff_date=$(date -d "$keep_days days ago" +%Y-%m-%d)
    fi

    echo -e "${GREEN}📦 Log Pruning Configuration${NC}"
    echo "═══════════════════════════════════════════════════"
    echo "Log file: $log_path"
    echo "Keep entries from: $cutoff_date onwards (last $keep_days day(s))"
    echo "Archive directory: $archive_dir"
    echo "Dry run: $dry_run"
    echo ""

    # Get current log size
    local current_size=$(du -h "$log_path" | cut -f1)
    echo "Current log size: $current_size"
    echo ""

    if [[ "$dry_run" == "true" ]]; then
        echo -e "${YELLOW}⚠️  DRY RUN - No changes will be made${NC}"
        echo ""
        echo "Would extract entries older than $cutoff_date to:"
        echo "  $archive_dir/${TODAY}_archive.log.gz"
        echo ""
        echo "To actually prune, run without --dry-run"
        return 0
    fi

    # Extract old entries
    echo "Extracting old entries..."
    local temp_old="/tmp/log_old_$$.log"
    local temp_new="/tmp/log_new_$$.log"

    # Split log file by date
    if command -v rg &> /dev/null; then
        # New entries (keep)
        rg "$cutoff_date|$(date +%Y-%m-%d)" "$log_path" > "$temp_new" || true

        # Old entries (archive)
        rg -v "$cutoff_date|$(date +%Y-%m-%d)" "$log_path" > "$temp_old" || true
    else
        # Fallback to grep
        grep -E "$cutoff_date|$(date +%Y-%m-%d)" "$log_path" > "$temp_new" || true
        grep -vE "$cutoff_date|$(date +%Y-%m-%d)" "$log_path" > "$temp_old" || true
    fi

    # Archive old entries (compressed)
    if [[ -s "$temp_old" ]]; then
        local archive_file="$archive_dir/${TODAY}_archive.log.gz"
        gzip -c "$temp_old" > "$archive_file"

        local archived_size=$(du -h "$archive_file" | cut -f1)
        echo -e "${GREEN}✅ Archived old entries to: $archive_file ($archived_size)${NC}"
    else
        echo -e "${YELLOW}⚠️  No old entries to archive${NC}"
    fi

    # Replace log file with new entries only
    if [[ -s "$temp_new" ]]; then
        cp "$log_path" "$log_path.backup"
        cat "$temp_new" > "$log_path"

        local new_size=$(du -h "$log_path" | cut -f1)
        echo -e "${GREEN}✅ Updated log file${NC}"
        echo "  Before: $current_size"
        echo "  After:  $new_size"
        echo "  Backup: $log_path.backup"
    else
        echo -e "${YELLOW}⚠️  No recent entries found (log would be empty)${NC}"
        echo "Keeping original log file unchanged"
    fi

    # Cleanup temp files
    rm -f "$temp_old" "$temp_new"

    echo ""
    echo -e "${GREEN}✅ Pruning complete!${NC}"
}

# ============================================================================
# Command: Statistics
# ============================================================================

cmd_stats() {
    local log_path="${1:-$LOG_FILE}"

    if [[ ! -f "$log_path" ]]; then
        echo -e "${RED}❌ Log file not found: $log_path${NC}"
        return 1
    fi

    echo -e "${GREEN}📊 Log Statistics: $log_path${NC}"
    echo "═══════════════════════════════════════════════════"
    echo ""

    # File info
    local file_size=$(du -h "$log_path" | cut -f1)
    local line_count=$(wc -l < "$log_path")

    echo "📁 File Info:"
    echo "  Size: $file_size"
    echo "  Lines: $(printf "%'d" $line_count)"
    echo ""

    # Error breakdown
    echo "📈 Error Breakdown (Last 7 days):"

    if command -v rg &> /dev/null; then
        local critical_count=$(rg -i "critical" "$log_path" | wc -l)
        local error_count=$(rg -i "error" "$log_path" | grep -iv "critical" | wc -l)
        local warning_count=$(rg -i "warning" "$log_path" | wc -l)
        local info_count=$(rg -i "info" "$log_path" | wc -l)
    else
        local critical_count=$(grep -i "critical" "$log_path" | wc -l)
        local error_count=$(grep -i "error" "$log_path" | grep -iv "critical" | wc -l)
        local warning_count=$(grep -i "warning" "$log_path" | wc -l)
        local info_count=$(grep -i "info" "$log_path" | wc -l)
    fi

    echo "  CRITICAL: $critical_count"
    echo "  ERROR: $error_count"
    echo "  WARNING: $warning_count"
    echo "  INFO: $info_count"
    echo ""

    # Top errors (if ripgrep available)
    if command -v rg &> /dev/null; then
        echo "🔥 Top 5 Error Messages:"
        rg -i "(error|critical)" "$log_path" \
            | cut -d':' -f4- \
            | sort \
            | uniq -c \
            | sort -rn \
            | head -5 \
            | nl
        echo ""
    fi

    echo "💡 Recommendation:"
    if [[ $line_count -gt 100000 ]]; then
        echo "  Log file is large ($line_count lines). Consider pruning:"
        echo "  bash log-tools.sh prune"
    else
        echo "  Log file size is manageable"
    fi
}

# ============================================================================
# Command: Merge Multiple Logs
# ============================================================================

cmd_merge() {
    shift  # Remove 'merge' command from args
    local log_files=("$@")

    if [[ ${#log_files[@]} -eq 0 ]]; then
        echo -e "${RED}❌ No log files specified${NC}"
        echo "Usage: bash log-tools.sh merge file1.log file2.log ..."
        return 1
    fi

    # Check all files exist
    for log in "${log_files[@]}"; do
        if [[ ! -f "$log" ]]; then
            echo -e "${RED}❌ File not found: $log${NC}"
            return 1
        fi
    done

    echo -e "${GREEN}📊 Merging ${#log_files[@]} log files${NC}"
    echo "═══════════════════════════════════════════════════"
    for log in "${log_files[@]}"; do
        echo "  - $log"
    done
    echo ""

    # Use lnav if available (best for multi-file viewing)
    if command -v lnav &> /dev/null; then
        echo "Opening with lnav (automatically merged by timestamp)"
        echo ""
        lnav "${log_files[@]}"
    else
        echo -e "${YELLOW}⚠️  lnav not available - showing files sequentially${NC}"
        echo "Install lnav for proper timestamp-based merging:"
        echo "  Mac: brew install lnav"
        echo "  Linux: sudo apt install lnav"
        echo ""

        for log in "${log_files[@]}"; do
            echo -e "${BLUE}=== $log ===${NC}"
            tail -100 "$log"
            echo ""
        done
    fi
}

# ============================================================================
# Main Command Router
# ============================================================================

main() {
    # Check dependencies first
    check_dependencies

    local command="${1:-help}"

    # Auto-detect framework for commands that need it
    if [[ "$command" != "help" && "$command" != "merge" ]]; then
        if [[ -z "${2:-}" ]]; then
            detect_framework || exit 1
        else
            # Manual log file provided
            LOG_FILE="$2"
        fi
    fi

    case "$command" in
        view)
            cmd_view "${2:-}"
            ;;
        errors)
            cmd_errors "${2:-}"
            ;;
        tail)
            cmd_tail "${2:-}" "${3:-all}"
            ;;
        search)
            if [[ -z "${2:-}" ]]; then
                echo -e "${RED}❌ Search pattern required${NC}"
                echo "Usage: bash log-tools.sh search \"pattern\" [logfile] [context_lines]"
                exit 1
            fi
            cmd_search "$2" "${3:-$LOG_FILE}" "${4:-5}"
            ;;
        prune)
            local dry_run="false"
            [[ "${3:-}" == "--dry-run" ]] && dry_run="true"
            cmd_prune "${2:-}" "1" "$dry_run"
            ;;
        stats)
            cmd_stats "${2:-}"
            ;;
        merge)
            cmd_merge "$@"
            ;;
        help|--help|-h)
            cat << EOF
${GREEN}Log Analysis Tools${NC}
Fast log analysis with modern CLI tools

${BLUE}Usage:${NC}
  bash log-tools.sh <command> [options]

${BLUE}Commands:${NC}
  view [logfile]              View logs with lnav/bat/less
  errors [logfile]            Extract errors from last 24h
  tail [logfile] [level]      Real-time log monitoring
  search <pattern> [logfile]  Search logs with context
  prune [logfile] [--dry-run] Archive old logs (keep today)
  stats [logfile]             Show log statistics
  merge <file1> <file2> ...   Merge multiple log files

${BLUE}Examples:${NC}
  bash log-tools.sh view                     # Auto-detect framework
  bash log-tools.sh errors                   # Show today's errors
  bash log-tools.sh tail ERROR               # Tail ERROR level only
  bash log-tools.sh search "database"        # Search with context
  bash log-tools.sh prune --dry-run          # Preview pruning
  bash log-tools.sh stats                    # Show statistics
  bash log-tools.sh merge app.log error.log  # Merge logs

${BLUE}Install Tools:${NC}
  Mac:    brew install lnav fd ripgrep bat
  Linux:  sudo apt install lnav fd-find ripgrep bat

EOF
            ;;
        *)
            echo -e "${RED}❌ Unknown command: $command${NC}"
            echo "Run 'bash log-tools.sh help' for usage information"
            exit 1
            ;;
    esac
}

# Run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
