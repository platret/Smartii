# Skill Manager

**Native Python-based skill management for Claude Code**

## Quick Start

```bash
# List all skills
python .claude/skills/skill-manager/scripts/skill-manager.py list

# Enable a skill
python .claude/skills/skill-manager/scripts/skill-manager.py enable colored-output

# Disable a skill
python .claude/skills/skill-manager/scripts/skill-manager.py disable time-helper

# Show skill details
python .claude/skills/skill-manager/scripts/skill-manager.py status changelog-manager

# Export configuration
python .claude/skills/skill-manager/scripts/skill-manager.py export
```

## Features

- ⚡ **90% Token Savings** - Native Python instead of LLM parsing
- 🔍 **Auto-Discovery** - Scans `.claude/skills/` automatically
- 📝 **YAML Parsing** - Reads skill metadata from skill.md frontmatter
- ⚙️ **Permission Management** - Enables/disables skills in settings.local.json
- 📊 **Rich Output** - Formatted lists, JSON export, detailed status
- 🖥️ **Cross-Platform** - Works on Windows, Mac, Linux

## Usage with Claude Code

Use the `/cs-skill-management` slash command for interactive management:

```bash
/cs-skill-management                      # Interactive menu
/cs-skill-management enable <skill-name>  # Quick enable
/cs-skill-management disable <skill-name> # Quick disable
/cs-skill-management status <skill-name>  # Show details
/cs-skill-management list enabled         # List enabled skills
```

## Requirements

- Python 3.6+
- No external dependencies (uses only stdlib)

## Token Efficiency

**Before (LLM-based):**
- Read 6+ skill.md files: ~600-800 tokens
- Parse and format: ~150 tokens
- **Total: ~800-1000 tokens**

**After (Script-based):**
- Run Python script: ~30 tokens
- Parse JSON output: ~20 tokens
- **Total: ~50 tokens**

**Savings: 750-900 tokens per operation (90% reduction)**

## License

Part of the Generic Claude Code Framework
