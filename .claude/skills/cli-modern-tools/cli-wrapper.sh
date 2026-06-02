#!/usr/bin/env bash
# CLI Modern Tools Wrapper
# Automatically replaces traditional commands with modern alternatives

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Function to suggest and use modern alternative
suggest_and_use() {
    local traditional="$1"
    local modern="$2"
    local fallback_cmd="$3"
    shift 3
    local args=("$@")

    if command_exists "$modern"; then
        echo -e "${GREEN}✓${NC} Using ${BLUE}$modern${NC} instead of ${YELLOW}$traditional${NC}"
        "$modern" "${args[@]}"
    else
        echo -e "${YELLOW}⚠${NC} $modern not found, falling back to $traditional"
        echo -e "${BLUE}Install with:${NC} $fallback_cmd"
        "$traditional" "${args[@]}"
    fi
}

# Main command router
case "${1:-help}" in
    # View file with bat
    view|cat)
        shift
        suggest_and_use "cat" "bat" "scoop install bat" "$@"
        ;;

    # List directory with eza
    list|ls)
        shift
        if command_exists "eza"; then
            echo -e "${GREEN}✓${NC} Using ${BLUE}eza --long --git${NC} instead of ${YELLOW}ls${NC}"
            eza --long --git --color=always "$@"
        else
            echo -e "${YELLOW}⚠${NC} eza not found, falling back to ls"
            echo -e "${BLUE}Install with:${NC} scoop install eza"
            ls -lah "$@"
        fi
        ;;

    # Find files with fd
    find)
        shift
        pattern="${1:-*}"
        path="${2:-.}"

        # Use real fd executable (bypass broken wrappers)
        FD_BIN=""
        if [ -f "C:/Users/rohit/scoop/shims/fd.exe" ]; then
            FD_BIN="C:/Users/rohit/scoop/shims/fd.exe"
        elif command -v fd.exe &> /dev/null; then
            FD_BIN="fd.exe"
        elif command -v fd &> /dev/null && fd --version &> /dev/null; then
            FD_BIN="fd"
        fi

        if [ -n "$FD_BIN" ]; then
            echo -e "${GREEN}✓${NC} Using ${BLUE}fd${NC} instead of ${YELLOW}find${NC} (18x faster)"
            "$FD_BIN" --glob "$pattern" "$path"
        else
            echo -e "${YELLOW}⚠${NC} fd not found, falling back to find"
            echo -e "${BLUE}Install with:${NC} scoop install fd"
            find "$path" -name "$pattern"
        fi
        ;;

    # Tree view with eza
    tree)
        shift
        if command_exists "eza"; then
            echo -e "${GREEN}✓${NC} Using ${BLUE}eza --tree${NC} instead of ${YELLOW}tree${NC}"
            eza --tree --level="${1:-3}" "${@:2}"
        else
            echo -e "${YELLOW}⚠${NC} eza not found, using traditional tree"
            echo -e "${BLUE}Install with:${NC} scoop install eza"
            tree -L "${1:-3}" "${@:2}"
        fi
        ;;

    # Check tool availability
    check)
        echo -e "\n${BLUE}=== CLI Modern Tools Status ===${NC}\n"

        echo -n "bat (better cat): "
        if command_exists bat; then
            echo -e "${GREEN}✓ Installed${NC}"
        else
            echo -e "${RED}✗ Not found${NC} - Install: scoop install bat"
        fi

        echo -n "eza (better ls): "
        if command_exists eza; then
            echo -e "${GREEN}✓ Installed${NC}"
        else
            echo -e "${RED}✗ Not found${NC} - Install: scoop install eza"
        fi

        echo -n "fd (better find): "
        if command_exists fd; then
            echo -e "${GREEN}✓ Installed${NC}"
        else
            echo -e "${RED}✗ Not found${NC} - Install: scoop install fd"
        fi

        echo -n "watchexec (file watcher): "
        if command_exists watchexec; then
            echo -e "${GREEN}✓ Installed${NC}"
        else
            echo -e "${RED}✗ Not found${NC} - Install: scoop install watchexec"
        fi

        echo ""
        ;;

    # Install all tools (Windows - Scoop)
    install)
        echo -e "${BLUE}Installing modern CLI tools via Scoop...${NC}"

        if ! command_exists scoop; then
            echo -e "${RED}Error:${NC} Scoop not found. Install from https://scoop.sh"
            exit 1
        fi

        scoop install bat eza fd watchexec

        echo -e "\n${GREEN}✓ Installation complete!${NC}"
        echo -e "Run: ${BLUE}bash $0 check${NC} to verify"
        ;;

    # Help
    help|--help|-h)
        cat <<EOF
${BLUE}CLI Modern Tools Wrapper${NC}

${GREEN}Usage:${NC}
  bash cli-wrapper.sh <command> [args...]

${GREEN}Commands:${NC}
  ${BLUE}view <file>${NC}        - View file with bat (syntax highlighting)
  ${BLUE}list [dir]${NC}         - List directory with eza (git status, icons)
  ${BLUE}find <pattern>${NC}     - Find files with fd (18x faster)
  ${BLUE}tree [depth]${NC}       - Tree view with eza
  ${BLUE}check${NC}              - Check which modern tools are installed
  ${BLUE}install${NC}            - Install all modern tools (Windows/Scoop)
  ${BLUE}help${NC}               - Show this help

${GREEN}Examples:${NC}
  bash cli-wrapper.sh view app.js
  bash cli-wrapper.sh list app/Models/
  bash cli-wrapper.sh find "*.tsx"
  bash cli-wrapper.sh tree 3
  bash cli-wrapper.sh check

${GREEN}Modern Tools:${NC}
  bat       > cat      (syntax highlighting, line numbers)
  eza       > ls       (git status, icons, colors)
  fd        > find     (18x faster, respects .gitignore)
  watchexec            (auto-run commands on file changes)

${GREEN}Installation:${NC}
  Windows: bash cli-wrapper.sh install
  Mac:     brew install bat eza fd watchexec
  Linux:   apt install bat fd-find && cargo install eza watchexec-cli

EOF
        ;;

    *)
        echo -e "${RED}Error:${NC} Unknown command: $1"
        echo "Run: bash $0 help"
        exit 1
        ;;
esac
