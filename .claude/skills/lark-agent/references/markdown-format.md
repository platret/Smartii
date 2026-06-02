# Markdown Format Specification

This document defines the required markdown format for test files processed by Lark Agent.

## Overview

The markdown format uses a hierarchical heading structure to organize test information:

- **H1 (#)**: Test title and overview
- **H2 (##)**: Test scenarios
- **H3 (###)**: Individual test tasks

## Required Structure

### Level 1: Test Title (H1)

The first H1 heading defines the overall test title.

**Format:**
```markdown
# Test Title
```

**Description:**
Lines immediately following the H1 (before the next heading) are treated as the test description.

**Example:**
```markdown
# User Authentication Test
This test verifies that the user authentication system works correctly
across different scenarios including login, logout, and session management.
```

### Level 2: Test Scenarios (H2)

H2 headings define test scenarios. Each scenario should start with "Test Scenario:" for clarity.

**Format:**
```markdown
## Test Scenario: Scenario Name
```

**Description:**
Lines following the H2 (before the next heading or task) describe what the scenario tests.

**Example:**
```markdown
## Test Scenario: Successful Login
This scenario verifies that users can successfully log in with valid credentials
and are redirected to the appropriate dashboard.
```

### Level 3: Test Tasks (H3)

H3 headings define individual test tasks. Each task should start with "Task:" for clarity.

**Format:**
```markdown
### Task: Task Name
1. Step one
2. Step two
3. Step three
Expected Result: What should happen
```

**Required Components:**
1. **Title**: Clear task name after "Task:"
2. **Steps**: Numbered list of actions to perform
3. **Expected Result**: Line starting with "Expected Result:" describing the expected outcome

**Example:**
```markdown
### Task: Login with Valid Credentials
1. Navigate to the login page
2. Enter valid username and password
3. Click the "Sign In" button
Expected Result: User should be redirected to the dashboard and see their profile name
```

## Complete Example

Here's a complete example showing all levels:

```markdown
# User Registration and Login Test

Comprehensive test of user registration and authentication flows.

## Test Scenario: New User Registration

Test that new users can successfully register for an account.

### Task: Register with Valid Information
1. Navigate to registration page
2. Fill in all required fields with valid data
3. Accept terms and conditions
4. Click "Create Account" button
Expected Result: Account created successfully, confirmation email sent

### Task: Verify Email Confirmation
1. Check email inbox for confirmation email
2. Click confirmation link in email
3. Verify redirect to login page
Expected Result: Email confirmed, user can now log in

## Test Scenario: Existing User Login

Test that existing users can log in with their credentials.

### Task: Login with Email and Password
1. Navigate to login page
2. Enter registered email address
3. Enter correct password
4. Click "Sign In" button
Expected Result: User logged in and redirected to dashboard

### Task: Verify Session Persistence
1. After logging in, close the browser
2. Reopen the browser and navigate to the site
3. Check if user is still logged in
Expected Result: User session persists, user remains logged in
```

## Parsing Rules

### Heading Hierarchy

The parser expects strict heading hierarchy:
- Only one H1 per file (test title)
- Multiple H2 headings (scenarios)
- Multiple H3 headings under each H2 (tasks)

### Text Extraction

**Test Description:**
- All non-heading text between H1 and first H2
- Trimmed and joined into single string

**Scenario Description:**
- All non-heading text between H2 and first H3
- Trimmed and joined into single string

**Task Steps:**
- All numbered list items (1., 2., 3., etc.)
- Extracted and joined with commas

**Expected Result:**
- Line starting with "Expected Result:"
- Text after the colon is extracted

### Special Formatting

**Numbered Lists:**
```markdown
1. First step
2. Second step
3. Third step
```

**Expected Result:**
```markdown
Expected Result: Description of expected outcome
```

**Optional Notes:**
You can include additional notes or context that won't be parsed:
```markdown
> Note: This test requires admin privileges
```

## Validation

The parser validates:

1. **H1 exists**: File must have at least one H1 heading
2. **H2 exists**: File must have at least one H2 heading (scenario)
3. **H3 exists**: Each scenario must have at least one H3 heading (task)
4. **Expected Result**: Each task must have an "Expected Result:" line

## Common Mistakes

### ❌ Missing Expected Result

```markdown
### Task: Login
1. Enter credentials
2. Click login
```

**Fix:** Add Expected Result line
```markdown
### Task: Login
1. Enter credentials
2. Click login
Expected Result: User should be logged in
```

### ❌ Wrong Heading Level

```markdown
# Test Title
### Task: Direct Task (skipped H2)
```

**Fix:** Include H2 scenario
```markdown
# Test Title
## Test Scenario: Main Scenario
### Task: Proper Task
```

### ❌ No Numbered Steps

```markdown
### Task: Login
Enter credentials and click login
Expected Result: Logged in
```

**Fix:** Use numbered list
```markdown
### Task: Login
1. Enter credentials
2. Click login button
Expected Result: User logged in successfully
```

## Best Practices

### Clear Task Titles

✅ Good:
```markdown
### Task: Verify Password Reset Email Delivery
```

❌ Bad:
```markdown
### Task: Test
```

### Detailed Steps

✅ Good:
```markdown
1. Navigate to login page at /login
2. Enter email: test@example.com
3. Enter password: Test123!
4. Click the blue "Sign In" button
```

❌ Bad:
```markdown
1. Login
```

### Specific Expected Results

✅ Good:
```markdown
Expected Result: User should be redirected to /dashboard, see welcome message "Hello, Test User", and have access to all dashboard features
```

❌ Bad:
```markdown
Expected Result: It works
```

### Scenario Organization

Group related tasks under appropriate scenarios:

```markdown
## Test Scenario: User Authentication
### Task: Login with Email
### Task: Login with Username
### Task: Logout

## Test Scenario: Password Management
### Task: Reset Password
### Task: Change Password
```

## File Naming

Recommended file naming convention:

- Use descriptive names: `user-authentication-test.md`
- Include feature area: `checkout-payment-flow-test.md`
- Use hyphens, not spaces: `shopping-cart-test.md`
- Add version if needed: `onboarding-test-v2.md`

## Encoding

- Use UTF-8 encoding
- Avoid special characters in headings
- Emoji are supported: 🔐 Login Test

## Line Endings

- Unix (LF) or Windows (CRLF) line endings are both supported
- Parser normalizes line endings automatically

