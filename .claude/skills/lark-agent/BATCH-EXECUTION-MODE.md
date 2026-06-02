# Lark Agent - Batch Execution Mode

## Problem Statement

The original Lark Agent skill was designed to output a step-by-step workflow plan that Claude Code would then execute manually, one step at a time. This approach had several issues:

### Issues with Old Approach

1. **Token Wasteful**: Claude Code would execute each step verbosely, showing progress for every single task creation
2. **Slow Execution**: Sequential execution of 10-20+ tasks took a long time
3. **Verbose Output**: Hundreds of lines of output for simple operations
4. **Manual Intervention**: Claude Code had to interpret and execute each step

**Example Token Usage (Old Way):**
- Creating 15 tasks across 4 scenarios: **50,000+ tokens**
- Verbose step-by-step execution with progress messages
- Individual MCP calls shown one by one

## Solution: Batch Execution Mode

The new batch execution mode solves these problems by:

1. **Generating a Compact Batch Plan**: The skill outputs a single, structured JSON plan
2. **Dependency-Based Execution**: All MCP calls are pre-configured with dependencies
3. **Minimal Output**: Only final summary is shown
4. **Fast Execution**: All tasks created in batch

**Example Token Usage (New Way):**
- Creating 15 tasks across 4 scenarios: **<5,000 tokens**
- Compact batch plan execution
- Single final summary

## Architecture Changes

### Old Architecture

```
User Request
    ↓
Skill Execution
    ↓
Outputs Step-by-Step Workflow
    ↓
Claude Code Interprets Each Step
    ↓
Executes MCP Call 1 → Shows Result
    ↓
Executes MCP Call 2 → Shows Result
    ↓
... (repeat for every task)
    ↓
Final Summary
```

### New Architecture

```
User Request
    ↓
Skill Execution
    ↓
Outputs Compact Batch Plan
    ↓
Claude Code Executes ALL MCP Calls in Batch
    ↓
Updates JSON File
    ↓
Shows Final Summary ONLY
```

## Key Components

### 1. LarkBatchExecutor (`lark_batch_executor.py`)

New module that generates a compact batch execution plan:

- **Input**: JSON file with test structure
- **Output**: Compact batch plan with all MCP calls pre-configured
- **Features**:
  - Dependency tracking
  - Template variable support
  - Metadata for result mapping
  - Post-execution instructions

### 2. Modified LarkAgent (`lark_agent.py`)

Updated to use batch executor instead of step-by-step workflow:

- Removed: `LarkTaskCreator` and `LarkTaskVerifier`
- Added: `LarkBatchExecutor`
- Changed: `create_lark_tasks()` → `create_lark_tasks_batch()`
- Simplified: Return structure with `execute_immediately: true` flag

### 3. Updated Instructions (`CLAUDE-CODE-INSTRUCTIONS.md`)

New instructions emphasize:

- **Token efficiency** as top priority
- **Batch execution** as the only mode
- **Minimal output** requirement
- **No step-by-step** execution

## Batch Plan Structure

```json
{
  "execute_immediately": true,
  "execution_mode": "batch",
  "summary": {
    "test_title": "...",
    "scenarios_count": 4,
    "tasks_count": 15
  },
  "mcp_calls": [
    {
      "id": "tasklist",
      "tool": "lark-mcp",
      "method": "task_v2_tasklist_create",
      "params": { ... },
      "save_result_as": "tasklist_guid"
    },
    {
      "id": "parent_task",
      "tool": "lark-mcp",
      "method": "task_v2_task_create",
      "params": {
        "data": {
          "tasklists": [{"tasklist_guid": "{{tasklist_guid}}"}]
        }
      },
      "depends_on": ["tasklist"],
      "save_result_as": "parent_task_guid"
    },
    // ... more calls
  ],
  "post_execution": {
    "action": "update_json",
    "json_path": "...",
    "map_results": { ... }
  }
}
```

## Execution Flow

### For Claude Code

1. **Receive batch plan** from skill execution
2. **Parse mcp_calls** array
3. **Execute in dependency order**:
   - Execute calls with no dependencies
   - Save results using `save_result_as` names
   - Replace template variables (e.g., `{{tasklist_guid}}`)
   - Execute dependent calls
4. **Update JSON file** with task IDs
5. **Show final summary** only

### Template Variable Replacement

Template variables use double curly braces: `{{variable_name}}`

Example:
```json
{
  "params": {
    "data": {
      "parent_task_guid": "{{parent_task_guid}}"
    }
  }
}
```

After execution of the `parent_task` call, replace `{{parent_task_guid}}` with the actual GUID returned.

## Benefits

### Token Efficiency

- **90% reduction** in token usage
- No verbose intermediate output
- Compact JSON structure

### Speed

- **Batch execution** is much faster
- No waiting between steps
- Parallel execution possible

### Maintainability

- **Single source of truth**: Batch plan contains everything
- **Easy to debug**: All MCP calls in one structure
- **Testable**: Can validate plan without execution

### User Experience

- **Clean output**: Only final summary shown
- **Fast feedback**: Results appear quickly
- **Professional**: No verbose progress spam

## Migration Guide

### For Skill Developers

If you're updating the skill:

1. Replace `LarkTaskCreator` with `LarkBatchExecutor`
2. Update return structure to include `execute_immediately: true`
3. Generate `mcp_calls` array with dependencies
4. Add `post_execution` instructions

### For Claude Code

If you're implementing batch execution:

1. Check for `execute_immediately: true` flag
2. Parse `batch_plan.mcp_calls` array
3. Execute in dependency order
4. Replace template variables
5. Update JSON file
6. Show final summary only

## Testing

### Test the Batch Executor

```bash
python .claude/skills/lark-agent/scripts/lark_batch_executor.py tests/manual/test.json
```

### Test the Full Skill

```bash
python .claude/skills/lark-agent/run.py tests/manual/test.md --owner="Test User" --priority=1 --target-date="2025-12-31"
```

### Verify Output

The output should contain:
- `execute_immediately: true`
- `execution_mode: "batch"`
- `batch_plan.mcp_calls` array
- `post_execution` instructions

## Future Enhancements

1. **Parallel Execution**: Execute independent calls in parallel
2. **Error Handling**: Retry logic for failed calls
3. **Progress Tracking**: Optional minimal progress indicator
4. **Validation**: Pre-execution validation of batch plan
5. **Dry Run**: Test mode without actual execution

## Conclusion

The batch execution mode transforms the Lark Agent skill from a verbose, token-wasteful workflow into a compact, efficient, and fast execution engine. This is the new standard for all skill development.

**Key Takeaway**: Skills should do ALL the work and output compact, executable plans. Claude Code should execute plans efficiently without verbose intermediate steps.

