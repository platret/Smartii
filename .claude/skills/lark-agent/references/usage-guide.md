# Lark Agent Usage Guide

Complete guide for using the Lark Agent skill to convert markdown test documentation into Lark tasks.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Markdown Format](#markdown-format)
3. [Command Line Usage](#command-line-usage)
4. [JSON Output Structure](#json-output-structure)
5. [Lark Task Hierarchy](#lark-task-hierarchy)
6. [Advanced Usage](#advanced-usage)
7. [Examples](#examples)

## Quick Start

### Basic Workflow

1. Create a markdown test file following the required format
2. Run the lark-agent script with your file
3. Review the generated JSON
4. Verify tasks created in Lark

### Minimal Example

```bash
node .claude/skills/lark-agent/scripts/lark-agent.cjs tests/my-test.md
```

This will:
- Parse `tests/my-test.md`
- Generate `tests/my-test.json`
- Create hierarchical tasks in Lark

## Markdown Format

### Required Structure

Your markdown file must follow this hierarchy:

```markdown
# Test Title (H1 - Required)
Brief description of the test

## Test Scenario: Scenario Name (H2 - Required)
Description of what this scenario tests

### Task: Task Name (H3 - Required)
1. Step one
2. Step two
3. Step three
Expected Result: What should happen
```

### Heading Levels

- **H1 (# Title)**: Test overview title
- **H2 (## Test Scenario: ...)**: Individual test scenarios
- **H3 (### Task: ...)**: Individual test tasks/steps

### Task Format

Each task should include:
1. **Title**: Clear, descriptive name
2. **Steps**: Numbered list of actions
3. **Expected Result**: What should happen (required)

Example:
```markdown
### Task: User Login Verification
1. Navigate to login page
2. Enter valid credentials
3. Click "Sign In" button
Expected Result: User should be redirected to dashboard
```

### Multiple Scenarios

You can have multiple scenarios in one test file:

```markdown
# User Authentication Test

## Test Scenario: Successful Login
Test that users can log in with valid credentials

### Task: Login with Email
1. Enter email address
2. Enter password
3. Click login
Expected Result: User logged in successfully

### Task: Verify Dashboard Access
1. Check dashboard loads
2. Verify user name displayed
Expected Result: Dashboard shows user information

## Test Scenario: Failed Login
Test that invalid credentials are rejected

### Task: Login with Wrong Password
1. Enter valid email
2. Enter incorrect password
3. Click login
Expected Result: Error message displayed
```

## Command Line Usage

### Basic Syntax

```bash
node lark-agent.cjs <input-file> [options]
```

### Available Options

#### --owner
Assign an owner to all tasks.

```bash
node lark-agent.cjs test.md --owner="John Doe"
```

#### --target-date
Set the target completion date (YYYY-MM-DD format).

```bash
node lark-agent.cjs test.md --target-date="2025-12-31"
```

Default: 14 days from current date

#### --start-date
Set the start date (YYYY-MM-DD format).

```bash
node lark-agent.cjs test.md --start-date="2025-11-01"
```

Default: Current date

#### --priority
Set task priority level.

```bash
node lark-agent.cjs test.md --priority=high
```

Options: `low`, `medium`, `high`
Default: `medium`

#### --timezone
Specify timezone for date calculations.

```bash
node lark-agent.cjs test.md --timezone="America/New_York"
```

Default: `UTC`

### Combined Options

```bash
node lark-agent.cjs tests/login-test.md \
  --owner="QA Team" \
  --target-date="2025-12-31" \
  --priority=high \
  --timezone="America/Los_Angeles"
```

## JSON Output Structure

The generated JSON follows this structure:

```json
{
  "testOverview": {
    "title": "Test Title",
    "description": "Test description",
    "owner": "Assigned Owner",
    "targetDate": "2025-11-02",
    "startDate": "2025-10-19",
    "status": "pending",
    "larkTaskListId": null,
    "parentTaskId": null,
    "priority": "medium"
  },
  "scenarios": [
    {
      "scenarioId": "scenario-0-1234567890",
      "title": "Scenario Name",
      "description": "Scenario description",
      "expectedOutcome": "",
      "owner": "Assigned Owner",
      "status": "pending",
      "tasks": [
        {
          "taskId": "task-0-0-1234567890",
          "title": "Task Name",
          "description": "Task steps",
          "expectedResult": "Expected outcome",
          "status": "pending",
          "notes": "",
          "lark_task_id": null
        }
      ],
      "lark_task_id": null
    }
  ],
  "larkActionsCompleted": false,
  "larkActionsCompletedAt": null,
  "larksActions": "pending"
}
```

## Lark Task Hierarchy

Tasks are created in Lark with a 3-level hierarchy:

### Level 1: Parent Task
- Created from `testOverview`
- Contains the overall test title and description
- Assigned to specified owner
- Has target and start dates

### Level 2: Scenario Tasks
- Created from each `scenario`
- Marked as **milestones** when they have subtasks
- Grouped under the parent task
- Represent major test scenarios

### Level 3: Individual Tasks
- Created from each `task` within scenarios
- Contain the actual test steps
- Include expected results
- Assigned to team members

### Example Hierarchy

```
📋 User Authentication Test (Parent)
  ├─ 🎯 Successful Login (Scenario/Milestone)
  │   ├─ ✓ Login with Email (Task)
  │   └─ ✓ Verify Dashboard Access (Task)
  └─ 🎯 Failed Login (Scenario/Milestone)
      └─ ✓ Login with Wrong Password (Task)
```

## Advanced Usage

### Custom JSON Modification

After JSON generation, you can manually edit the JSON file before task creation:

1. Run markdown parsing only
2. Edit the generated JSON
3. Run task creation separately

### Batch Processing

Process multiple test files:

```bash
for file in tests/*.md; do
  node lark-agent.cjs "$file" --owner="QA Team"
done
```

### Integration with CI/CD

Include in your CI/CD pipeline:

```yaml
- name: Create Lark Tasks
  run: |
    node .claude/skills/lark-agent/scripts/lark-agent.cjs \
      tests/regression-test.md \
      --owner="CI Bot" \
      --priority=high
```

## Examples

See the `assets/templates/` directory for:
- `test-template.md` - Template markdown file
- `output-template.json` - Example JSON output

### Example 1: Simple Feature Test

Input (`feature-test.md`):
```markdown
# Shopping Cart Feature Test

## Test Scenario: Add Items to Cart
Verify users can add products to shopping cart

### Task: Add Single Item
1. Browse to product page
2. Click "Add to Cart" button
3. Verify cart icon updates
Expected Result: Cart shows 1 item

### Task: Add Multiple Items
1. Add first product
2. Add second product
3. Check cart contents
Expected Result: Cart shows 2 items
```

Command:
```bash
node lark-agent.cjs feature-test.md --owner="Dev Team"
```

### Example 2: Regression Test Suite

Input (`regression-test.md`):
```markdown
# Q4 Regression Test Suite

## Test Scenario: User Registration
Test complete registration flow

### Task: Register New User
1. Fill registration form
2. Submit form
3. Verify email sent
Expected Result: User account created

## Test Scenario: Payment Processing
Test payment functionality

### Task: Process Credit Card Payment
1. Add items to cart
2. Proceed to checkout
3. Enter payment details
4. Complete purchase
Expected Result: Payment successful, order confirmed
```

Command:
```bash
node lark-agent.cjs regression-test.md \
  --owner="QA Lead" \
  --target-date="2025-12-15" \
  --priority=high
```

## Troubleshooting

### Common Issues

**Issue**: "File not found"
- **Solution**: Check file path is correct and file exists

**Issue**: "Invalid markdown structure"
- **Solution**: Verify heading hierarchy (H1 > H2 > H3)

**Issue**: "Missing expected result"
- **Solution**: Ensure each task has "Expected Result:" line

**Issue**: "Lark task creation failed"
- **Solution**: Verify Lark MCP server is running and accessible

### Getting Help

For more help:
1. Check the main SKILL.md documentation
2. Review the JSON schema in `references/json-schema.md`
3. Examine template files in `assets/templates/`

