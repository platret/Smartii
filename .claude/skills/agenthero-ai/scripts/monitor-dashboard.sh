#!/bin/bash
# Project Orchestration Monitor Dashboard
# Real-time monitoring of active topics and sub-agent tasks
# Usage: bash monitor-dashboard.sh [--watch]

# Add Scoop to PATH first (before set -e) - try multiple approaches
if [[ -d "$HOME/scoop/shims" ]]; then
    export PATH="$HOME/scoop/shims:$PATH"
fi
# Also try USERPROFILE for Windows compatibility
if [[ -n "${USERPROFILE:-}" ]] && [[ -d "$USERPROFILE/scoop/shims" ]]; then
    export PATH="$USERPROFILE/scoop/shims:$PATH"
fi
# Fallback to common Windows location
if [[ -d "/c/Users/$USER/scoop/shims" ]]; then
    export PATH="/c/Users/$USER/scoop/shims:$PATH"
fi

set -euo pipefail

# Source utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils.sh"

STATE_DIR=".claude/agents/state"
TOPICS_FILE="$STATE_DIR/topics.json"

# Colors
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'

# Status icons
ICON_COMPLETED="✓"
ICON_IN_PROGRESS="⟳"
ICON_PENDING="○"
ICON_BLOCKED="⚠"
ICON_FAILED="✗"

# Clear screen function
clear_screen() {
    clear
    echo -ne "\033[0;0H"
}

# Print header
print_header() {
    echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}${CYAN}║${RESET}  ${BOLD}Project Orchestration Dashboard${RESET}                           ${BOLD}${CYAN}║${RESET}"
    echo -e "${BOLD}${CYAN}║${RESET}  ${DIM}Real-time monitoring of parallel sub-agent tasks${RESET}         ${BOLD}${CYAN}║${RESET}"
    echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════════╝${RESET}"
    echo ""
}

# Get status icon
get_status_icon() {
    local status=$1
    case "$status" in
        "completed") echo -e "${GREEN}${ICON_COMPLETED}${RESET}" ;;
        "in_progress") echo -e "${YELLOW}${ICON_IN_PROGRESS}${RESET}" ;;
        "pending") echo -e "${BLUE}${ICON_PENDING}${RESET}" ;;
        "blocked") echo -e "${RED}${ICON_BLOCKED}${RESET}" ;;
        "failed") echo -e "${RED}${ICON_FAILED}${RESET}" ;;
        *) echo -e "${DIM}?${RESET}" ;;
    esac
}

# Get progress bar
get_progress_bar() {
    local progress=$1
    local width=20
    local filled=$((progress * width / 100))
    local empty=$((width - filled))

    local bar=""
    for ((i=0; i<filled; i++)); do bar+="█"; done
    for ((i=0; i<empty; i++)); do bar+="░"; done

    if [[ $progress -eq 100 ]]; then
        echo -e "${GREEN}${bar}${RESET} ${progress}%"
    elif [[ $progress -gt 0 ]]; then
        echo -e "${YELLOW}${bar}${RESET} ${progress}%"
    else
        echo -e "${DIM}${bar}${RESET} ${progress}%"
    fi
}

# Format time ago
time_ago() {
    local timestamp=$1

    if [[ -z "$timestamp" ]] || [[ "$timestamp" == "null" ]]; then
        echo "N/A"
        return
    fi

    local now=$(date +%s)
    local then=$(date -d "$timestamp" +%s 2>/dev/null || echo $now)
    local diff=$((now - then))

    if [[ $diff -lt 60 ]]; then
        echo "${diff}s ago"
    elif [[ $diff -lt 3600 ]]; then
        echo "$((diff / 60))m ago"
    elif [[ $diff -lt 86400 ]]; then
        echo "$((diff / 3600))h ago"
    else
        echo "$((diff / 86400))d ago"
    fi
}

# Display topic summary
display_topic() {
    local topic_slug=$1
    local topic_dir="$STATE_DIR/$topic_slug"

    if [[ ! -d "$topic_dir" ]]; then
        return
    fi

    local topic_json="$topic_dir/topic.json"
    if [[ ! -f "$topic_json" ]]; then
        return
    fi

    # Read topic metadata
    local title=$(jq -r '.title' "$topic_json")
    local status=$(jq -r '.status' "$topic_json")
    local created=$(jq -r '.createdAt' "$topic_json")
    local last_active=$(jq -r '.lastActiveAt' "$topic_json")

    # Calculate progress from actual task files
    local total_tasks=0
    local completed_tasks=0
    local progress=0

    # Count actual task files and their status
    for task_file in "$topic_dir"/task-*.json; do
        if [[ -f "$task_file" ]]; then
            total_tasks=$((total_tasks + 1))
            local task_status=$(jq -r '.status // "pending"' "$task_file")
            if [[ "$task_status" == "completed" ]]; then
                completed_tasks=$((completed_tasks + 1))
            fi
        fi
    done

    # Calculate progress percentage
    if [[ $total_tasks -gt 0 ]]; then
        progress=$((completed_tasks * 100 / total_tasks))
    fi

    echo -e "${BOLD}${MAGENTA}📋 Topic:${RESET} ${BOLD}$title${RESET}"
    echo -e "   ${DIM}Slug:${RESET} $topic_slug"
    echo -e "   ${DIM}Created:${RESET} $(time_ago "$created")"
    echo -e "   ${DIM}Last Active:${RESET} $(time_ago "$last_active")"
    echo -e "   ${DIM}Progress:${RESET} $(get_progress_bar $progress) ${DIM}($completed_tasks/$total_tasks tasks)${RESET}"
    echo ""
}

# Display task details
display_task() {
    local task_file=$1

    if [[ ! -f "$task_file" ]]; then
        return
    fi

    local task_id=$(jq -r '.taskId // "unknown"' "$task_file")
    local focus=$(jq -r '.focusArea // "Unknown"' "$task_file")
    local status=$(jq -r '.status // "unknown"' "$task_file")
    local progress=$(jq -r '.progress // 0' "$task_file")
    local current_op=$(jq -r '.currentOperation // "N/A"' "$task_file")
    local started=$(jq -r '.startedAt // null' "$task_file")
    local log_count=$(jq '.logs | length' "$task_file")
    local files_created=$(jq '.filesCreated | length' "$task_file")
    local files_modified=$(jq '.filesModified | length' "$task_file")

    # Get latest log
    local latest_log=$(jq -r '.logs[-1].message // "No logs yet"' "$task_file")
    local latest_time=$(jq -r '.logs[-1].timestamp // null' "$task_file")

    # Get blocking question if any
    local has_question=$(jq -r '.blockingQuestion // null' "$task_file")
    local question_text=""
    if [[ "$has_question" != "null" ]]; then
        question_text=$(jq -r '.blockingQuestion.question // ""' "$task_file")
    fi

    echo -e "   $(get_status_icon "$status") ${BOLD}$task_id${RESET} ${DIM}($focus)${RESET}"
    echo -e "      ${DIM}Status:${RESET} $status $(get_progress_bar $progress)"

    if [[ "$status" == "in_progress" ]] || [[ "$status" == "completed" ]]; then
        echo -e "      ${DIM}Current:${RESET} $current_op"
        echo -e "      ${DIM}Started:${RESET} $(time_ago "$started")"
        echo -e "      ${DIM}Latest:${RESET} $latest_log ${DIM}($(time_ago "$latest_time"))${RESET}"
    fi

    if [[ "$status" == "blocked" ]] && [[ -n "$question_text" ]]; then
        echo -e "      ${RED}${ICON_BLOCKED} Blocked:${RESET} $question_text"
    fi

    echo -e "      ${DIM}Logs: $log_count | Files: +$files_created ~$files_modified${RESET}"
    echo ""
}

# Main dashboard display
show_dashboard() {
    clear_screen
    print_header

    if [[ ! -f "$TOPICS_FILE" ]]; then
        echo -e "${YELLOW}No topics found.${RESET}"
        echo ""
        echo "Run: python .claude/skills/agenthero-ai/scripts/topic_manager.py create_topic \"Your Topic\" --description \"Description\""
        return
    fi

    local active_count=$(jq '.active | length' "$TOPICS_FILE")
    local completed_count=$(jq '.completed | length' "$TOPICS_FILE")

    if [[ $active_count -eq 0 ]]; then
        echo -e "${YELLOW}No active topics.${RESET}"
        echo ""
        echo "Run: python .claude/skills/agenthero-ai/scripts/topic_manager.py create_topic \"Your Topic\" --description \"Description\""
        return
    fi

    echo -e "${BOLD}Active Topics: $active_count${RESET} ${DIM}| Completed: $completed_count${RESET}"
    echo ""

    # Display each active topic
    local topics=$(jq -r '.active[].slug' "$TOPICS_FILE")

    while IFS= read -r topic_slug; do
        if [[ -z "$topic_slug" ]]; then
            continue
        fi

        display_topic "$topic_slug"

        # Display tasks for this topic
        local topic_dir="$STATE_DIR/$topic_slug"
        if [[ -d "$topic_dir" ]]; then
            echo -e "${BOLD}${CYAN}   Sub-Agent Tasks:${RESET}"
            echo ""

            local task_count=0
            for task_file in "$topic_dir"/task-*.json; do
                if [[ -f "$task_file" ]]; then
                    display_task "$task_file"
                    task_count=$((task_count + 1))
                fi
            done

            if [[ $task_count -eq 0 ]]; then
                echo -e "   ${DIM}No tasks created yet${RESET}"
                echo ""
            fi
        fi

        echo -e "${DIM}────────────────────────────────────────────────────────────────${RESET}"
        echo ""
    done <<< "$topics"

    echo -e "${DIM}Last updated: $(date '+%Y-%m-%d %H:%M:%S')${RESET}"
    echo ""
}

# Watch mode - continuously update
watch_dashboard() {
    local interval=${1:-6}  # Default 6 seconds

    echo -e "${GREEN}Starting watch mode (refresh every ${interval}s)...${RESET}"
    echo -e "${DIM}Press Ctrl+C to exit${RESET}"
    sleep 2

    while true; do
        show_dashboard
        sleep "$interval"
    done
}

# Main
main() {
    local watch_mode=false
    local interval=2

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --watch|-w)
                watch_mode=true
                shift
                ;;
            --interval|-i)
                interval=$2
                shift 2
                ;;
            --help|-h)
                echo "Usage: monitor-dashboard.sh [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --watch, -w          Watch mode (continuous updates)"
                echo "  --interval, -i NUM   Update interval in seconds (default: 6)"
                echo "  --help, -h           Show this help message"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    if [[ "$watch_mode" == true ]]; then
        watch_dashboard "$interval"
    else
        show_dashboard
    fi
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
