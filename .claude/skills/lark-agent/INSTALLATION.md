# Lark Agent Skill - Installation & Setup Guide

## ✅ Installation Complete

The Lark Agent skill has been successfully created and installed in your Claude Code workspace!

## 📦 What Was Created

### Skill Structure

```
.claude/skills/lark-agent/
├── SKILL.md                          # Main skill documentation
├── README.md                         # Quick start guide
├── INSTALLATION.md                   # This file
├── scripts/
│   ├── lark_agent.py                # Main orchestrator (Python)
│   └── markdown_parser.py           # Markdown parsing logic (Python)
├── references/
│   ├── usage-guide.md               # Detailed usage examples
│   ├── json-schema.md               # JSON structure specification
│   └── markdown-format.md           # Markdown format requirements
└── assets/
    └── templates/
        ├── test-template.md         # Example markdown template
        └── output-template.json     # Example JSON output
```

### Command Integration

```
.claude/commands/lark-agent.md       # Command for easy invocation
```

### Packaged Skill

```
lark-agent.zip                       # Distributable skill package
```

## 🚀 How to Use

### Method 1: Natural Language (Recommended)

Simply ask Claude Code to process your test file:

```
Process this test file with lark-agent: tests/manual/my-test.md
```

Claude Code will automatically:
1. Detect the lark-agent skill
2. Parse the markdown file
3. Generate JSON structure
4. Create Lark tasks via MCP

### Method 2: Command Invocation

Use the command directly:

```
/lark-agent tests/manual/my-test.md --owner="QA Team" --target-date="2025-12-31"
```

### Method 3: Direct Script Execution

Run the Python script directly:

```bash
python .claude/skills/lark-agent/scripts/lark_agent.py tests/manual/my-test.md --owner="QA Team"
```

## 📝 Markdown Format

Your test files should follow this structure:

```markdown
# Test Title
Brief description of the test

## Test Scenario: Scenario Name
Description of what this scenario tests

### Task: Task Name
1. First step to perform
2. Second step to perform
3. Third step to perform
Expected Result: What should happen
```

**Key Requirements:**
- H1 (#) for test title
- H2 (##) for scenarios (must start with "Test Scenario:")
- H3 (###) for tasks (must start with "Task:")
- Numbered steps (1., 2., 3., etc.)
- "Expected Result:" line for each task

## 🔧 Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--owner` | Assign owner to tasks | "Test User" |
| `--target-date` | Target completion date (YYYY-MM-DD) | 14 days from now |
| `--start-date` | Start date (YYYY-MM-DD) | Today |
| `--priority` | Task priority (low/medium/high) | medium |
| `--timezone` | Timezone for date calculations | UTC |

## 📊 Workflow

```
┌─────────────────┐
│  Markdown File  │
│   (test.md)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Markdown Parser │ ← lark_agent.py
│  (Python)       │   markdown_parser.py
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  JSON Structure │
│   (test.json)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Lark MCP Tools │ ← Claude Code integration
│  (Task Creation)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Lark Tasks     │
│  (3-level       │
│   hierarchy)    │
└─────────────────┘
```

## 🧪 Testing

### Test the Markdown Parser

Test parsing without creating Lark tasks:

```bash
python .claude/skills/lark-agent/scripts/markdown_parser.py tests/manual/onboarding-timezone-country-currency-test-lark-v2.md
```

This will output the generated JSON structure.

### Test with Reference File

The skill has been tested with:
```
tests/manual/onboarding-timezone-country-currency-test-lark-v2.md
```

Result: ✅ Successfully parsed 4 scenarios with 15 tasks

## 📚 Documentation

### Quick Reference

- **README.md**: Quick start guide
- **SKILL.md**: Complete skill documentation

### Detailed Guides

- **references/usage-guide.md**: Detailed usage examples and best practices
- **references/json-schema.md**: Complete JSON structure specification
- **references/markdown-format.md**: Markdown format requirements and validation

### Templates

- **assets/templates/test-template.md**: Example markdown test file
- **assets/templates/output-template.json**: Example JSON output

## 🔗 Integration with Lark MCP

### Prerequisites

1. **Lark MCP Server**: Must be running and accessible
2. **Lark API Credentials**: Properly configured
3. **Permissions**: Ability to create tasks in Lark

### Lark MCP Tools Used

- `task_v2_task_create` - Create individual tasks
- `task_v2_tasklist_create` - Create task lists
- `task_v2_taskSubtask_create` - Create subtasks
- `task_v2_task_addMembers` - Assign users to tasks

### Task Hierarchy

The skill creates a 3-level hierarchy:

1. **Level 1 (Parent)**: Test overview task
   - Contains overall test information
   - Assigned to specified owner
   - Has target and start dates

2. **Level 2 (Scenarios)**: Scenario tasks
   - Marked as **milestones**
   - Represent major test areas
   - Grouped under parent task

3. **Level 3 (Tasks)**: Individual test tasks
   - Contain actual test steps
   - Include expected results
   - Assigned to team members

## 🎯 Example Usage

### Example 1: Basic Test Processing

```
Process tests/manual/login-test.md with lark-agent
```

**Result:**
- Parses markdown file
- Generates `tests/manual/login-test.json`
- Creates Lark tasks with default settings

### Example 2: QA Team Assignment

```
Process tests/manual/checkout-flow.md with lark-agent --owner="QA Lead" --target-date="2025-11-30"
```

**Result:**
- All tasks assigned to "QA Lead"
- Target date set to November 30, 2025
- Creates hierarchical Lark tasks

### Example 3: High Priority Test

```
Process tests/manual/critical-bug-verification.md with lark-agent --priority=high --owner="Dev Team"
```

**Result:**
- Tasks marked as high priority
- Assigned to "Dev Team"
- Immediate attention in Lark

## 🐛 Troubleshooting

### Common Issues

**Issue**: Markdown parsing fails
- **Check**: Heading hierarchy (H1 > H2 > H3)
- **Check**: "Test Scenario:" prefix on H2 headings
- **Check**: "Task:" prefix on H3 headings
- **Check**: "Expected Result:" line in each task

**Issue**: Lark tasks not created
- **Check**: Lark MCP server is running
- **Check**: API credentials are valid
- **Check**: User has permissions in Lark

**Issue**: User assignment fails
- **Check**: Owner name exists in Lark
- **Check**: Proper user permissions

### Debug Mode

Run the parser independently to debug:

```bash
python .claude/skills/lark-agent/scripts/markdown_parser.py your-test.md
```

This shows the generated JSON without creating Lark tasks.

## 📦 Distribution

The skill has been packaged as:
```
lark-agent.zip
```

This can be shared with other team members or imported into other Claude Code workspaces.

## 🔄 Updates

To update the skill:

1. Modify files in `.claude/skills/lark-agent/`
2. Test changes with sample files
3. Re-package using:
   ```bash
   python .claude/skills/skill-creator/scripts/package_skill.py .claude/skills/lark-agent
   ```

## ✨ Features

- ✅ **Python-based**: Reliable script execution
- ✅ **Markdown parsing**: Structured test extraction
- ✅ **JSON generation**: Standardized format
- ✅ **Lark integration**: Hierarchical task creation
- ✅ **Flexible options**: Customizable owner, dates, priority
- ✅ **Error handling**: Validation and helpful error messages
- ✅ **Documentation**: Comprehensive guides and examples
- ✅ **Templates**: Ready-to-use examples

## 🎉 Success!

The Lark Agent skill is now ready to use. Start by processing your first test file:

```
Process tests/manual/my-test.md with lark-agent
```

Happy testing! 🚀

