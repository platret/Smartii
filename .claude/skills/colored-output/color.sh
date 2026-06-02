#!/bin/bash
# Colored Output Formatter
# Usage: bash color.sh [type] [component] [message]

TYPE=$1
COMPONENT=$2
MESSAGE=$3

# ANSI Color Codes
RESET='\033[0m'
BOLD='\033[1m'

# Component Colors
SKILL_COLOR='\033[1;34m'      # Bold Blue
AGENT_COLOR='\033[1;35m'      # Bold Purple
COMMAND_COLOR='\033[1;32m'    # Bold Green

# Status Colors
SUCCESS_COLOR='\033[1;32m'    # Bold Green
ERROR_COLOR='\033[1;31m'      # Bold Red
WARNING_COLOR='\033[1;33m'    # Bold Yellow
INFO_COLOR='\033[1;36m'       # Bold Cyan
PROGRESS_COLOR='\033[0;34m'   # Blue

# Icons
SKILL_ICON='🔧'
AGENT_ICON='🤖'
COMMAND_ICON='⚡'
SUCCESS_ICON='✅'
ERROR_ICON='❌'
WARNING_ICON='⚠️'
INFO_ICON='ℹ️'
PROGRESS_ICON='▶'

case "$TYPE" in
    skill-header)
        echo -e "${SKILL_COLOR}${SKILL_ICON} [${COMPONENT}]${RESET} ${MESSAGE}"
        ;;
    agent-header)
        echo -e "${AGENT_COLOR}${AGENT_ICON} [${COMPONENT}]${RESET} ${MESSAGE}"
        ;;
    command-header)
        echo -e "${COMMAND_COLOR}${COMMAND_ICON} [${COMPONENT}]${RESET} ${MESSAGE}"
        ;;
    success)
        echo -e "${SUCCESS_COLOR}${SUCCESS_ICON}${RESET} ${MESSAGE}"
        ;;
    error)
        echo -e "${ERROR_COLOR}${ERROR_ICON}${RESET} ${MESSAGE}"
        ;;
    warning)
        echo -e "${WARNING_COLOR}${WARNING_ICON}${RESET} ${MESSAGE}"
        ;;
    info)
        echo -e "${INFO_COLOR}${INFO_ICON}${RESET} ${MESSAGE}"
        ;;
    progress)
        echo -e "${PROGRESS_COLOR}${PROGRESS_ICON}${RESET} ${MESSAGE}"
        ;;
    *)
        echo -e "${MESSAGE}"
        ;;
esac
