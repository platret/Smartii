# Instructions for Claude Code

## ⚠️ CRITICAL: TOKEN EFFICIENCY RULES

**THIS SKILL MUST BE EXECUTED WITH MINIMAL TOKEN USAGE!**

The skill is designed to be **SELF-CONTAINED** and do ALL the work internally. Your job is to:
1. Collect parameters from user (if not provided)
2. Execute the skill ONCE
3. Let the skill handle EVERYTHING
4. Display ONLY the final summary

**DO NOT:**
- ❌ Execute workflow steps manually
- ❌ Make individual MCP calls yourself
- ❌ Parse and interpret the workflow output
- ❌ Show verbose progress messages
- ❌ Create tasks one by one

**DO:**
- ✅ Execute the skill script ONCE
- ✅ Let the skill do ALL the work
- ✅ Display ONLY the final result

## When to Activate This Skill

Activate the lark-agent skill when the user:
- Mentions creating Lark tasks from test plans
- Mentions "lark", "test cases", "test planning", "test scenarios"
- Wants to convert markdown test documentation into Lark tasks
- Says things like "create Lark tasks from..." or "process test file..."

## How to Use This Skill (SIMPLIFIED)

### Step 1: Collect Parameters (if not provided)

If user provides all parameters in their request, skip to Step 2.

Otherwise, ask for missing parameters:

1. **📄 Test file path** (REQUIRED)
2. **👤 Owner name** (OPTIONAL, default: "Test User")
3. **⚡ Priority** (OPTIONAL, default: 1 for low, 2 for medium, 3 for high)
4. **📅 Target date** (OPTIONAL, default: 14 days from today)

### Step 2: Execute the Skill ONCE

Run the Python script with parameters:

```bash
python .claude/skills/lark-agent/run.py [file-path] --owner="[owner]" --priority=[priority] --target-date="[date]"
```

**Example:**
```bash
python .claude/skills/lark-agent/run.py tests/manual/login-test.md --owner="rohit" --priority=1 --target-date="2025-12-31"
```

### Step 3: Display ONLY the Final Summary

The skill will output JSON with `execute_immediately: true` flag. When you see this:

1. **Execute the workflow in ONE BATCH** (not step by step)
2. **Show minimal progress** (just "Creating tasks...")
3. **Display final summary** when done

**IMPORTANT:** The skill output contains a `compact_execution` object with ALL MCP calls pre-configured. Execute them ALL AT ONCE without showing individual steps.

## Execution Flow (TOKEN-EFFICIENT)

```
User Request
    ↓
Collect Parameters (if needed)
    ↓
Execute Skill Script ONCE
    ↓
Skill outputs compact execution plan
    ↓
Execute ALL MCP calls in batch
    ↓
Update JSON file
    ↓
Show final summary ONLY
```

## Example Conversation Flow (EFFICIENT)

```
User: Create Lark tasks from tests/manual/login-test.md with owner rohit, priority 1, target 2025-10-23

Claude Code:
🔄 Executing Lark Agent skill...

[Skill executes - shows its own banner and progress]

🏗️ Creating Lark tasks in batch...

[All tasks created in one go]

✅ Completed! Created 15 tasks across 4 scenarios.

📊 Summary:
   📋 Test: User Login Test
   🎯 Scenarios: 4
   📝 Total Tasks: 15
   📁 JSON: tests/manual/login-test.json

🔗 Lark Task List: [URL]
```

## Token Efficiency Guidelines

### ❌ WASTEFUL (OLD WAY - 50K+ tokens)
```
1. Execute skill
2. Parse workflow output
3. Show "Step 1: Creating task list"
4. Call mcp__lark-mcp__task_v2_tasklist_create
5. Show result
6. Show "Step 2: Creating parent task"
7. Call mcp__lark-mcp__task_v2_task_create
8. Show result
... (repeat for every task)
```

### ✅ EFFICIENT (NEW WAY - <5K tokens)
```
1. Execute skill
2. Batch execute ALL MCP calls
3. Show final summary
```

## Important Notes

### ❌ DO NOT Do This

- DO NOT execute workflow steps manually one by one
- DO NOT show verbose progress for each task creation
- DO NOT parse and interpret workflow output step by step
- DO NOT try to run interactive mode (it doesn't work)
- DO NOT waste tokens on intermediate steps

### ✅ DO This

- DO execute the skill script ONCE
- DO let the skill handle everything
- DO execute MCP calls in batch/parallel
- DO show only final summary
- DO minimize token usage

## Troubleshooting

### If the script fails with "EOFError"

This means it's trying to run in interactive mode. Make sure you're passing the file path as the first argument:

```bash
# ❌ Wrong (tries interactive mode)
python .claude/skills/lark-agent/run.py

# ✅ Correct (direct mode)
python .claude/skills/lark-agent/run.py tests/manual/test.md
```

### If user doesn't provide a file path

Ask them: "Which test file would you like to process? Please provide the path to your markdown test file."

## Batch Execution Guide

When the skill returns output with `execute_immediately: true`, follow these steps:

### 1. Parse the Batch Plan

The output contains a `batch_plan` object with `mcp_calls` array. Each call has:
- `id`: Unique identifier
- `tool`: MCP server name (e.g., "lark-mcp")
- `method`: MCP method name (e.g., "task_v2_tasklist_create")
- `params`: Parameters to pass
- `depends_on`: Array of IDs this call depends on
- `save_result_as`: Variable name to save the result

### 2. Execute in Dependency Order

1. Execute calls with no dependencies first
2. Save results using `save_result_as` names
3. Replace template variables in subsequent calls (e.g., `{{tasklist_guid}}`)
4. Execute dependent calls
5. Continue until all calls are executed

### 3. Update JSON File

After all MCP calls complete:
1. Load the JSON file from `json_file` path
2. Update task IDs based on `post_execution.map_results`
3. Set `larkActionsCompleted: true`
4. Set `larkActionsCompletedAt` to current timestamp
5. Save the updated JSON

### 4. Show Final Summary

Display a concise summary:
```
✅ Completed! Created [N] tasks across [M] scenarios.

📊 Summary:
   📋 Test: [title]
   🎯 Scenarios: [count]
   📝 Total Tasks: [count]
   📁 JSON: [path]

🔗 Lark Task List: [URL if available]
```

## Quick Reference

**Skill Activation Triggers:**
- "create lark tasks"
- "process test file"
- "convert test plan to lark"
- "lark task creation"
- mentions "test scenarios" + "lark"

**Required Parameter:**
- Test file path

**Optional Parameters:**
- Owner (default: "Test User")
- Priority (default: 1 for low, 2 for medium, 3 for high)
- Target date (default: 14 days from today)

**Execution Command:**
```bash
python .claude/skills/lark-agent/run.py [file] --owner="[name]" --priority=[1-3] --target-date="YYYY-MM-DD"
```

**Key Principles:**
- ✅ Skill generates complete batch plan
- ✅ Claude Code executes MCP calls in dependency order
- ✅ Minimal token usage (no verbose step-by-step)
- ✅ Fast execution (batch mode)
- ✅ Single final summary only

