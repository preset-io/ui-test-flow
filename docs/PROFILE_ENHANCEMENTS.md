# Profile System Enhancements

## Overview

The UITestFlow profile system has been enhanced to support production-ready, mature automated web UI testing with multi-layered configurations, LLM integration, and flexible execution modes.

## Key Features

### 1. Multi-Layered Profile System

Profiles now support multiple categorization types:

- **Environment Profiles**: Dev, staging, prod with different URLs and auth
- **Workflow Profiles**: Pre-auth, authenticated, admin workflows
- **Custom Profiles**: User-defined custom configurations

### 2. Profile Types (`profile_type`)

```python
class ProfileType(str, Enum):
    ENVIRONMENT = "environment"  # dev, staging, prod
    WORKFLOW = "workflow"        # pre-auth, authenticated, admin
    CUSTOM = "custom"            # Custom configurations
```

### 3. Execution Modes (`execution_mode`)

```python
class ProfileExecutionMode(str, Enum):
    AUTOMATED = "automated"  # Ready for automated testing
    MANUAL = "manual"        # Ready for manual testing (headed mode, paused)
    HYBRID = "hybrid"        # Mix of automated + manual verification steps
```

**Use Cases**:

- `AUTOMATED`: Full CI/CD automation
- `MANUAL`: Manual QA verification (headed mode, browser visible, can pause for inspection)
- `HYBRID`: Automated tests with manual verification checkpoints (e.g., "verify dashboard looks correct")

### 4. Initialization Steps (`init_steps`)

Profiles can now define initialization steps that run before tests:

```json
{
  "init_steps": [
    {
      "name": "Navigate to login page",
      "action": "goto",
      "url": "https://app.example.com/login",
      "timeout": 30000,
      "critical": true
    },
    {
      "name": "Enter username",
      "action": "fill",
      "selector": "#username",
      "value": "${USERNAME}",
      "critical": true
    },
    {
      "name": "Enter password",
      "action": "fill",
      "selector": "#password",
      "value": "${PASSWORD}",
      "critical": true
    },
    {
      "name": "Click login button",
      "action": "click",
      "selector": "button[type='submit']",
      "wait_after": 2000,
      "critical": true
    },
    {
      "name": "Wait for dashboard",
      "action": "wait_for",
      "selector": ".dashboard-container",
      "timeout": 10000,
      "critical": true
    }
  ]
}
```

**Init Step Fields**:

- `name`: Human-readable step name
- `action`: ActionType (goto, click, fill, wait_for, etc.)
- `selector`: CSS/XPath selector
- `value`: Input value (supports environment variable substitution with `${VAR}`)
- `url`: URL for navigation steps
- `timeout`: Step-specific timeout (default: 30000ms)
- `wait_after`: Wait after step completes (milliseconds)
- `screenshot`: Capture screenshot after step
- `description`: Detailed step description
- `critical`: If true, profile initialization fails if this step fails
- `condition`: Conditional execution (e.g., 'element_visible(.login-button)')

### 5. LLM Configuration (`llm_config`)

Enhanced LLM configuration for test generation, selector healing, and error recovery:

```json
{
  "llm_config": {
    "enabled": true,
    "provider": "claude-code-cli",
    "model": "claude-sonnet-4-5",
    "api_key_env": "ANTHROPIC_API_KEY",
    "temperature": 0.0,
    "max_tokens": 4096,
    "timeout": 60,

    "cli_command": "claude",
    "cli_args": ["-p", "--dangerously-allow-all-tools"],

    "use_for_test_generation": true,
    "use_for_selector_healing": true,
    "use_for_error_recovery": true
  }
}
```

**Supported LLM Providers**:

```python
class LLMProvider(str, Enum):
    CLAUDE_CODE_CLI = "claude-code-cli"  # Claude Code CLI (default)
    CLAUDE_SDK = "claude-sdk"             # Claude Agent SDK
    CLAUDE_API = "claude-api"             # Direct Claude API
    OPENAI = "openai"                     # OpenAI API
    OLLAMA = "ollama"                     # Ollama local models
    CUSTOM = "custom"                      # Custom LLM endpoint
```

**LLM Features**:

- **Test Generation**: Generate tests from natural language descriptions
- **Selector Healing**: Auto-fix broken selectors when elements not found
- **Error Recovery**: Intelligent error recovery and retry strategies

### 6. Browser Configuration Enhancements

#### Browser Types

```python
class BrowserType(str, Enum):
    CHROMIUM = "chromium"  # Chromium (default, most stable for automation)
    CHROME = "chrome"       # Google Chrome (branded version)
    FIREFOX = "firefox"
    WEBKIT = "webkit"       # Safari/WebKit
```

#### Browser Frameworks

```python
class BrowserFramework(str, Enum):
    PLAYWRIGHT = "playwright"   # Default, recommended
    SELENIUM = "selenium"       # Future support
    PUPPETEER = "puppeteer"     # Future support
```

#### Device Emulation

Advanced device emulation for mobile/responsive testing:

```json
{
  "browser_config": {
    "browser_type": "chromium",
    "framework": "playwright",
    "headless": false,
    "device_emulation": {
      "device_name": "iPhone 12",
      "viewport": {"width": 390, "height": 844},
      "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) ...",
      "device_scale_factor": 3.0,
      "is_mobile": true,
      "has_touch": true,
      "locale": "en-US",
      "timezone": "America/Los_Angeles",
      "geolocation": {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "accuracy": 100
      },
      "permissions": ["geolocation", "notifications"]
    }
  }
}
```

**Predefined Devices**:

- iPhone 12, iPhone 12 Pro, iPhone 13, iPhone 14
- Pixel 5, Pixel 6, Pixel 7
- iPad Pro, iPad Air
- Galaxy S21, Galaxy S22
- Custom configurations

### 7. Profile Tags

Profiles can be tagged for organization and filtering:

```json
{
  "tags": ["production", "high-priority", "smoke-tests", "auth-required"]
}
```

## Complete Profile Example

### Example 1: Production Environment Profile

```json
{
  "name": "Production Environment",
  "description": "Production environment with full authentication",
  "profile_type": "environment",
  "execution_mode": "automated",
  "base_url": "https://app.production.com",
  "tags": ["production", "authenticated", "critical"],

  "init_steps": [
    {
      "name": "Navigate to login",
      "action": "goto",
      "url": "https://app.production.com/login",
      "critical": true
    },
    {
      "name": "Enter email",
      "action": "fill",
      "selector": "#email",
      "value": "${PROD_EMAIL}",
      "critical": true
    },
    {
      "name": "Enter password",
      "action": "fill",
      "selector": "#password",
      "value": "${PROD_PASSWORD}",
      "critical": true
    },
    {
      "name": "Submit login",
      "action": "click",
      "selector": "button[type='submit']",
      "wait_after": 2000,
      "critical": true
    },
    {
      "name": "Wait for workspace selector",
      "action": "wait_for",
      "selector": ".workspace-selector",
      "timeout": 10000,
      "critical": false
    },
    {
      "name": "Select default workspace",
      "action": "click",
      "selector": "[data-workspace='default']",
      "condition": "element_visible(.workspace-selector)",
      "critical": false
    }
  ],

  "auth_config": {
    "type": "form",
    "username": "${PROD_EMAIL}",
    "password": "${PROD_PASSWORD}"
  },

  "browser_config": {
    "browser_type": "chromium",
    "framework": "playwright",
    "headless": true,
    "viewport": {
      "width": 1920,
      "height": 1080
    },
    "record_video": true,
    "record_har": true,
    "ignore_https_errors": false
  },

  "llm_config": {
    "enabled": true,
    "provider": "claude-code-cli",
    "model": "claude-sonnet-4-5",
    "api_key_env": "ANTHROPIC_API_KEY",
    "cli_command": "claude",
    "cli_args": ["-p"],
    "use_for_test_generation": true,
    "use_for_selector_healing": true,
    "use_for_error_recovery": true
  }
}
```

### Example 2: Manual Testing Profile

```json
{
  "name": "Manual QA Verification",
  "description": "Headed mode for manual QA verification",
  "profile_type": "workflow",
  "execution_mode": "manual",
  "base_url": "https://staging.example.com",
  "tags": ["manual", "qa", "staging"],

  "browser_config": {
    "browser_type": "chrome",
    "framework": "playwright",
    "headless": false,
    "slowmo": 500,
    "viewport": {
      "width": 1920,
      "height": 1080
    }
  },

  "llm_config": {
    "enabled": false
  }
}
```

### Example 3: Mobile Device Testing Profile

```json
{
  "name": "Mobile - iPhone 12",
  "description": "iPhone 12 emulation for responsive testing",
  "profile_type": "environment",
  "execution_mode": "automated",
  "base_url": "https://app.example.com",
  "tags": ["mobile", "ios", "responsive"],

  "browser_config": {
    "browser_type": "chromium",
    "framework": "playwright",
    "headless": true,
    "device_emulation": {
      "device_name": "iPhone 12",
      "viewport": {"width": 390, "height": 844},
      "device_scale_factor": 3.0,
      "is_mobile": true,
      "has_touch": true,
      "locale": "en-US",
      "timezone": "America/Los_Angeles",
      "permissions": ["geolocation"]
    }
  }
}
```

## Profile Execution Flow

### 1. Automated Mode (`execution_mode: "automated"`)

```
1. Load profile configuration
2. Initialize browser with browser_config
3. Run init_steps (if defined)
   - If critical step fails: abort
   - If non-critical step fails: log warning, continue
4. Execute test(s)
5. Collect results
6. Close browser
7. Generate reports
```

### 2. Manual Mode (`execution_mode: "manual"`)

```
1. Load profile configuration
2. Initialize browser with browser_config (headless: false)
3. Run init_steps (if defined)
4. PAUSE - browser ready for manual testing
   - Browser window visible
   - Can manually interact
   - Can run individual tests
5. On demand: Execute tests
6. Manual verification points
7. Keep browser open until manually closed
```

### 3. Hybrid Mode (`execution_mode: "hybrid"`)

```
1. Load profile configuration
2. Initialize browser with browser_config
3. Run init_steps (if defined)
4. Execute automated test steps
5. PAUSE at manual verification points
   - Prompt user for verification
   - Capture screenshot
   - Wait for user confirmation
6. Continue automated execution
7. Repeat steps 4-6
8. Collect results
9. Generate reports
```

## Database Schema

The `profiles` table now includes:

```sql
CREATE TABLE profiles (
    id VARCHAR(100) PRIMARY KEY,
    org_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    profile_type VARCHAR(50) DEFAULT 'environment',  -- environment, workflow, custom
    execution_mode VARCHAR(50) DEFAULT 'automated',  -- automated, manual, hybrid
    base_url VARCHAR(500),
    init_steps JSON DEFAULT '[]'::JSON,              -- Initialization steps
    auth_config JSON DEFAULT '{}'::JSON,
    browser_config JSON DEFAULT '{}'::JSON,
    llm_config JSON DEFAULT '{}'::JSON,              -- LLM configuration
    notification_config JSON DEFAULT '{}'::JSON,
    tags JSON DEFAULT '[]'::JSON,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_profiles_profile_type ON profiles(profile_type);
CREATE INDEX idx_profiles_tags ON profiles USING GIN (CAST(tags AS jsonb));
```

## API Endpoints

### Create Profile

```http
POST /api/profiles
Content-Type: application/json

{
  "name": "Staging Environment",
  "description": "Staging with auth",
  "profile_type": "environment",
  "execution_mode": "automated",
  "base_url": "https://staging.example.com",
  "init_steps": [...],
  "auth_config": {...},
  "browser_config": {...},
  "llm_config": {...},
  "tags": ["staging", "automated"]
}
```

### Update Profile

```http
PUT /api/profiles/{profile_id}
Content-Type: application/json

{...same fields as create...}
```

### Get Profile

```http
GET /api/profiles/{profile_id}
```

### List Profiles

```http
GET /api/profiles
GET /api/profiles?profile_type=environment
GET /api/profiles?tags=production
```

### Delete Profile

```http
DELETE /api/profiles/{profile_id}
```

### Test Profile Connection

```http
POST /api/profiles/{profile_id}/test
```

### Start Profile (Execute Init Steps)

```http
POST /api/profiles/{profile_id}/start
Content-Type: application/json

{
  "execution_mode": "automated",  // Override profile's default
  "headless": false               // Override browser headless setting
}
```

## Best Practices

### 1. Environment Profiles

- Create separate profiles for dev, staging, prod
- Use environment variables for sensitive credentials (`${VAR_NAME}`)
- Tag with environment name for easy filtering

### 2. Workflow Profiles

- Create profiles for common workflows (login, checkout, admin)
- Use init_steps to set up the workflow state
- Mark critical init steps appropriately

### 3. Init Steps

- Keep init_steps focused on setup only
- Use `critical: true` for essential steps
- Use `critical: false` for optional setup (e.g., dismiss banners)
- Add `wait_after` for dynamic content

### 4. LLM Configuration

- Use Claude Code CLI for local development
- Use Claude SDK for production deployments
- Enable selector healing for flaky tests
- Disable LLM for performance-critical tests

### 5. Manual Testing

- Use `execution_mode: "manual"` for QA verification
- Set `headless: false` and `slowmo: 500` for visibility
- Keep browser open for inspection

### 6. Device Emulation

- Test responsive designs with device emulation
- Use predefined devices for consistency
- Test geolocation features with geolocation config
- Grant necessary permissions (geolocation, notifications)

## Migration

To migrate existing profiles to the new schema, run:

```bash
PGPASSWORD='uitest' psql -h localhost -U uitest -d uitestflow -f migrations/001_add_profile_enhancements.sql
```

Existing profiles will automatically get default values:

- `profile_type`: "environment"
- `execution_mode`: "automated"
- `init_steps`: []
- `llm_config`: {}
- `tags`: []

## Future Enhancements

- Profile inheritance (child profiles extend parent)
- Profile templates (quick-start templates)
- Profile scheduling (run profiles on schedule)
- Profile chaining (run multiple profiles in sequence)
- Profile comparison (diff two profiles)
- Profile version control (track profile changes)
- Profile sharing (export/import profiles)
- MCP integration (profiles as MCP resources)
