# Getting Started with UITestFlow

This guide will walk you through installing UITestFlow, setting up your first profile, and running your first test. By the end, you'll have a working UI testing environment ready for CI/CD integration.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Setting Up Profiles](#setting-up-profiles)
- [Writing Your First Test](#writing-your-first-test)
- [Running Tests](#running-tests)
- [Understanding Test Results](#understanding-test-results)
- [Next Steps](#next-steps)

## Installation

### Prerequisites

- **Python 3.11 or higher** - [Download Python](https://www.python.org/downloads/)
- **pip** (usually included with Python)
- **Git** (optional, for cloning examples)

### Install UITestFlow

#### From PyPI (Recommended - Coming Soon)

```bash
pip install uitestflow
```

#### From Source (Current)

```bash
# Clone the repository
git clone https://github.com/preset-io/ui-test-flow.git
cd ui-test-flow

# Create a virtual environment (recommended)
python -m venv .venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install UITestFlow
pip install -e .
```

### Install Playwright Browsers

UITestFlow uses Playwright for browser automation. After installing UITestFlow, install the browser binaries:

```bash
playwright install chromium
```

For cross-browser testing, you can also install Firefox and WebKit:

```bash
playwright install firefox webkit
```

### Verify Installation

```bash
# Check UITestFlow is installed
uitestflow --version

# Check available commands
uitestflow --help
```

You should see output similar to:

```
UITestFlow v0.1.0
Usage: uitestflow [OPTIONS] COMMAND [ARGS]...

Options:
  --version   Show version
  --help      Show this message and exit

Commands:
  run         Run UI tests
  tui         Start interactive terminal UI
  profiles    Manage test profiles
  config      Manage configuration
  report      Generate test reports
  ...
```

## Quick Start

Let's create and run a simple test to verify everything is working.

### 1. Create a Project Directory

```bash
mkdir my-ui-tests
cd my-ui-tests
```

### 2. Initialize Configuration

```bash
uitestflow config init
```

This creates a `.uitest_profiles.yaml` file in your current directory with a default profile.

### 3. Run the Example Test

Let's test against a simple public website:

Create a file `test_example.yaml`:

```yaml
version: "1.0"
name: "Example.com Test"

steps:
  - name: "Navigate to example.com"
    action: "goto"
    url: "https://example.com"

  - name: "Verify page title"
    action: "expect"
    assertion: "title_contains"
    value: "Example Domain"

evaluators:
  - name: "all_steps_completed"
    type: "execution_successful"
```

Run the test:

```bash
uitestflow run test_example.yaml
```

You should see output like:

```
╭─── Test Execution ───╮
│ Browser: chromium    │
│ Headless: true       │
╰──────────────────────╯

Running: Example.com Test

  ✓ Navigate to example.com (1.5s)
  ✓ Verify page title (0.2s)

╭─── Evaluators ───╮
│ ✓ all_steps_completed │
╰────────────────────────╯

Result: PASSED ✓
Duration: 1.7s
```

Congratulations! You've run your first UITestFlow test.

## Setting Up Profiles

Profiles let you manage different environments (local, staging, production) with different configurations.

### Understanding Profiles

A profile contains:

- **Base URL**: The root URL of your application
- **Authentication**: Credentials and auth method
- **Browser settings**: Headless mode, viewport size, device emulation
- **Notifications**: Where to send alerts on failures

### Profile Configuration File

Edit `.uitest_profiles.yaml` (or create it if it doesn't exist):

```yaml
# Default profile to use when none is specified
default: local

profiles:
  # Local development environment
  local:
    name: "Local Development"
    base_url: "http://localhost:8080"
    auth:
      type: "form"
      username: "admin"
      password: "admin"
    browser:
      headless: false      # Show browser window
      slowmo: 100          # Slow down actions by 100ms

  # Staging environment
  staging:
    name: "Staging Environment"
    base_url: "https://staging.myapp.com"
    auth:
      type: "form"
      username: "${STAGING_USERNAME}"  # From environment variable
      password: "${STAGING_PASSWORD}"
    browser:
      headless: true       # Run in background
      viewport:
        width: 1920
        height: 1080

  # Production environment (read-only tests only!)
  production:
    name: "Production Environment"
    base_url: "https://app.myapp.com"
    auth:
      type: "oauth"
      provider: "okta"
      client_id: "${OKTA_CLIENT_ID}"
      client_secret: "${OKTA_CLIENT_SECRET}"
    browser:
      headless: true
    notifications:
      on_failure:
        - slack: "#production-alerts"
        - email: "oncall@mycompany.com"
```

### Using Environment Variables

Store sensitive credentials in environment variables:

Create a `.env` file (add to `.gitignore`!):

```bash
# Local credentials
LOCAL_USERNAME=admin
LOCAL_PASSWORD=admin

# Staging credentials
STAGING_USERNAME=test_user
STAGING_PASSWORD=test_password

# Production OAuth
OKTA_CLIENT_ID=abc123...
OKTA_CLIENT_SECRET=xyz789...
```

Reference them in your profile with `${VARIABLE_NAME}` syntax.

### Testing Profile Connectivity

Before running tests, verify your profile configuration:

```bash
# Test the staging profile
uitestflow profiles test staging

# List all available profiles
uitestflow profiles list
```

## Writing Your First Test

Let's create a realistic test for a web application with authentication.

### Test Structure

Create `tests/login_test.yaml`:

```yaml
version: "1.0"
name: "User Login Test"
description: "Verify users can login with valid credentials"

# Steps are executed in order
steps:
  # Step 1: Navigate to login page
  - name: "Navigate to login page"
    action: "goto"
    url: "{{ base_url }}/login/"  # Uses base_url from profile
    screenshot: true               # Capture screenshot after this step

  # Step 2: Wait for page to be ready
  - name: "Wait for login form"
    action: "wait_for"
    selector: 'form[name="login"]'
    timeout: 5000  # milliseconds

  # Step 3: Fill username field
  - name: "Enter username"
    action: "fill"
    selector: 'input[name="username"]'
    value: "{{ auth.username }}"  # Uses username from profile

  # Step 4: Fill password field
  - name: "Enter password"
    action: "fill"
    selector: 'input[name="password"]'
    value: "{{ auth.password }}"  # Uses password from profile

  # Step 5: Submit form
  - name: "Click login button"
    action: "click"
    selector: 'button[type="submit"]'

  # Step 6: Verify successful login
  - name: "Wait for dashboard"
    action: "wait_for"
    selector: '.dashboard-content'
    timeout: 10000
    screenshot: true

# Evaluators determine pass/fail
evaluators:
  # All steps must complete
  - name: "all_steps_completed"
    type: "execution_successful"

  # No JavaScript errors
  - name: "no_console_errors"
    type: "console_errors"
    max_errors: 0

  # Performance check
  - name: "login_performance"
    type: "performance"
    max_load_time: 5000

# Optional: Retry on failure
retry:
  max_attempts: 2
  delay: 1000

# Tags for organization
tags:
  - "authentication"
  - "critical"
  - "smoke-test"
```

### Available Actions

UITestFlow supports many Playwright actions:

| Action | Description | Example |
|--------|-------------|---------|
| `goto` | Navigate to URL | `action: "goto"`, `url: "https://..."` |
| `click` | Click element | `action: "click"`, `selector: "button"` |
| `fill` | Fill input field | `action: "fill"`, `selector: "input"`, `value: "text"` |
| `type` | Type text slowly | `action: "type"`, `selector: "input"`, `value: "text"` |
| `select` | Select dropdown option | `action: "select"`, `selector: "select"`, `value: "option"` |
| `wait_for` | Wait for element | `action: "wait_for"`, `selector: ".element"` |
| `wait_for_network_idle` | Wait for network | `action: "wait_for_network_idle"` |
| `screenshot` | Capture screenshot | `action: "screenshot"`, `name: "my_screenshot"` |
| `expect` | Assertion | `action: "expect"`, `assertion: "title_contains"` |

### Template Variables

Use template variables to make tests reusable:

- `{{ base_url }}` - Base URL from profile
- `{{ auth.username }}` - Username from profile
- `{{ auth.password }}` - Password from profile
- `{{ env.VARIABLE }}` - Environment variable

### Common Selectors

UITestFlow uses CSS selectors (and can use XPath):

```yaml
# By element name
selector: 'input[name="username"]'

# By ID
selector: '#login-button'

# By class
selector: '.submit-btn'

# By text content
selector: 'button:has-text("Login")'

# By data attribute
selector: '[data-test="submit"]'

# Combine selectors
selector: 'form.login input[type="text"]'
```

## Running Tests

### Basic Execution

```bash
# Run a single test with default profile
uitestflow run tests/login_test.yaml

# Run with specific profile
uitestflow run tests/login_test.yaml --profile staging

# Run all tests in a directory
uitestflow run tests/

# Run tests matching pattern
uitestflow run tests/ --pattern "login_*"
```

### Execution Options

```bash
# Run in headed mode (show browser window)
uitestflow run tests/login_test.yaml --no-headless

# Run with specific browser
uitestflow run tests/login_test.yaml --browser firefox

# Run with custom timeout
uitestflow run tests/login_test.yaml --timeout 30000

# Generate HTML report
uitestflow run tests/login_test.yaml --report-format html --output report.html

# Export for CI (JUnit XML)
uitestflow run tests/login_test.yaml --format junit --output results.xml
```

### Watch Mode

Run tests automatically when files change:

```bash
uitestflow watch tests/
```

### Interactive TUI

For local development, use the Terminal UI:

```bash
uitestflow tui
```

This launches an interactive interface where you can:

- Browse and select tests
- View real-time execution
- Inspect screenshots
- Review test history
- Manage profiles

## Understanding Test Results

### Console Output

When a test passes:

```
╭─── Test Execution ───╮
│ Profile: local       │
│ Browser: chromium    │
╰──────────────────────╯

Running: User Login Test

  ✓ Navigate to login page (1.2s)
    📸 Screenshot: login_page.png
  ✓ Wait for login form (0.1s)
  ✓ Enter username (0.2s)
  ✓ Enter password (0.2s)
  ✓ Click login button (0.3s)
  ✓ Wait for dashboard (1.5s)
    📸 Screenshot: dashboard.png

╭─── Evaluators ───╮
│ ✓ all_steps_completed │
│ ✓ no_console_errors   │
│ ✓ login_performance   │
╰────────────────────────╯

Result: PASSED ✓
Duration: 3.5s
Screenshots: 2
```

When a test fails:

```
Running: User Login Test

  ✓ Navigate to login page (1.2s)
  ✓ Wait for login form (0.1s)
  ✓ Enter username (0.2s)
  ✓ Enter password (0.2s)
  ✗ Click login button (30.0s)
    Error: Timeout waiting for selector 'button[type="submit"]'
    📸 Screenshot: error_screenshot.png

╭─── Evaluators ───╮
│ ✗ all_steps_completed │
│   Step 5 failed: Timeout
╰────────────────────────╯

Result: FAILED ✗
Duration: 31.7s
Error Screenshot: error_screenshot.png
```

### Exit Codes

UITestFlow uses standard exit codes for CI/CD integration:

- `0` - All tests passed
- `1` - One or more tests failed
- `2` - Test execution error (invalid config, etc.)

### Artifacts

Tests generate artifacts in the `.uitestflow/` directory:

```
.uitestflow/
├── runs/
│   └── 2024-01-15_14-30-45_abc123/
│       ├── screenshots/
│       │   ├── login_page.png
│       │   └── dashboard.png
│       ├── video.webm
│       ├── trace.zip
│       ├── logs.json
│       └── report.html
```

View artifacts:

```bash
# List recent test runs
uitestflow runs list

# View run details
uitestflow runs show abc123

# Open HTML report in browser
uitestflow report abc123 --open
```

## Next Steps

Now that you're familiar with the basics, explore:

### Advanced Topics

- **[Writing Tests Guide](guides/writing-tests.md)** - In-depth test authoring
- **[YAML Reference](guides/yaml-reference.md)** - Complete YAML schema
- **[Evaluators Guide](guides/evaluators.md)** - All built-in evaluators
- **[Natural Language Tests](guides/natural-language-tests.md)** - LLM-powered tests
- **[CI/CD Integration](guides/ci-cd-integration.md)** - GitHub Actions, GitLab CI, Jenkins

### Examples

Browse complete examples:

- **[Login Tests](../examples/basic/login_test.yaml)** - Authentication flows
- **[Dashboard Tests](../examples/basic/dashboard_filters.yaml)** - Superset dashboard testing
- **[Form Validation](../examples/forms/)** - Complex form interactions
- **[E2E Flows](../examples/e2e/)** - Multi-page user journeys

### Best Practices

1. **Use Profiles**: Separate configs for each environment
2. **Tag Your Tests**: Organize by feature, priority, type
3. **Meaningful Names**: Use descriptive step and test names
4. **Smart Selectors**: Prefer `data-test` attributes over classes
5. **Add Screenshots**: Capture at key points for debugging
6. **Reasonable Timeouts**: Don't make them too short or too long
7. **Retry Logic**: Add retries for flaky network-dependent tests
8. **Version Control**: Store tests in Git alongside application code

### Getting Help

- **Documentation**: [docs.uitestflow.io](https://docs.uitestflow.io) (coming soon)
- **Examples**: Browse the [`examples/`](../examples/) directory
- **Issues**: [GitHub Issues](https://github.com/preset-io/ui-test-flow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/preset-io/ui-test-flow/discussions)

Happy testing!
