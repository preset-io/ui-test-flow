# UITestFlow

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Enterprise-grade UI testing platform that enables teams to validate web application functionality through natural language instructions, automated browser interactions, and intelligent test result reporting.**

## Overview

UITestFlow makes UI testing accessible and powerful by accepting test instructions in natural language or structured formats, executing them with Playwright-powered browser automation, and generating beautiful, actionable test reports with screenshots and recordings.

### Value Proposition

- **Natural Language Tests**: Write tests in plain English - no coding required
- **Structured Tests**: Or use YAML/JSON for precise control
- **Beautiful Reports**: Screenshots, videos, and detailed execution logs
- **CI/CD Ready**: Seamless integration with GitHub Actions, GitLab CI, Jenkins
- **Zero Lock-in**: Open source with self-hosted deployment option

## Key Features

### Core Capabilities

- **Multi-Format Test Input**: Natural language, YAML definitions, or JSON schemas
- **Intelligent Test Execution**: LLM-powered interpretation of test instructions via Claude MCP
- **Browser Automation**: Playwright-based headless/headed browser control (Chromium, Firefox, WebKit)
- **Visual Documentation**: Screenshots at key points, full session recordings
- **Multiple Interfaces**: CLI, TUI (Terminal UI), Web UI, REST API
- **Profile Management**: Multiple environment configurations (dev/staging/prod)
- **Authentication Support**: Form auth, OAuth, JWT, custom flows

### Example: Natural Language Test

```
Can you test the dashboard filter functionality?
Login to http://35.85.221.158:8080 with admin/admin
Navigate to any dashboard with filters
Apply a filter and verify the charts update correctly
```

### Example: YAML Test

```yaml
version: "1.0"
name: "Login and Dashboard Test"
url: "http://35.85.221.158:8080/login/"

auth:
  type: "form"
  username: "admin"
  password: "admin"

steps:
  - name: "Navigate to login page"
    action: "goto"
    url: "{{ base_url }}/login/"

  - name: "Enter credentials"
    action: "fill"
    selectors:
      - selector: 'input[name="username"]'
        value: "{{ auth.username }}"
      - selector: 'input[name="password"]'
        value: "{{ auth.password }}"

  - name: "Click login button"
    action: "click"
    selector: 'button[type="submit"]'

  - name: "Verify dashboard loads"
    action: "wait_for"
    selector: '.dashboard-content'
    timeout: 10000

evaluators:
  - name: "all_steps_completed"
    type: "execution_successful"
  - name: "no_console_errors"
    type: "console_errors"
    max_errors: 0
  - name: "page_performance"
    type: "performance"
    max_load_time: 5000
```

## Quick Start

### Installation

```bash
# Install from PyPI (coming soon)
pip install uitestflow

# Or install from source
git clone https://github.com/preset-io/ui-test-flow.git
cd ui-test-flow
pip install -e .
```

### Your First Test

1. **Create a profile** (`.uitest_profiles.yaml`):

```yaml
default: local

profiles:
  local:
    name: "Local Development"
    base_url: "http://localhost:8080"
    auth:
      type: "form"
      username: "admin"
      password: "admin"
    browser:
      headless: false
```

2. **Create a test file** (`tests/login_test.yaml`):

```yaml
version: "1.0"
name: "Simple Login Test"

steps:
  - name: "Navigate to login"
    action: "goto"
    url: "{{ base_url }}/login/"

  - name: "Fill username"
    action: "fill"
    selector: 'input[name="username"]'
    value: "{{ auth.username }}"

  - name: "Fill password"
    action: "fill"
    selector: 'input[name="password"]'
    value: "{{ auth.password }}"

  - name: "Click submit"
    action: "click"
    selector: 'button[type="submit"]'

evaluators:
  - name: "all_steps_completed"
    type: "execution_successful"
```

3. **Run the test**:

```bash
uitestflow run tests/login_test.yaml --profile local
```

## MCP Integration (Claude-Powered)

UITestFlow integrates with Anthropic's Model Context Protocol (MCP) to enable intelligent test generation and execution powered by Claude.

### Features

- **Natural Language Test Generation**: Describe your test in plain English, get a complete YAML test
- **Adaptive Selectors**: Claude suggests alternative selectors when elements change
- **Intelligent Error Recovery**: Automatic recovery from common test failures
- **Real-time Guidance**: Step-by-step validation and suggestions during execution

### Quick Start with MCP

**1. Set up your Anthropic API key:**

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Get your API key from: <https://console.anthropic.com/settings/keys>

**2. Enable MCP features:**

```bash
# Copy example configuration
cp .env.mcp.example .env

# Edit .env and set your API key
UITESTFLOW_MCP_ENABLED=true
ANTHROPIC_API_KEY=your-api-key-here
```

**3. Generate a test from natural language:**

```bash
uitestflow generate "Login to example.com with admin/password123, verify dashboard loads" \
  --output login_test.yaml
```

This creates a complete test file with all necessary steps, selectors, and evaluators.

**4. Run with Claude guidance:**

```bash
uitestflow run login_test.yaml --with-claude
```

Claude provides real-time guidance, adapts selectors, and recovers from errors automatically.

### MCP Examples

**Example 1: Simple Login Test Generation**

```bash
uitestflow generate "Navigate to /login, fill username and password, click submit, verify dashboard" \
  --base-url "http://example.com" \
  --output tests/login.yaml
```

**Example 2: Complex Form with Validation**

```bash
uitestflow generate "Fill registration form with firstName, lastName, email, password, accept terms, submit, verify success message appears" \
  --model claude-3-5-sonnet-20241022 \
  --output tests/registration.yaml
```

**Example 3: E2E Shopping Flow**

```bash
uitestflow generate "Search for 'laptop', add first result to cart, proceed to checkout, fill shipping info, complete order" \
  --model claude-3-5-sonnet-20241022 \
  --output tests/checkout.yaml
```

**Example 4: Guided Execution with Error Recovery**

```bash
# Run test with Claude guidance enabled
uitestflow run tests/complex_flow.yaml --with-claude

# Result: Claude adapts selectors and recovers from errors automatically
# - Original selector fails → Claude suggests alternatives
# - Unexpected redirect → Claude adapts the flow
# - Element not ready → Claude adds appropriate wait
```

### MCP Configuration

Control MCP behavior in your `.env` file:

```bash
# Feature toggles
UITESTFLOW_MCP_ENABLED=true
UITESTFLOW_MCP_GENERATION_ENABLED=true
UITESTFLOW_MCP_GUIDED_EXECUTION_ENABLED=true

# Claude model selection
# Options: claude-3-5-haiku-20241022 (fast), claude-3-5-sonnet-20241022 (balanced)
UITESTFLOW_MCP_CLAUDE_MODEL=claude-3-5-haiku-20241022
UITESTFLOW_MCP_CLAUDE_TEMPERATURE=0.3

# Guidance settings
UITESTFLOW_MCP_GUIDANCE_DETAIL_LEVEL=standard  # minimal, standard, verbose
UITESTFLOW_MCP_GUIDANCE_MAX_RETRIES=3

# Features
UITESTFLOW_MCP_SELECTOR_ADAPTATION_ENABLED=true
UITESTFLOW_MCP_ERROR_RECOVERY_ENABLED=true
```

### MCP Documentation

- **[MCP User Guide](docs/MCP_GUIDE.md)** - Complete guide to MCP features
- **[MCP API Reference](docs/MCP_API.md)** - REST API and WebSocket documentation
- **[MCP Examples](examples/mcp_test_generation.py)** - Comprehensive code examples

### Cost Considerations

MCP uses the Anthropic API which has usage-based pricing:

- **Test Generation**: ~$0.001-0.01 per test (depending on complexity)
- **Guided Execution**: ~$0.005-0.02 per test run (depending on steps)
- **Haiku Model**: Most cost-effective for simple to moderate tests
- **Sonnet Model**: Better for complex workflows, slightly higher cost

**Tips to minimize costs:**

- Use Haiku (default) for most tests
- Enable response caching: `UITESTFLOW_MCP_CACHE_RESPONSES=true`
- Use minimal guidance level for simple tests
- Disable guidance for tests that don't need it

## User Interfaces

UITestFlow provides three interfaces to accommodate different workflows:

### 1. Web UI

Beautiful browser-based interface for visual test management and real-time monitoring.

```bash
# Start the web server (development mode with auto-reload)
uitestflow serve --reload

# Or using make
make serve

# Production mode with multiple workers
make serve-prod
```

Access the Web UI at:

- **Dashboard**: <http://localhost:8080>
- **API Docs**: <http://localhost:8080/docs>

**Features**:

- Visual test creation and editing
- Real-time test execution monitoring
- Screenshot gallery and video playback
- Shareable test reports
- Team collaboration
- Analytics and trends
- **AI Test Generator** - Generate tests from natural language descriptions
- **Live Execution View** - Real-time step progress with screenshots
- **Claude Guidance Panel** - View AI suggestions and adaptations

**MCP-Powered Features** (with Anthropic API key):

- **AI Test Generator** (`/generate` route):
  - Describe your test in plain English
  - Select Claude model (Haiku for speed, Sonnet for complex tests)
  - Adjust temperature for creativity vs. consistency
  - View generated test in JSON/YAML/Preview
  - Save and run tests directly from the UI

- **Real-Time Execution View** (`/tests/:id/execute` route):
  - Live progress tracking with step-by-step status
  - Screenshot gallery updated in real-time via WebSocket
  - Console logs and error messages
  - Execution metrics (duration, progress %)
  - Connection status indicator

- **Claude Guidance Panel**:
  - Step-by-step AI guidance and suggestions
  - Selector adaptation history (original → adapted)
  - Error recovery actions taken
  - Expandable/collapsible per step
  - Copy suggestions to clipboard

**Quick UI Tour**:

1. **Dashboard** (`/`) - Test overview and recent runs
2. **AI Generate** (`/generate`) - Generate tests with Claude
3. **Tests** (`/library`) - Browse and manage test library
4. **Run Test** (`/runner`) - Execute tests manually
5. **Results** (`/results`) - View test execution history

See [UI Guide](docs/ui-guide.md) for detailed documentation.

### 2. Terminal UI (TUI)

Interactive terminal dashboard for local development (Coming Soon).

```bash
# Launch the TUI
uitestflow tui

# Or using make
make tui
```

**Planned Features**:

- Interactive test browser
- Real-time execution monitoring
- Vim-style navigation
- Screenshot preview
- Profile management

### 3. Command Line Interface (CLI)

Perfect for automation, CI/CD pipelines, and scripting.

```bash
# Run a specific test file
uitestflow run tests/dashboard_filters.yaml --profile staging

# Run all tests matching a pattern
uitestflow run tests/ --pattern "login_*" --profile production

# Run from URL (e.g., GitHub PR)
uitestflow run-from-url "https://github.com/apache/superset/pull/35152" \
  --base-url "http://35.85.221.158:8080" \
  --auth-user admin \
  --auth-pass admin
```

### Example Output

```
╭─── Test Execution ───╮
│ Profile: staging     │
│ Browser: chromium    │
│ Headless: true       │
╰──────────────────────╯

Running: Login and Navigate to Dashboard

  ✓ Navigate to login page (1.2s)
    📸 Screenshot: login_page.png

  ✓ Enter credentials (0.3s)

  ✓ Click login button (0.5s)
    📸 Screenshot: after_login.png

  ✓ Verify dashboard loads (2.1s)
    📸 Screenshot: dashboard.png

╭─── Evaluators ───╮
│ ✓ all_steps_completed │
│ ✓ no_console_errors   │
│ ✓ page_load_time < 5s │
╰───────────────────────╯

Result: PASSED ✓
Duration: 4.1s
Screenshots: 3
Report: https://uitestflow.preset.io/runs/12345
```

### Management Commands

```bash
# List available profiles
uitestflow profiles list

# Test a profile's connectivity
uitestflow profiles test staging

# Initialize configuration
uitestflow config init

# Validate configuration
uitestflow config validate

# Show version information
uitestflow version
```

### Database Setup

UITestFlow requires PostgreSQL for the web server. You have two options:

**Option 1: Use Local PostgreSQL (Recommended for Development)**

```bash
# Setup database on your local PostgreSQL installation
make setup-local-db

# Start the server
uitestflow serve --reload
```

See [LOCAL_POSTGRES_SETUP.md](./LOCAL_POSTGRES_SETUP.md) for detailed instructions.

**Option 2: Use Docker**

```bash
# Start just the database services
make docker-up-db

# Or start all services (database, Redis, API server, workers)
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

**Note:** The CLI tool works standalone without a database. The web UI requires PostgreSQL.

## Configuration

### Profile Configuration (`.uitest_profiles.yaml`)

```yaml
default: local

profiles:
  local:
    name: "Local Development"
    base_url: "http://localhost:8080"
    auth:
      type: "form"
      username: "${LOCAL_USERNAME}"
      password: "${LOCAL_PASSWORD}"
    browser:
      headless: false
      slowmo: 500  # Slow down for visibility

  staging:
    name: "Staging Environment"
    base_url: "https://staging.preset.io"
    auth:
      type: "oauth"
      provider: "okta"
      client_id: "${OKTA_CLIENT_ID}"
      client_secret: "${OKTA_CLIENT_SECRET}"
    browser:
      headless: true

  production:
    name: "Production Environment"
    base_url: "https://app.preset.io"
    auth:
      type: "oauth"
      provider: "okta"
      client_id: "${OKTA_PROD_CLIENT_ID}"
      client_secret: "${OKTA_PROD_CLIENT_SECRET}"
    browser:
      headless: true
    notifications:
      on_failure:
        - slack: "#alerts"
        - email: "oncall@preset.io"
```

### Browser Configuration

```yaml
browser:
  type: "chromium"  # chromium, firefox, webkit
  headless: true
  viewport:
    width: 1920
    height: 1080
  device: "Desktop"  # or "iPhone 12", "Pixel 5"
  locale: "en-US"
  timezone: "America/Los_Angeles"
```

## CI/CD Integration

### GitHub Actions

```yaml
name: UI Tests
on: [pull_request]

jobs:
  ui-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install UITestFlow
        run: pip install uitestflow

      - name: Run UI Tests
        env:
          UITEST_API_KEY: ${{ secrets.UITEST_API_KEY }}
        run: |
          uitestflow run tests/ --profile staging --format junit --output results.xml

      - name: Publish Test Results
        uses: EnricoMi/publish-unit-test-result-action@v2
        if: always()
        with:
          files: results.xml
```

### GitLab CI

```yaml
ui_tests:
  stage: test
  image: python:3.11
  script:
    - pip install uitestflow
    - uitestflow run tests/ --profile staging --format junit --output results.xml
  artifacts:
    reports:
      junit: results.xml
```

## Preset Use Case: Superset PR Testing

UITestFlow was built with Apache Superset and Preset workflows in mind. Here's how Preset engineers use it:

### Scenario: Testing Dashboard Filter Changes

A PR claims to fix dashboard filter functionality. Instead of manual testing:

1. **PR Description includes test instructions**:

   ```
   Testing instructions:
   1. Login to http://35.85.221.158:8080/ (admin/admin)
   2. Navigate to any dashboard with filters
   3. Apply a filter from the dropdown
   4. Verify charts update correctly
   5. Verify URL parameters reflect filter state
   ```

2. **CI automatically runs the test**:

   ```bash
   uitestflow run-from-pr ${{ github.event.pull_request.number }} \
     --profile pr-testing \
     --base-url http://35.85.221.158:8080
   ```

3. **Results posted to PR**:

   ```
   🤖 UI Test Results

   ✅ Test Passed (4.2s)

   Steps:
   ✓ Login successful (1.2s)
   ✓ Dashboard loaded (0.8s)
   ✓ Filter applied (1.1s)
   ✓ Charts updated correctly (1.1s)

   📊 View full report: https://uitestflow.preset.io/runs/abc-123
   📸 Screenshots: 6 captured
   🎥 Video: Available
   ```

### Example Test: Superset Dashboard Filters

See [`examples/basic/dashboard_filters.yaml`](examples/basic/dashboard_filters.yaml) for a complete example.

## Documentation

### Getting Started

- **[Getting Started Guide](docs/getting-started.md)** - Installation and first test walkthrough
- **[UI Guide](docs/ui-guide.md)** - Complete guide to Web UI, TUI, and CLI

### Writing Tests

- **[Writing Tests](docs/guides/writing-tests.md)** - Comprehensive test authoring guide
- **[YAML Reference](docs/guides/yaml-reference.md)** - Complete YAML schema documentation
- **[Evaluators](docs/guides/evaluators.md)** - Built-in evaluators and custom evaluators

### Integration

- **[CI/CD Integration](docs/guides/ci-cd-integration.md)** - Integration guides for all major CI platforms
- **[API Documentation](docs/api/rest-api.md)** - REST API reference
- **[CLI Reference](docs/api/cli-reference.md)** - Complete CLI command documentation

### UI Development

- **[React UI Setup](uitestflow/ui/README.md)** - React development setup and component docs

## Examples

Explore complete test examples in the [`examples/`](examples/) directory:

- **[Basic Login Test](examples/basic/login_test.yaml)** - Simple form authentication
- **[Dashboard Filters](examples/basic/dashboard_filters.yaml)** - Superset dashboard testing
- **[E2E User Flows](examples/advanced/e2e-user-flow.yaml)** - Multi-step user journeys
- **[Visual Regression](examples/advanced/visual-regression.yaml)** - Screenshot comparison
- **[Performance Testing](examples/advanced/performance-test.yaml)** - Load time validation

### MCP Example Tests

Ready-to-run example tests demonstrating MCP features (`examples/tests/`):

- **[login_flow.yaml](examples/tests/login_flow.yaml)** - Login flow with validation
- **[form_submission.yaml](examples/tests/form_submission.yaml)** - Multi-field form testing
- **[navigation_flow.yaml](examples/tests/navigation_flow.yaml)** - Multi-page navigation
- **[search_workflow.yaml](examples/tests/search_workflow.yaml)** - Search and result validation
- **[e2e_shopping.yaml](examples/tests/e2e_shopping.yaml)** - Complete e2e shopping cart flow

**Run all example tests:**

```bash
# Run all MCP example tests with report generation
./scripts/run_example_tests.sh --open-report

# Or run individual tests
uitestflow run examples/tests/login_flow.yaml
uitestflow run examples/tests/e2e_shopping.yaml --with-claude
```

The script will:

- Execute all 5 example tests sequentially
- Generate screenshots and logs for each test
- Create an HTML report with results summary
- Automatically open the report in your browser (with `--open-report`)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Development setup
- Code style guidelines (Black, Ruff, type hints)
- Testing requirements (pytest, coverage)
- PR process and commit conventions
- Code review guidelines

### Quick Start for Contributors

```bash
# Clone the repository
git clone https://github.com/preset-io/ui-test-flow.git
cd uitestflow

# Set up development environment (creates venv, installs dependencies, pre-commit hooks)
make setup

# Or manually:
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -e ".[dev]"
pre-commit install

# Run tests
pytest
# or
make test

# Run linters and formatters
make lint
make format

# Start services with Docker
make docker-up

# View all available commands
make help
```

## Architecture

UITestFlow is built with a modular architecture:

- **Core Engine**: Test parsing, execution, and result generation
- **Browser Automation**: Playwright integration with MCP support
- **LLM Integration**: Claude via Model Context Protocol for natural language interpretation
- **CLI/TUI**: Typer + Rich + Textual for beautiful terminal interfaces
- **Web UI** (coming soon): React + TypeScript + Tailwind CSS
- **API Server** (coming soon): FastAPI + PostgreSQL + Celery

## Roadmap

- **Phase 1 (Current)**: CLI tool with basic YAML test execution
- **Phase 2**: LLM-powered natural language tests
- **Phase 3**: Web UI and REST API
- **Phase 4**: Advanced CI/CD integration and GitHub App
- **Phase 5**: Enterprise features (RBAC, audit logging, SSO)
- **Phase 6**: Visual regression, accessibility testing, mobile support

## License

UITestFlow is licensed under the [Apache License 2.0](LICENSE).

The core testing engine, CLI, and basic features are fully open source. Enterprise features (RBAC, SAML/SSO, audit logging) are available in the commercial version.

## Support

- **Community Support**: [GitHub Discussions](https://github.com/preset-io/ui-test-flow/discussions)
- **Bug Reports**: [GitHub Issues](https://github.com/preset-io/ui-test-flow/issues)
- **Commercial Support**: Contact [support@preset.io](mailto:support@preset.io)

## Acknowledgments

UITestFlow is built on the shoulders of giants:

- [Playwright](https://playwright.dev) - Modern browser automation
- [Anthropic Claude](https://anthropic.com) - LLM-powered test interpretation
- [Model Context Protocol](https://modelcontextprotocol.io) - Standardized LLM integration
- [MCP Playwright](https://github.com/executeautomation/mcp-playwright) - MCP server for Playwright

Built with love by the team at [Preset](https://preset.io) for the Apache Superset community and beyond.
