# Lark Agent - Usage Guide

## ✅ Working Mode: Direct Mode

The Lark Agent skill works in **direct mode** where you provide all parameters upfront.

### How to Use

Provide your test file and parameters in one command:

```
python .claude/skills/lark-agent/run.py [file-path] --owner="[name]" --priority=[1-3] --target-date="YYYY-MM-DD"
```

### Example

```
python .claude/skills/lark-agent/run.py tests/manual/onboarding-timezone-country-currency-test-lark-v2.md --owner="rohit" --priority=2 --target-date="2025-10-22"
```

### Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `file-path` | ✅ Yes | Path to markdown test file | `tests/manual/test.md` |
| `--owner` | ❌ No | Task owner name | `--owner="QA Team"` |
| `--priority` | ❌ No | Priority level (1=low, 2=medium, 3=high) | `--priority=2` |
| `--target-date` | ❌ No | Target completion date | `--target-date="2025-12-31"` |
| `--task-list-id` | ❌ No | Existing Lark task list ID | `--task-list-id="abc123"` |

### What It Does

1. **🔍 Parses** your markdown test file
2. **📝 Generates** structured JSON with test hierarchy
3. **🏗️ Prepares** Lark task creation workflow
4. **✅ Prepares** verification workflow
5. **📤 Outputs** complete workflow for execution

### Output

The skill outputs a JSON workflow plan that contains:
- Task list creation request
- Parent task creation request
- Scenario tasks creation requests (marked as milestones)
- Individual tasks creation requests
- Verification steps

This workflow can then be executed via Lark MCP tools to create the actual tasks.

---

## ❌ Interactive Mode Not Supported

Interactive mode (prompting for inputs) does **not work** in Claude Code's current environment because:
- No stdin available for `input()` calls
- Scripts run in non-interactive bash environment
- EOF errors occur when trying to read user input

**Solution:** Use direct mode with all parameters provided upfront (as shown above).

---

## 🎯 Quick Start

### Step 1: Prepare Your Markdown File

Create a test file following this structure:

```markdown
# Test Title
Description of the test

## Test Scenario: Scenario Name
Scenario description

### Task: Task Name
1. Step one
2. Step two
Expected Result: What should happen
```

### Step 2: Run the Skill

```bash
python .claude/skills/lark-agent/run.py tests/manual/your-test.md --owner="Your Name" --priority=2 --target-date="2025-12-31"
```

### Step 3: Review Output

The skill will:
- ✅ Parse your markdown
- ✅ Generate JSON structure
- ✅ Prepare workflow for Lark MCP
- ✅ Output complete plan

### Step 4: Execute Workflow

The JSON output contains all the MCP tool calls needed. Claude Code can then:
1. Create task list in Lark
2. Create parent task
3. Create scenario tasks (as milestones)
4. Create individual tasks
5. Verify all tasks were created correctly

---

## 📋 Example Workflow

```bash
# Run the skill
python .claude/skills/lark-agent/run.py \
  tests/manual/login-test.md \
  --owner="QA Team" \
  --priority=2 \
  --target-date="2025-12-31"

# Output shows:
# ✅ Parsed: 3 scenarios, 12 tasks
# ✅ JSON generated: tests/manual/login-test.json
# ✅ Workflow prepared: 5 steps
# ✅ Verification prepared: 4 steps
# 📤 Complete workflow output as JSON
```

---

## 🔧 Troubleshooting

### Error: "EOFError: EOF when reading a line"

**Cause:** Trying to run interactive mode  
**Solution:** Use direct mode with all parameters

### Error: "File not found"

**Cause:** Invalid file path  
**Solution:** Check the file path is correct and file exists

### Error: "Invalid file type"

**Cause:** File is not .md or .markdown  
**Solution:** Use a markdown file

---

## 📚 More Information

- **Skill Documentation**: `.claude/skills/lark-agent/SKILL.md`
- **README**: `.claude/skills/lark-agent/README.md`
- **Installation**: `.claude/skills/lark-agent/INSTALLATION.md`
- **Markdown Format**: `.claude/skills/lark-agent/references/markdown-format.md`
- **JSON Schema**: `.claude/skills/lark-agent/references/json-schema.md`

