# Sample User Login Test

This is a comprehensive test plan for the user login functionality.

## Test Scenario: Valid Login Flow

Test that users can successfully log in with valid credentials.

### Task: Navigate to Login Page

1. Open browser
2. Navigate to https://example.com/login
3. Verify login form is displayed

Expected Result: Login page should load successfully with username and password fields visible.

### Task: Enter Valid Credentials

1. Enter valid username: "testuser@example.com"
2. Enter valid password: "SecurePass123"
3. Click "Login" button

Expected Result: User should be authenticated and redirected to dashboard.

### Task: Verify Dashboard Access

1. Wait for dashboard to load
2. Verify user name is displayed in header
3. Verify navigation menu is accessible

Expected Result: Dashboard should display with user's name and all navigation options visible.

## Test Scenario: Invalid Login Attempts

Test that invalid login attempts are properly handled with appropriate error messages.

### Task: Test Empty Credentials

1. Navigate to login page
2. Leave username field empty
3. Leave password field empty
4. Click "Login" button

Expected Result: Error message "Please enter username and password" should be displayed.

### Task: Test Invalid Password

1. Navigate to login page
2. Enter valid username: "testuser@example.com"
3. Enter invalid password: "WrongPassword"
4. Click "Login" button

Expected Result: Error message "Invalid username or password" should be displayed.

### Task: Test Account Lockout

1. Attempt login with wrong password 5 times
2. Verify account lockout message
3. Wait for lockout period to expire

Expected Result: After 5 failed attempts, account should be temporarily locked with message "Account locked. Try again in 15 minutes."

## Test Scenario: Password Recovery

Test the password recovery functionality for users who forgot their password.

### Task: Initiate Password Recovery

1. Navigate to login page
2. Click "Forgot Password?" link
3. Verify password recovery form is displayed

Expected Result: Password recovery form should be displayed with email input field.

### Task: Request Password Reset

1. Enter valid email: "testuser@example.com"
2. Click "Send Reset Link" button
3. Verify confirmation message

Expected Result: Confirmation message "Password reset link sent to your email" should be displayed.

### Task: Verify Reset Email

1. Check email inbox for password reset email
2. Verify email contains reset link
3. Click reset link

Expected Result: Password reset email should be received within 5 minutes with a valid reset link.

### Task: Reset Password

1. Enter new password: "NewSecurePass123"
2. Confirm new password: "NewSecurePass123"
3. Click "Reset Password" button

Expected Result: Password should be successfully reset and user should be able to login with new password.
