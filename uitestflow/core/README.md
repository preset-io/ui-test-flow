# UITestFlow Core Module

This module contains the core configuration, data models, and shared components for UITestFlow.

## Overview

The core module provides:

1. **Configuration Management** - Hierarchical configuration loading from multiple sources
2. **Profile Management** - Environment-specific test profiles with authentication and browser settings
3. **Data Models** - Type-safe Pydantic models for tests, runs, and results
4. **Exception Handling** - Custom exception hierarchy for clear error reporting

## Components

### 1. Configuration (`config.py`)

The configuration system loads settings from multiple sources with clear priority:

**Priority Order (highest to lowest):**

1. Command-line options (CLI overrides)
2. Profile from `.uitest_profiles.yaml`
3. `.env` file in current directory
4. `~/.uitestflow` (user config file)
5. Environment variables
6. Built-in defaults

**Usage:**

```python
from uitestflow.core import Config, init_config, get_config

# Initialize with profile and overrides
config = init_config(profile="staging", headless=False)

# Access configuration
print(config.base_url)
print(config.profile_id)
print(config.settings.anthropic_api_key)

# Get config source tracking
sources = config.get_all_with_sources()
for key, (value, source) in sources.items():
    print(f"{key}: {value} (from {source})")

# Validate configuration
errors = config.validate()
if errors:
    print(f"Configuration errors: {errors}")
```

**Environment Variables:**

```bash
# API Keys
export UITESTFLOW_ANTHROPIC_API_KEY="your-key"
export UITESTFLOW_OPENAI_API_KEY="your-key"

# Storage
export UITESTFLOW_STORAGE_BACKEND="s3"
export UITESTFLOW_S3_BUCKET="my-bucket"
export UITESTFLOW_S3_REGION="us-west-2"

# Server
export UITESTFLOW_SERVER_HOST="0.0.0.0"
export UITESTFLOW_SERVER_PORT="8080"

# Database
export UITESTFLOW_DATABASE_URL="postgresql://user:pass@localhost/uitestflow"
export UITESTFLOW_REDIS_URL="redis://localhost:6379/0"
```

### 2. Profiles (`profiles.py`)

Profiles define environment-specific configurations including URLs, authentication, browser settings, and notifications.

**Profile File Format** (`.uitest_profiles.yaml`):

```yaml
default: local

global:
  timeout: 30000
  rate_limit:
    requests_per_minute: 60

profiles:
  local:
    name: "Local Development"
    description: "Local development environment"
    base_url: "http://localhost:8080"

    auth:
      type: "form"
      username: "${LOCAL_USERNAME:-admin}"
      password: "${LOCAL_PASSWORD:-admin}"

    browser:
      type: "chromium"
      headless: false
      slowmo: 500
      viewport:
        width: 1920
        height: 1080

  staging:
    name: "Staging Environment"
    base_url: "https://staging.example.com"

    auth:
      type: "bearer"
      token: "${STAGING_API_TOKEN}"

    browser:
      type: "chromium"
      headless: true

    notifications:
      on_failure:
        - slack: "#test-alerts"
```

**Usage:**

```python
from uitestflow.core import (
    ProfileManager,
    load_profile,
    list_available_profiles
)

# List profiles
profiles = list_available_profiles()
print(f"Available profiles: {profiles}")

# Load a profile
profile = load_profile("staging")
print(f"Base URL: {profile.base_url}")
print(f"Auth type: {profile.auth.auth_type}")
print(f"Browser: {profile.browser.browser_type}")

# Use ProfileManager for advanced operations
manager = ProfileManager()
errors = manager.validate_profile("staging")
if errors:
    print(f"Validation errors: {errors}")
```

**Environment Variable Substitution:**

Profiles support environment variable substitution with defaults:

```yaml
base_url: "${BASE_URL:-http://localhost:8080}"
auth:
  username: "${USERNAME}"
  password: "${PASSWORD:-default-password}"
```

Syntax:

- `${VAR_NAME}` - Required variable (empty string if not set)
- `${VAR_NAME:-default}` - Variable with default value

### 3. Data Models (`models.py`)

Type-safe Pydantic models for all UITestFlow entities.

**Test Definition:**

```python
from uitestflow.core import (
    TestDefinition,
    TestStep,
    ActionType,
    EvaluatorConfig,
    EvaluatorType,
    BrowserConfig,
    AuthConfig
)

# Create a test definition
test = TestDefinition(
    name="Login Test",
    description="Test user login flow",
    url="http://localhost:8080",
    steps=[
        TestStep(
            name="Navigate to login",
            action=ActionType.GOTO,
            url="http://localhost:8080/login"
        ),
        TestStep(
            name="Enter username",
            action=ActionType.FILL,
            selector='input[name="username"]',
            value="admin"
        ),
        TestStep(
            name="Enter password",
            action=ActionType.FILL,
            selector='input[name="password"]',
            value="admin"
        ),
        TestStep(
            name="Submit",
            action=ActionType.CLICK,
            selector='button[type="submit"]'
        )
    ],
    evaluators=[
        EvaluatorConfig(
            name="all_steps_completed",
            evaluator_type=EvaluatorType.ALL_STEPS_COMPLETED
        ),
        EvaluatorConfig(
            name="no_console_errors",
            evaluator_type=EvaluatorType.NO_CONSOLE_ERRORS
        )
    ],
    tags=["login", "smoke-test"]
)

# Serialize to JSON
test_json = test.model_dump_json(indent=2)

# Deserialize from JSON
test = TestDefinition.model_validate_json(test_json)
```

**Test Run and Results:**

```python
from datetime import datetime
from uitestflow.core import (
    TestRun,
    TestStatus,
    TestResult,
    EvalResult
)

# Create a test run
run = TestRun(
    test_id=test.id,
    test_name=test.name,
    profile="local",
    triggered_by="manual"
)

# Mark as started
run.mark_started()

# Execute test (implementation in execution engine)
# ... test execution logic ...

# Create results
result = TestResult(
    passed=True,
    score=1.0,
    steps_executed=4,
    steps_passed=4,
    steps_failed=0,
    evaluator_results=[
        EvalResult(
            evaluator_name="all_steps_completed",
            passed=True,
            score=1.0,
            reason="All steps completed successfully"
        ),
        EvalResult(
            evaluator_name="no_console_errors",
            passed=True,
            score=1.0,
            reason="No console errors detected"
        )
    ],
    total_duration_ms=5000
)

# Mark as completed
run.mark_completed(result)

print(f"Test completed: {run.status}")
print(f"Duration: {run.duration_ms}ms")
print(f"Result: {'PASSED' if result.passed else 'FAILED'}")
```

**Available Enums:**

```python
from uitestflow.core import (
    TestStatus,      # PENDING, RUNNING, COMPLETED, FAILED, ABORTED
    ActionType,      # GOTO, CLICK, FILL, WAIT_FOR, etc.
    AuthType,        # NONE, FORM, BASIC, BEARER, JWT, OAUTH, CUSTOM
    BrowserType,     # CHROMIUM, FIREFOX, WEBKIT
    EvaluatorType,   # ALL_STEPS_COMPLETED, NO_CONSOLE_ERRORS, etc.
    ScreenshotStrategy  # ALWAYS, ON_ERROR, KEY_POINTS, NEVER
)
```

### 4. Exceptions (`exceptions.py`)

Custom exception hierarchy for clear error handling.

**Exception Hierarchy:**

```
UITestFlowError (base)
├── ConfigurationError
│   ├── ProfileNotFoundError
│   └── ProfileValidationError
├── TestDefinitionError
│   ├── TestParseError
│   └── TestValidationError
├── TestExecutionError
├── BrowserError
│   ├── BrowserLaunchError
│   └── BrowserTimeoutError
├── AuthenticationError
├── EvaluatorError
├── StorageError
└── NotificationError
```

**Usage:**

```python
from uitestflow.core import (
    ProfileNotFoundError,
    TestExecutionError,
    BrowserTimeoutError
)

try:
    profile = load_profile("nonexistent")
except ProfileNotFoundError as e:
    print(f"Error: {e.message}")
    print(f"Available profiles: {e.available_profiles}")

try:
    # Execute test step with timeout
    pass
except BrowserTimeoutError as e:
    print(f"Operation timed out: {e.operation}")
    print(f"Timeout: {e.timeout_ms}ms")
    print(f"Selector: {e.selector}")
```

All exceptions include:

- `message`: Human-readable error message
- `details`: Dictionary with additional context
- Specific attributes for typed error handling

## Configuration Files

### `.uitest_profiles.yaml`

Main configuration file for test profiles. Place this file in:

- Current directory (preferred for project-specific profiles)
- Parent directories (searched up to 5 levels)

See `examples/.uitest_profiles.yaml` for a complete example.

### `.env`

Environment-specific variables. Example:

```bash
# API Keys
UITESTFLOW_ANTHROPIC_API_KEY=your-key-here
UITESTFLOW_OPENAI_API_KEY=your-key-here

# Storage
UITESTFLOW_STORAGE_BACKEND=s3
UITESTFLOW_S3_BUCKET=my-test-artifacts
UITESTFLOW_S3_REGION=us-west-2

# Database
UITESTFLOW_DATABASE_URL=postgresql://user:pass@localhost/uitestflow
```

### `~/.uitestflow`

User-level configuration file (same format as `.env`):

```bash
# Personal defaults
UITESTFLOW_DEFAULT_PROFILE=local
UITESTFLOW_DEFAULT_BROWSER=chromium
UITESTFLOW_DEFAULT_HEADLESS=true

# API keys (don't commit to git!)
UITESTFLOW_ANTHROPIC_API_KEY=your-personal-key
```

## Design Patterns

### 1. Configuration Hierarchy

Configuration is loaded in a clear priority order, with each level able to override the previous:

```
CLI args (highest)
  ↓
Profile settings
  ↓
.env file
  ↓
~/.uitestflow
  ↓
Environment variables
  ↓
Built-in defaults (lowest)
```

### 2. Global Singletons

Configuration and profile managers use global singleton patterns with explicit initialization:

```python
# Initialize once
config = init_config(profile="staging")

# Access anywhere
from uitestflow.core import get_config
config = get_config()

# Reload if needed
from uitestflow.core import reload_config
config = reload_config()
```

### 3. Pydantic Validation

All data models use Pydantic for:

- Type validation
- Serialization/deserialization
- Documentation
- IDE autocomplete

```python
# Type hints everywhere
def process_test(test: TestDefinition) -> TestResult:
    # IDE knows all attributes and types
    for step in test.steps:
        # step.action is ActionType enum
        # step.selector is str | None
        pass
```

### 4. Exception Context

Exceptions include structured context for better error handling:

```python
try:
    profile = load_profile("staging")
except ProfileNotFoundError as e:
    # Access structured data
    print(f"Missing profile: {e.profile_id}")
    print(f"Available: {e.available_profiles}")
    print(f"Details: {e.details}")
```

## Best Practices

### 1. Use Profiles for Environments

Create separate profiles for each environment:

```yaml
profiles:
  local:    # Local development
  ci:       # CI/CD pipelines
  staging:  # Pre-production testing
  production:  # Production smoke tests
```

### 2. Never Commit Secrets

Use environment variable substitution in profiles:

```yaml
auth:
  token: "${API_TOKEN}"  # Set via environment
```

Store actual values in:

- `.env` (add to `.gitignore`)
- `~/.uitestflow` (user-specific)
- CI/CD secret management

### 3. Validate Early

Validate configuration before running tests:

```python
config = init_config(profile="staging")
errors = config.validate()
if errors:
    raise ConfigurationError(f"Invalid config: {errors}")
```

### 4. Use Type Hints

Leverage Pydantic models for type safety:

```python
def create_test(
    name: str,
    steps: list[TestStep],
    evaluators: list[EvaluatorConfig]
) -> TestDefinition:
    return TestDefinition(
        name=name,
        steps=steps,
        evaluators=evaluators
    )
```

### 5. Track Configuration Sources

Use source tracking for debugging:

```python
config = get_config()
sources = config.get_all_with_sources()

# Debug where each value came from
for key, (value, source) in sources.items():
    print(f"{key}: {source}")
```

## Examples

See `examples/test_config_system.py` for complete working examples of:

- Profile loading and validation
- Configuration hierarchy
- Test definition creation
- Using profiles with tests

Run the example:

```bash
cd examples
python test_config_system.py
```

## Testing

Unit tests for the core module are in `tests/core/`:

```bash
pytest tests/core/
```

## Contributing

When adding new configuration options:

1. Add to `UITestFlowSettings` in `config.py`
2. Update environment variable documentation
3. Add example to `.uitest_profiles.yaml`
4. Add tests

When adding new models:

1. Use Pydantic `BaseModel`
2. Add type hints and descriptions
3. Add validators if needed
4. Export from `__init__.py`
5. Add examples to this README
