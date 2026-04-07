# Contributing to UITestFlow

Thank you for your interest in contributing to UITestFlow! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style Guide](#code-style-guide)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Commit Message Conventions](#commit-message-conventions)
- [Code Review Guidelines](#code-review-guidelines)

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- A GitHub account

### First-time Setup

1. **Fork the repository** on GitHub

2. **Clone your fork**:

   ```bash
   git clone https://github.com/YOUR-USERNAME/ui-test-flow.git
   cd ui-test-flow
   ```

3. **Add upstream remote**:

   ```bash
   git remote add upstream https://github.com/preset-io/ui-test-flow.git
   ```

## Development Setup

### Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### Install Development Dependencies

```bash
# Install package in editable mode with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (recommended)
pre-commit install
```

### Install Playwright Browsers

```bash
# Install required browser binaries
playwright install chromium firefox webkit
```

### Verify Installation

```bash
# Run tests to verify setup
pytest

# Run linters
black --check .
ruff check .
mypy .
```

## Code Style Guide

We follow strict code style guidelines to ensure consistency and maintainability.

### Python Style

- **Formatter**: [Black](https://black.readthedocs.io/) (line length: 88)
- **Linter**: [Ruff](https://beta.ruff.rs/docs/) (replacing Flake8, isort, etc.)
- **Type Checker**: [mypy](https://mypy.readthedocs.io/) with strict mode
- **Docstrings**: Google style

### Type Hints

All functions and methods must have type hints:

```python
# Good
def execute_test(
    test_file: str,
    profile: str | None = None,
    headless: bool = True
) -> TestResult:
    """Execute a test from a file.

    Args:
        test_file: Path to the test YAML file
        profile: Profile name to use (default: from config)
        headless: Run browser in headless mode

    Returns:
        TestResult containing execution details and status

    Raises:
        TestExecutionError: If test execution fails
        FileNotFoundError: If test file doesn't exist
    """
    ...
```

```python
# Bad - missing type hints
def execute_test(test_file, profile=None):
    ...
```

### Imports

Imports are automatically organized by Ruff. Follow this order:

1. Standard library imports
2. Third-party imports
3. Local application imports

```python
# Good
import os
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright
from pydantic import BaseModel

from uitestflow.core.executor import TestExecutor
from uitestflow.models.test import TestDefinition
```

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `TestExecutor`, `BrowserManager`)
- **Functions/Methods**: `snake_case` (e.g., `execute_test`, `parse_yaml`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`, `MAX_RETRIES`)
- **Private members**: Prefix with `_` (e.g., `_internal_method`)

### Code Organization

```python
# Good - clear structure with docstring
class TestExecutor:
    """Executes UI tests using Playwright.

    This class manages the lifecycle of test execution including
    browser session management, step execution, and result collection.
    """

    def __init__(self, config: ExecutorConfig) -> None:
        """Initialize the test executor.

        Args:
            config: Configuration for test execution
        """
        self._config = config
        self._browser: Browser | None = None

    async def execute(self, test_def: TestDefinition) -> TestResult:
        """Execute a test definition.

        Args:
            test_def: The test to execute

        Returns:
            TestResult with execution details

        Raises:
            TestExecutionError: If execution fails
        """
        ...
```

## Testing Requirements

### Test Framework

We use [pytest](https://pytest.org/) for all tests.

### Coverage Requirements

- **Minimum coverage**: 80% overall
- **Critical code**: 100% coverage for core execution logic
- **New code**: All new features must include tests

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=uitestflow --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_executor.py

# Run specific test
pytest tests/test_executor.py::test_execute_simple_test

# Run with verbose output
pytest -v

# Run only fast tests (skip integration tests)
pytest -m "not integration"
```

### Writing Tests

```python
import pytest
from uitestflow.core.executor import TestExecutor
from uitestflow.models.test import TestDefinition


class TestTestExecutor:
    """Tests for TestExecutor class."""

    @pytest.fixture
    def executor(self):
        """Create a test executor instance."""
        return TestExecutor(config=ExecutorConfig(headless=True))

    @pytest.fixture
    def simple_test(self):
        """Create a simple test definition."""
        return TestDefinition(
            name="Simple Test",
            steps=[
                {"action": "goto", "url": "https://example.com"}
            ]
        )

    async def test_execute_simple_test(self, executor, simple_test):
        """Test executing a simple test succeeds."""
        result = await executor.execute(simple_test)
        assert result.passed is True
        assert result.steps_executed == 1

    async def test_execute_invalid_url_fails(self, executor):
        """Test that invalid URLs fail gracefully."""
        test = TestDefinition(
            name="Invalid URL Test",
            steps=[{"action": "goto", "url": "not-a-url"}]
        )
        with pytest.raises(TestExecutionError):
            await executor.execute(test)
```

### Test Organization

```
tests/
├── unit/              # Unit tests (fast, isolated)
│   ├── test_parser.py
│   ├── test_executor.py
│   └── test_evaluators.py
├── integration/       # Integration tests (slower, requires services)
│   ├── test_playwright_integration.py
│   └── test_mcp_integration.py
├── e2e/              # End-to-end tests (slowest, full system)
│   └── test_cli.py
└── fixtures/         # Shared test fixtures
    ├── conftest.py
    └── sample_tests/
```

## Pull Request Process

### Before Opening a PR

All new functionality should be code reviewed by a peer. Quick bug fixes or minor cosmetic changes should still be reviewed, though there is some flexibility for urgent fixes.

### Branch Naming

For Preset internal contributors, follow the Shortcut integration format:

```bash
[user_name]/ch[ticket-number]/[additional description]
```

Example:

```bash
craig/ch123/add-oauth-support
```

For external contributors, use descriptive branch names:

```bash
feature/add-oauth-support
fix/screenshot-capture-bug
docs/improve-yaml-examples
```

### Before Submitting

1. **Rebase or merge main into your branch**:

   ```bash
   git fetch upstream
   git rebase upstream/main
   # or
   git merge upstream/main
   ```

2. **Ensure all tests pass**:

   ```bash
   pytest
   ```

3. **Ensure linting passes**:

   ```bash
   black .
   ruff check .
   mypy .
   ```

4. **Update documentation** if you've changed APIs or behavior

### Creating the PR

1. **Push your branch to GitHub**:

   ```bash
   git push origin your-branch-name
   ```

2. **Open a pull request** with:
   - **Clear title** following conventions: `feat:`, `fix:`, `chore:`, or `release:`
   - **Detailed description** of what's changed and why
   - **Screenshots** if there are UI changes
   - **Testing steps** you performed
   - **Link to related issues** or Shortcut tickets

3. **Mark as draft** if not ready for review or CI isn't green

4. **Assign reviewers** who have context with the affected code

### PR Title Conventions

Prefix your PR title with one of:

- `feat:` - New feature
- `fix:` - Bug fix
- `chore:` - Maintenance tasks, dependency updates
- `docs:` - Documentation changes
- `refactor:` - Code refactoring without behavior change
- `test:` - Adding or updating tests
- `release:` - Release-related changes

Examples:

- `feat: add OAuth authentication support`
- `fix: resolve screenshot capture timing issue`
- `chore: update Playwright to v1.40`
- `docs: improve YAML test examples`

### Breaking Up Large Features

If the feature is large, consider breaking into multiple PRs:

1. Database schema/model changes
2. Backend API endpoints
3. Frontend UI components
4. Integration and documentation

This makes review easier and reduces risk.

## Commit Message Conventions

### Format

```
<type>: <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, missing semi-colons, etc.)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat: add support for OAuth authentication

Implements OAuth 2.0 authentication flow with support for
multiple providers (Okta, Google, GitHub).

- Add OAuthProvider class
- Implement PKCE flow
- Add configuration options
- Update documentation

Closes #123
```

```
fix: resolve race condition in screenshot capture

Screenshots were sometimes captured before page fully loaded,
resulting in incomplete images. Now properly waits for network
idle before capturing.

Fixes #456
```

### Important Notes

- **DO NOT amend commits** unless explicitly asked
- **DO NOT force push** after PR reviews have started (makes it hard to see changes)
- Write clear, descriptive commit messages
- Keep commits focused and atomic

## Code Review Guidelines

### For PR Authors

1. **Respond to all comments** - even if just to acknowledge
2. **Ask questions** if feedback is unclear
3. **Mark conversations as resolved** once addressed
4. **Keep the PR updated** - push new commits to address feedback
5. **Be patient and respectful** - reviewers are helping improve your code

### For Reviewers

#### Before Approving

1. **Verify CI passes** - all builds, tests, and linting must pass
2. **Review both code and intent** - understand what the PR is doing and why
3. **Check test coverage** - ensure new code has appropriate tests
4. **Verify tests aren't modified incorrectly** - tests shouldn't be changed to make features pass
5. **Follow team conventions** - naming, structure, documentation
6. **Ask questions** if something is unclear - understanding comes before approval

#### Providing Feedback

1. **Be constructive** - suggest improvements, don't just criticize
2. **Be clear** if something is a suggestion vs. required for approval:
   - "Nit: Consider renaming this to..." (suggestion)
   - "Please add error handling here" (required)
3. **Provide context** - explain why something should be changed
4. **Recognize good work** - positive feedback is valuable too
5. **Tag others** if you're not confident in an area

#### Example Reviews

Good review comment:

```
This looks good overall! A few thoughts:

1. Could you add error handling for the case where the selector isn't found?
   This would make debugging easier when tests fail.

2. Nit: Consider extracting this into a helper function since it's used in
   multiple places.

3. Love the comprehensive test coverage here!
```

Not-so-good review comment:

```
This won't work.
```

### Merging

- **Requester is responsible** for merging and deleting the branch
- **Reviewer may merge** for quick changes with approval
- **Coordinate testing** requirements with the PR owner
- **Squash commits** if there are many small fixup commits

## Development Workflow

### Typical Development Cycle

```bash
# 1. Create a branch
git checkout -b feature/my-feature

# 2. Make changes
# ... edit files ...

# 3. Run tests locally
pytest
black .
ruff check .
mypy .

# 4. Commit changes
git add .
git commit -m "feat: add my feature"

# 5. Push to GitHub
git push origin feature/my-feature

# 6. Open PR on GitHub

# 7. Address review feedback
# ... make more changes ...
git add .
git commit -m "fix: address review feedback"
git push origin feature/my-feature

# 8. Once approved and CI passes, merge via GitHub UI
```

### Keeping Your Branch Updated

```bash
# Fetch latest changes
git fetch upstream

# Rebase your branch (preferred)
git rebase upstream/main

# Or merge (if rebase is complex)
git merge upstream/main

# Push updated branch
git push origin your-branch-name
```

## Getting Help

- **Questions?** Ask in [GitHub Discussions](https://github.com/preset-io/ui-test-flow/discussions)
- **Found a bug?** Open an [issue](https://github.com/preset-io/ui-test-flow/issues)
- **Need guidance?** Tag @maintainers in your PR

## License

By contributing to UITestFlow, you agree that your contributions will be licensed under the Apache License 2.0.

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please:

- Be respectful and constructive
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

Thank you for contributing to UITestFlow!
