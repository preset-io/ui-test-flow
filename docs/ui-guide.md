# UITestFlow UI Guide

Complete guide to using UITestFlow's user interfaces: Web UI, Terminal UI (TUI), and CLI.

## Table of Contents

- [Overview](#overview)
- [Web UI](#web-ui)
- [Terminal UI (TUI)](#terminal-ui-tui)
- [CLI Reference](#cli-reference)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [API Documentation](#api-documentation)

---

## Overview

UITestFlow provides three distinct user interfaces to accommodate different workflows and preferences:

1. **Web UI** - Browser-based interface for visual test management and reporting
2. **Terminal UI (TUI)** - Interactive terminal dashboard for local development
3. **CLI** - Command-line interface for automation and CI/CD integration

### When to Use Each Interface

| Interface | Best For | Features |
|-----------|----------|----------|
| **Web UI** | Team collaboration, visual reports, remote access | Full-featured dashboard, shareable reports, real-time updates |
| **TUI** | Local development, quick testing, terminal workflows | Fast navigation, keyboard-driven, low overhead |
| **CLI** | Automation, CI/CD, scripting | Scriptable, exit codes, multiple output formats |

---

## Web UI

### Starting the Web UI

#### Local Development

```bash
# Start with auto-reload (development mode)
uitestflow serve --reload

# Or using make
make serve
```

The web UI will be available at:

- **Web Interface**: <http://localhost:8080>
- **API Documentation**: <http://localhost:8080/docs>
- **OpenAPI Spec**: <http://localhost:8080/openapi.json>

#### Production Deployment

```bash
# Start in production mode with multiple workers
uitestflow serve --host 0.0.0.0 --port 8080 --workers 4

# Or using make
make serve-prod
```

#### Docker Compose

```bash
# Start all services including web UI
docker-compose up -d

# Start with UI development server (React hot reload)
docker-compose --profile ui-dev up -d
```

### Web UI Features

#### 1. Dashboard

The main dashboard provides an overview of your testing activity:

- **Test Run Statistics**: Pass/fail rates, trends over time
- **Recent Test Runs**: Quick access to latest results
- **Flaky Test Detection**: Identifies unreliable tests
- **Performance Metrics**: Average execution times, success rates

**Navigation**: Click on the UITestFlow logo or "Dashboard" in the sidebar

#### 2. Test Library

Browse, create, and manage your test definitions:

- **Browse Tests**: View all test definitions with search and filters
- **Create Test**: Visual editor or YAML/JSON editor
- **Import from PR**: Import test instructions from GitHub PR descriptions
- **Templates**: Start from pre-built test templates
- **Tags**: Organize tests with custom tags

**Navigation**: Click "Tests" in the sidebar

**Creating a Test**:

1. Click "New Test" button
2. Choose format: Natural Language, YAML, or JSON
3. Fill in test details
4. Add steps and evaluators
5. Save and run

#### 3. Test Runner

Execute tests manually with real-time monitoring:

- **Manual Execution**: Run any test with custom parameters
- **Real-time Progress**: Watch test execution live
- **Browser Preview**: See browser state during execution (VNC-style)
- **Pause/Resume/Abort**: Control test execution

**Navigation**: Click "Run" in the sidebar, or click "Run" on any test

**Running a Test**:

1. Select a test from the library
2. Choose a profile (environment)
3. Configure options (headless, screenshots, etc.)
4. Click "Run Test"
5. Monitor progress in real-time

#### 4. Results Viewer

View detailed test results and artifacts:

- **Test Run Details**: Full execution log with timestamps
- **Screenshot Gallery**: Browse captured screenshots with lightbox
- **Video Playback**: Watch recorded test sessions
- **Console Logs**: Searchable and filterable browser console output
- **Network Activity**: HAR viewer for HTTP requests/responses
- **Playwright Trace**: Integrated trace viewer for debugging
- **Share Links**: Generate shareable URLs for results

**Navigation**: Click "Results" in the sidebar, or click on any test run

**Viewing Results**:

- Click on any screenshot to view full-size with navigation
- Use arrow keys to navigate between screenshots
- Click "Download Video" to save the test recording
- Click "View Trace" to open Playwright's trace viewer
- Click "Share" to generate a public link (with optional password)

#### 5. Profiles

Manage environment configurations:

- **View Profiles**: List all configured environments
- **Create/Edit**: Add new profiles or modify existing ones
- **Test Connectivity**: Verify profile settings work
- **Auth Configuration**: Set up authentication methods
- **Browser Settings**: Configure browser options per profile
- **Notifications**: Set up alerts for test failures

**Navigation**: Click "Profiles" in the sidebar

**Creating a Profile**:

1. Click "New Profile"
2. Enter profile details (name, base URL)
3. Configure authentication (form, OAuth, custom)
4. Set browser options (headless, viewport, device emulation)
5. Configure notifications (Slack, email)
6. Save and test connectivity

#### 6. Analytics

View testing metrics and trends:

- **Coverage**: Test coverage by feature/page
- **Execution Trends**: Success rates over time
- **Performance Trends**: Page load times, execution duration
- **Cost Tracking**: Resource usage and estimated costs
- **Flaky Tests**: Tests with inconsistent results
- **Top Failures**: Most frequently failing tests

**Navigation**: Click "Analytics" in the sidebar

#### 7. Settings

Configure application settings:

- **User Profile**: Update your account information
- **API Keys**: Generate and manage API keys for programmatic access
- **Organization**: Organization settings (for team plans)
- **Billing**: View usage and manage subscription (for SaaS)
- **Integrations**: Connect with Slack, GitHub, etc.

**Navigation**: Click the user menu (top right) → "Settings"

### Web UI Screenshots

> Note: Screenshots will be added as the UI is developed

**Dashboard View**

```
[Placeholder for dashboard screenshot]
```

**Test Runner**

```
[Placeholder for test runner screenshot]
```

**Results Viewer with Screenshots**

```
[Placeholder for results viewer screenshot]
```

---

## Terminal UI (TUI)

> **Status**: The TUI is currently under development. This section documents the planned functionality.

### Starting the TUI

```bash
# Launch TUI with default profile
uitestflow tui

# Launch with specific profile
uitestflow tui --profile staging

# Or using make
make tui
```

### TUI Features (Coming Soon)

The Terminal UI will provide a full-featured interactive dashboard in your terminal using the Textual framework.

#### Planned Screens

1. **Home Screen**
   - Quick actions (run recent tests, select profile)
   - Test run history summary
   - Profile selector
   - System status

2. **Test Explorer**
   - Browse test files with tree view
   - Preview test definitions
   - Run individual tests
   - Edit tests (launches $EDITOR)

3. **Test Runner**
   - Real-time test execution view
   - Live screenshot preview (ASCII art or image)
   - Console logs streaming
   - Progress indicators and status

4. **Results Viewer**
   - Test run history table
   - Filterable results
   - Drill-down to individual runs
   - Screenshot gallery (terminal-compatible)

5. **Browser Preview**
   - Live view of browser state
   - DOM inspector (tree view)
   - Network requests (table)
   - Console logs (live streaming)

6. **Configuration**
   - Profile management
   - Settings editor
   - Auth debugger
   - System diagnostics

#### Navigation (Planned)

The TUI will support vim-style keybindings and standard navigation:

- **Arrow keys** or **hjkl**: Navigate up/down/left/right
- **Tab** / **Shift+Tab**: Switch between panels
- **Enter**: Select/activate item
- **Space**: Toggle/check item
- **1-6**: Switch to screen by number
- **/**: Global search
- **?**: Show help modal
- **r**: Run selected test
- **e**: Edit selected test
- **q** or **Ctrl+C**: Quit

---

## CLI Reference

### Core Commands

#### `uitestflow run`

Run a UI test from a test file.

```bash
uitestflow run <test-file> [OPTIONS]
```

**Options**:

- `--profile, -p TEXT`: Profile name from .uitest_profiles.yaml
- `--headless/--headed`: Run browser in headless mode (default: headless)
- `--output, -o PATH`: Output file for test results
- `--format, -f [json|yaml|table|html]`: Output format (default: table)
- `--verbose`: Show detailed output

**Examples**:

```bash
# Run with default settings
uitestflow run tests/login.yaml

# Run with specific profile in headed mode
uitestflow run tests/login.yaml --profile staging --headed

# Run and save results as JSON
uitestflow run tests/login.yaml --output results.json --format json

# Run with verbose output
uitestflow run tests/login.yaml --verbose
```

**Exit Codes**:

- `0`: Test passed
- `1`: Test failed
- `2`: Error during execution

#### `uitestflow serve`

Start the FastAPI web server for the Web UI.

```bash
uitestflow serve [OPTIONS]
```

**Options**:

- `--host, -h TEXT`: Host to bind to (default: 0.0.0.0)
- `--port, -p INTEGER`: Port to bind to (default: 8080)
- `--reload`: Enable auto-reload for development
- `--workers, -w INTEGER`: Number of worker processes (production only)

**Examples**:

```bash
# Development mode with auto-reload
uitestflow serve --reload

# Production mode with 4 workers
uitestflow serve --workers 4

# Custom host and port
uitestflow serve --host 127.0.0.1 --port 3000
```

#### `uitestflow tui`

Launch the interactive Terminal User Interface.

```bash
uitestflow tui [OPTIONS]
```

**Options**:

- `--profile, -p TEXT`: Default profile to use in TUI

**Examples**:

```bash
# Launch with default profile
uitestflow tui

# Launch with staging profile
uitestflow tui --profile staging
```

### Profile Management

#### `uitestflow profiles list`

List all available profiles.

```bash
uitestflow profiles list [OPTIONS]
```

**Options**:

- `--config, -c PATH`: Path to profiles configuration file

**Example**:

```bash
uitestflow profiles list
```

**Sample Output**:

```
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Profile ID ┃ Name                 ┃ Base URL                  ┃ Mode     ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ local      │ Local Development    │ http://localhost:8080     │ headed   │
│ staging    │ Staging Environment  │ https://staging.example…  │ headless │
│ production │ Production Environ…  │ https://app.example.com   │ headless │
└────────────┴──────────────────────┴───────────────────────────┴──────────┘
```

#### `uitestflow profiles test`

Test connectivity for a profile.

```bash
uitestflow profiles test <profile-name> [OPTIONS]
```

**Options**:

- `--config, -c PATH`: Path to profiles configuration file

**Example**:

```bash
uitestflow profiles test staging
```

### Configuration Management

#### `uitestflow config init`

Initialize a new configuration file.

```bash
uitestflow config init [OPTIONS]
```

**Options**:

- `--output, -o PATH`: Output path for configuration file (default: .uitest_profiles.yaml)
- `--force, -f`: Overwrite existing configuration

**Example**:

```bash
uitestflow config init
```

#### `uitestflow config validate`

Validate configuration file.

```bash
uitestflow config validate [OPTIONS]
```

**Options**:

- `--config, -c PATH`: Path to configuration file

**Example**:

```bash
uitestflow config validate
```

### Utility Commands

#### `uitestflow version`

Show version information.

```bash
uitestflow version
```

---

## Keyboard Shortcuts

### Web UI Shortcuts

| Shortcut | Action |
|----------|--------|
| `?` | Show help modal |
| `n` | Create new test |
| `r` | Run selected test |
| `s` | Search tests |
| `Esc` | Close modal/cancel |
| `Left/Right Arrow` | Navigate screenshots |
| `Space` | Play/pause video |
| `/` | Focus search bar |

### TUI Shortcuts (Coming Soon)

| Shortcut | Action |
|----------|--------|
| `↑/↓` or `k/j` | Navigate up/down |
| `←/→` or `h/l` | Navigate left/right |
| `Tab` | Next panel |
| `Shift+Tab` | Previous panel |
| `Enter` | Select/activate |
| `Space` | Toggle |
| `1-6` | Switch screen |
| `/` | Search |
| `?` | Help |
| `r` | Run test |
| `e` | Edit test |
| `q` | Quit |
| `Ctrl+C` | Force quit |

---

## API Documentation

The REST API is automatically documented using FastAPI's built-in OpenAPI support.

### Accessing API Documentation

When the server is running:

- **Interactive Docs (Swagger UI)**: <http://localhost:8080/docs>
- **Alternative Docs (ReDoc)**: <http://localhost:8080/redoc>
- **OpenAPI JSON**: <http://localhost:8080/openapi.json>

### Authentication

Most API endpoints require authentication using a JWT token or API key.

#### Getting a Token

```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'
```

Response:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Using the Token

Include the token in the Authorization header:

```bash
curl -X GET http://localhost:8080/api/tests \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

#### Using an API Key

Alternatively, use an API key:

```bash
curl -X GET http://localhost:8080/api/tests \
  -H "X-API-Key: your-api-key-here"
```

### Key API Endpoints

#### Test Management

```bash
# List all tests
GET /api/tests

# Get test by ID
GET /api/tests/{test_id}

# Create new test
POST /api/tests

# Update test
PUT /api/tests/{test_id}

# Delete test
DELETE /api/tests/{test_id}
```

#### Test Execution

```bash
# Run a test
POST /api/runs
{
  "test_id": "uuid",
  "profile": "staging",
  "options": {
    "headless": true,
    "screenshots": true
  }
}

# Get run status
GET /api/runs/{run_id}

# Abort running test
POST /api/runs/{run_id}/abort

# List all runs
GET /api/runs?limit=50&offset=0
```

#### Results and Artifacts

```bash
# Get test results
GET /api/runs/{run_id}/result

# List screenshots
GET /api/runs/{run_id}/screenshots

# Get specific screenshot
GET /api/runs/{run_id}/screenshots/{index}

# Download video
GET /api/runs/{run_id}/video

# Get Playwright trace
GET /api/runs/{run_id}/trace

# Get console logs
GET /api/runs/{run_id}/logs

# Get HAR file
GET /api/runs/{run_id}/har
```

#### Profiles

```bash
# List profiles
GET /api/profiles

# Get profile
GET /api/profiles/{profile_id}

# Create profile
POST /api/profiles

# Update profile
PUT /api/profiles/{profile_id}

# Test profile connectivity
POST /api/profiles/{profile_id}/test
```

### Example: Running a Test via API

```bash
# 1. Create a test
TEST_ID=$(curl -X POST http://localhost:8080/api/tests \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Login Test",
    "steps": [
      {"action": "goto", "url": "https://example.com/login"},
      {"action": "fill", "selector": "#username", "value": "admin"},
      {"action": "fill", "selector": "#password", "value": "password"},
      {"action": "click", "selector": "#login-button"}
    ]
  }' | jq -r '.id')

# 2. Run the test
RUN_ID=$(curl -X POST http://localhost:8080/api/runs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"test_id\": \"$TEST_ID\",
    \"profile\": \"local\"
  }" | jq -r '.id')

# 3. Poll for completion
while true; do
  STATUS=$(curl -s http://localhost:8080/api/runs/$RUN_ID \
    -H "Authorization: Bearer $TOKEN" | jq -r '.status')
  echo "Status: $STATUS"
  [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ] && break
  sleep 2
done

# 4. Get results
curl http://localhost:8080/api/runs/$RUN_ID/result \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### Rate Limiting

API requests are rate-limited to prevent abuse:

- **Free tier**: 100 requests/hour
- **Team tier**: 1000 requests/hour
- **Enterprise**: Custom limits

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1634567890
```

---

## Tips and Best Practices

### Web UI

1. **Use Tags**: Organize tests with tags for easier filtering
2. **Share Links**: Use share links for PR reviews and bug reports
3. **Keyboard Shortcuts**: Learn keyboard shortcuts for faster navigation
4. **Save Filters**: Bookmark common filter combinations
5. **Watch Live**: Use real-time monitoring for long-running tests

### TUI

1. **Learn Vim Keys**: hjkl navigation is faster than arrows
2. **Use Search**: `/` to quickly find tests
3. **Multiple Terminals**: Run TUI alongside your editor
4. **Quick Actions**: Use number keys (1-6) to switch screens instantly

### CLI

1. **Exit Codes**: Check exit codes in scripts (`$?` in bash)
2. **Output Formats**: Use JSON/YAML for parsing in scripts
3. **Profiles**: Set up profiles for all your environments
4. **Aliases**: Create shell aliases for common commands

   ```bash
   alias uit="uitestflow run"
   alias uil="uitestflow profiles list"
   ```

### API

1. **API Keys**: Use API keys instead of tokens for long-running integrations
2. **Pagination**: Always use pagination for large result sets
3. **Webhooks**: Set up webhooks for real-time notifications
4. **Retry Logic**: Implement exponential backoff for retries
5. **Caching**: Cache test definitions to reduce API calls

---

## Troubleshooting

### Web UI Issues

**Server won't start**

```bash
# Check if port is already in use
lsof -i :8080

# Try a different port
uitestflow serve --port 8081
```

**Can't connect to database**

```bash
# Check database connection in docker-compose
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

### TUI Issues

**TUI doesn't display correctly**

```bash
# Check terminal compatibility
echo $TERM

# Try with different TERM
TERM=xterm-256color uitestflow tui

# Update Textual (once available)
pip install --upgrade textual
```

### API Issues

**401 Unauthorized**

- Check that your token hasn't expired
- Verify token is included in Authorization header
- Try generating a new token

**429 Too Many Requests**

- You've hit the rate limit
- Wait for the reset time (see X-RateLimit-Reset header)
- Upgrade to a higher tier for increased limits

**500 Internal Server Error**

- Check server logs: `docker-compose logs app`
- Verify database is running
- Check for configuration errors

---

## Next Steps

- **[Getting Started Guide](getting-started.md)** - Installation and setup
- **[Writing Tests](guides/writing-tests.md)** - Test authoring guide
- **[CI/CD Integration](guides/ci-cd-integration.md)** - Automation setup
- **[API Reference](api/rest-api.md)** - Complete API documentation

For more help, visit:

- **GitHub Issues**: <https://github.com/preset-io/ui-test-flow/issues>
- **Discussions**: <https://github.com/preset-io/ui-test-flow/discussions>
- **Documentation**: <https://docs.uitestflow.io> (coming soon)
