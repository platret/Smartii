# JSON Schema Documentation

Complete specification of the JSON structure used by Lark Agent.

## Overview

The JSON structure represents a hierarchical test plan with three levels:
1. **Test Overview** - Top-level test information
2. **Scenarios** - Test scenarios or feature areas
3. **Tasks** - Individual test tasks/steps

## Root Structure

```json
{
  "testOverview": { ... },
  "scenarios": [ ... ],
  "larkActionsCompleted": false,
  "larkActionsCompletedAt": null,
  "larksActions": "pending"
}
```

## Test Overview Object

The `testOverview` object contains metadata about the entire test.

### Schema

```typescript
{
  title: string;              // Test title (required)
  description: string;        // Test description (required)
  owner: string;              // Assigned owner (required)
  targetDate: string;         // Target completion date YYYY-MM-DD (required)
  startDate: string;          // Start date YYYY-MM-DD (required)
  status: string;             // Status: "pending" | "in_progress" | "completed"
  larkTaskListId: string | null;  // Lark task list ID (populated after creation)
  parentTaskId: string | null;    // Lark parent task ID (populated after creation)
  priority: string;           // Priority: "low" | "medium" | "high"
}
```

### Example

```json
{
  "testOverview": {
    "title": "User Authentication Test",
    "description": "Comprehensive test of user authentication flows",
    "owner": "QA Team",
    "targetDate": "2025-11-02",
    "startDate": "2025-10-19",
    "status": "pending",
    "larkTaskListId": null,
    "parentTaskId": null,
    "priority": "high"
  }
}
```

### Field Descriptions

- **title**: Main title of the test (from H1 heading in markdown)
- **description**: Brief description of what the test covers
- **owner**: Person or team responsible for the test
- **targetDate**: When the test should be completed (ISO date format)
- **startDate**: When the test begins (ISO date format)
- **status**: Current status of the test
- **larkTaskListId**: ID of the Lark task list (null until created)
- **parentTaskId**: ID of the parent Lark task (null until created)
- **priority**: Importance level of the test

## Scenarios Array

The `scenarios` array contains test scenarios, each representing a major test area.

### Schema

```typescript
{
  scenarioId: string;         // Unique identifier (auto-generated)
  title: string;              // Scenario title (required)
  description: string;        // Scenario description (required)
  expectedOutcome: string;    // Expected outcome of scenario
  owner: string;              // Assigned owner (required)
  status: string;             // Status: "pending" | "in_progress" | "completed"
  tasks: Task[];              // Array of tasks (required)
  lark_task_id: string | null; // Lark task ID (populated after creation)
}
```

### Example

```json
{
  "scenarios": [
    {
      "scenarioId": "scenario-0-1729338000000",
      "title": "Test Scenario: Successful Login",
      "description": "Verify users can log in with valid credentials",
      "expectedOutcome": "User successfully authenticated and redirected",
      "owner": "QA Team",
      "status": "pending",
      "tasks": [ ... ],
      "lark_task_id": null
    }
  ]
}
```

### Field Descriptions

- **scenarioId**: Unique identifier in format `scenario-{index}-{timestamp}`
- **title**: Scenario name (from H2 heading in markdown)
- **description**: What this scenario tests
- **expectedOutcome**: Overall expected result for the scenario
- **owner**: Person or team responsible for this scenario
- **status**: Current status of the scenario
- **tasks**: Array of individual test tasks
- **lark_task_id**: ID of the Lark task (null until created)

## Tasks Array

Each scenario contains a `tasks` array with individual test tasks.

### Schema

```typescript
{
  taskId: string;             // Unique identifier (auto-generated)
  title: string;              // Task title (required)
  description: string;        // Task steps/description (required)
  expectedResult: string;     // Expected result (required)
  status: string;             // Status: "pending" | "in_progress" | "completed"
  notes: string;              // Additional notes
  lark_task_id: string | null; // Lark task ID (populated after creation)
}
```

### Example

```json
{
  "tasks": [
    {
      "taskId": "task-0-0-1729338000000",
      "title": "Task: Login with Valid Credentials",
      "description": "Navigate to login page, Enter username and password, Click Sign In button",
      "expectedResult": "User should be redirected to dashboard",
      "status": "pending",
      "notes": "",
      "lark_task_id": null
    }
  ]
}
```

### Field Descriptions

- **taskId**: Unique identifier in format `task-{scenarioIndex}-{taskIndex}-{timestamp}`
- **title**: Task name (from H3 heading in markdown)
- **description**: Detailed steps to perform (from numbered list in markdown)
- **expectedResult**: What should happen (from "Expected Result:" line)
- **status**: Current status of the task
- **notes**: Additional notes or observations
- **lark_task_id**: ID of the Lark task (null until created)

## Lark Metadata Fields

These fields track the Lark task creation process.

### Schema

```typescript
{
  larkActionsCompleted: boolean;      // Whether Lark tasks have been created
  larkActionsCompletedAt: string | null; // ISO timestamp of completion
  larksActions: string;               // Status: "pending" | "in_progress" | "completed"
}
```

### Example

```json
{
  "larkActionsCompleted": true,
  "larkActionsCompletedAt": "2025-10-19T10:15:59.627Z",
  "larksActions": "completed"
}
```

## Complete Example

Here's a complete JSON file with all components:

```json
{
  "testOverview": {
    "title": "Shopping Cart Feature Test",
    "description": "Test shopping cart functionality including add, remove, and checkout",
    "owner": "QA Team",
    "targetDate": "2025-11-15",
    "startDate": "2025-10-20",
    "status": "pending",
    "larkTaskListId": null,
    "parentTaskId": null,
    "priority": "medium"
  },
  "scenarios": [
    {
      "scenarioId": "scenario-0-1729338000000",
      "title": "Test Scenario: Add Items to Cart",
      "description": "Verify users can add products to shopping cart",
      "expectedOutcome": "Products successfully added to cart",
      "owner": "QA Team",
      "status": "pending",
      "tasks": [
        {
          "taskId": "task-0-0-1729338000000",
          "title": "Task: Add Single Item",
          "description": "Browse to product page, Click Add to Cart button, Verify cart icon updates",
          "expectedResult": "Cart shows 1 item",
          "status": "pending",
          "notes": "",
          "lark_task_id": null
        },
        {
          "taskId": "task-0-1-1729338000000",
          "title": "Task: Add Multiple Items",
          "description": "Add first product, Add second product, Check cart contents",
          "expectedResult": "Cart shows 2 items",
          "status": "pending",
          "notes": "",
          "lark_task_id": null
        }
      ],
      "lark_task_id": null
    },
    {
      "scenarioId": "scenario-1-1729338000000",
      "title": "Test Scenario: Remove Items from Cart",
      "description": "Verify users can remove products from cart",
      "expectedOutcome": "Products successfully removed from cart",
      "owner": "QA Team",
      "status": "pending",
      "tasks": [
        {
          "taskId": "task-1-0-1729338000000",
          "title": "Task: Remove Single Item",
          "description": "Open cart, Click remove button, Verify item removed",
          "expectedResult": "Item removed from cart",
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

## ID Generation

### Scenario IDs

Format: `scenario-{index}-{timestamp}`

- **index**: Zero-based index of scenario in the scenarios array
- **timestamp**: Unix timestamp in milliseconds when generated

Example: `scenario-0-1729338000000`

### Task IDs

Format: `task-{scenarioIndex}-{taskIndex}-{timestamp}`

- **scenarioIndex**: Index of parent scenario
- **taskIndex**: Index of task within scenario
- **timestamp**: Unix timestamp in milliseconds when generated

Example: `task-0-0-1729338000000` (first task of first scenario)

## Status Values

All status fields use these values:

- **pending**: Not started
- **in_progress**: Currently being worked on
- **completed**: Finished
- **blocked**: Cannot proceed
- **skipped**: Intentionally skipped

## Priority Values

Priority fields use these values:

- **low**: Low priority
- **medium**: Medium priority (default)
- **high**: High priority
- **critical**: Critical priority

## Date Format

All date fields use ISO 8601 format:

- **Date only**: `YYYY-MM-DD` (e.g., "2025-10-19")
- **Date and time**: `YYYY-MM-DDTHH:mm:ss.sssZ` (e.g., "2025-10-19T10:15:59.627Z")

## Validation Rules

### Required Fields

**testOverview**:
- title (non-empty string)
- description (non-empty string)
- owner (non-empty string)
- targetDate (valid ISO date)
- startDate (valid ISO date)

**scenarios**:
- scenarioId (unique string)
- title (non-empty string)
- description (non-empty string)
- owner (non-empty string)
- tasks (non-empty array)

**tasks**:
- taskId (unique string)
- title (non-empty string)
- description (non-empty string)
- expectedResult (non-empty string)

### Constraints

- targetDate must be >= startDate
- scenarioId must be unique within scenarios array
- taskId must be unique across all tasks
- status must be one of the valid status values
- priority must be one of the valid priority values

## Usage in Lark Agent

1. **Markdown Parsing**: Generates this JSON structure from markdown
2. **Task Creation**: Reads this JSON to create Lark tasks
3. **ID Population**: Updates lark_task_id fields after creation
4. **Status Tracking**: Updates status fields as work progresses

