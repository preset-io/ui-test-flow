# UITestFlow MCP Integration Guide

Complete guide to using Model Context Protocol (MCP) with Claude for intelligent test generation and execution.

## Table of Contents

1. [Overview](#overview)
2. [Installation & Setup](#installation--setup)
3. [Quick Start](#quick-start)
4. [Test Generation](#test-generation)
5. [Guided Execution](#guided-execution)
6. [CLI Usage](#cli-usage)
7. [API Usage](#api-usage)
8. [Configuration](#configuration)
9. [Advanced Features](#advanced-features)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)

## Overview

### What is MCP Integration?

UITestFlow integrates with Anthropic's Model Context Protocol (MCP) to enable:

- **Natural Language Test Generation**: Describe your test in plain English, get a complete test definition
- **Intelligent Selector Adaptation**: Claude suggests alternative selectors when elements aren't found
- **Error Recovery**: Automatic recovery from test failures with Claude's guidance
- **Step Validation**: Real-time validation of test steps with page state analysis

### Architecture

```
┌─────────────────┐
│  UITestFlow CLI │
│   or API        │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Claude Client (Anthropic API)     │
│   • Test generation                 │
│   • Guidance during execution       │
└────────┬───────────────┬────────────┘
         │               │
         ▼               ▼
┌─────────────────┐  ┌──────────────────┐
│  MCP Playwright │  │  Test Runner     │
│  Server         │  │  • Step execution│
│  • Browser      │  │  • Page state    │
│    automation   │  │  • Screenshots   │
│  • Tools        │  └──────────────────┘
└─────────────────┘
```

### Benefits

- **Faster Test Creation**: Write tests in natural language instead of code
- **More Robust Tests**: Adaptive selectors reduce flakiness
- **Better Debugging**: Claude provides context-aware error messages
- **Lower Maintenance**: Auto-recovery from common failures

## Installation & Setup

### Prerequisites

- Python 3.11 or higher
- UITestFlow installed (`pip install uitestflow`)
- Anthropic API key

### Get Your API Key

1. Go to <https://console.anthropic.com/settings/keys>
2. Create a new API key
3. Save it securely

### Configure API Key

**Option 1: Environment Variable (Recommended)**

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Add to your shell profile (`.bashrc`, `.zshrc`, etc.) for persistence.

**Option 2: .env File**

```bash
# Copy example file
cp .env.mcp.example .env

# Edit and add your key
echo "ANTHROPIC_API_KEY=your-api-key-here" >> .env
```

**Option 3: Configuration File**

```yaml
# .uitest_profiles.yaml
default: local

profiles:
  local:
    anthropic_api_key: "your-api-key-here"
    # ... other settings
```

### Enable MCP Features

```bash
# In your .env file
UITESTFLOW_MCP_ENABLED=true
UITESTFLOW_MCP_CLAUDE_ENABLED=true
UITESTFLOW_MCP_GENERATION_ENABLED=true
UITESTFLOW_MCP_GUIDED_EXECUTION_ENABLED=true
```

### Verify Installation

```bash
uitestflow config validate
```

Expected output:

```
✓ Configuration valid
✓ MCP features enabled
✓ Claude API key configured
✓ MCP server available
```

## Quick Start

### Generate Your First Test

```bash
uitestflow generate "Login to http://example.com with admin/password123" \
  --output login_test.yaml
```

This creates a complete test file:

```yaml
version: "1.0"
name: "login_test"
steps:
  - name: "Navigate to login page"
    action: "goto"
    url: "http://example.com/login"
  - name: "Fill username"
    action: "fill"
    selector: 'input[name="username"]'
    value: "admin"
  # ... more steps
```

### Run the Test

```bash
uitestflow run login_test.yaml
```

### Run with Claude Guidance

```bash
uitestflow run login_test.yaml --with-claude
```

This enables:

- Real-time selector adaptation
- Error recovery
- Step validation
- Enhanced logging

## Test Generation

### Basic Generation

```bash
uitestflow generate "DESCRIPTION" --output FILE
```

**Example: Simple Form**

```bash
uitestflow generate "Fill out contact form with name 'John', email 'john@example.com', submit" \
  --output contact_form.yaml \
  --base-url "http://example.com"
```

### Generation Options

```bash
uitestflow generate "DESCRIPTION" \
  --output FILE              # Output file path
  --base-url URL             # Base URL for test
  --model MODEL              # Claude model (haiku/sonnet/opus)
  --temperature TEMP         # Creativity (0.0-1.0)
  --dry-run                  # Preview without saving
  --verbose                  # Show generation details
```

### Model Selection

**claude-3-5-haiku-20241022** (Default, Recommended)

- Fastest generation
- Most cost-effective
- Great for simple to moderate complexity tests

**claude-3-5-sonnet-20241022**

- Balanced performance
- Better for complex multi-step workflows
- More detailed evaluators

**claude-3-opus-20240229**

- Most capable
- Best for complex scenarios with many edge cases
- Highest cost

```bash
# Use Haiku for simple tests
uitestflow generate "Login test" --model claude-3-5-haiku-20241022

# Use Sonnet for complex workflows
uitestflow generate "Complete checkout flow with multiple items" \
  --model claude-3-5-sonnet-20241022
```

### Temperature Control

Temperature affects creativity and variability:

- **0.0-0.3**: Deterministic, consistent (recommended for tests)
- **0.3-0.5**: Slightly varied, balanced
- **0.5-1.0**: Creative, more varied (not recommended for tests)

```bash
# Deterministic generation
uitestflow generate "Login test" --temperature 0.2

# More creative (use cautiously)
uitestflow generate "Explore dashboard features" --temperature 0.5
```

### Writing Good Descriptions

**Be Specific**

```
❌ "Test the login"
✅ "Navigate to /login, fill username 'admin' and password 'pass123', click submit, verify dashboard loads"
```

**Include Expected Outcomes**

```
❌ "Search for products"
✅ "Search for 'laptop', verify at least 5 results appear, click first result"
```

**Mention Important Selectors**

```
❌ "Click the button"
✅ "Click the submit button with data-testid='submit-btn'"
```

**Describe User Flow**

```
❌ "Test checkout"
✅ "Add item to cart, go to checkout, fill shipping info, select payment method, complete order"
```

### Examples by Scenario

**Login Test**

```bash
uitestflow generate "Navigate to login page, fill username and password from config, click login button, wait for dashboard to load" \
  --output tests/login.yaml
```

**Form Submission**

```bash
uitestflow generate "Fill registration form with firstName, lastName, email, password, confirmPassword, accept terms checkbox, submit, verify success message" \
  --output tests/registration.yaml
```

**Search and Filter**

```bash
uitestflow generate "Search for 'wireless mouse', apply price filter $20-$50, apply brand filter 'Logitech', verify results update, click first result" \
  --output tests/search.yaml
```

**Multi-Page Navigation**

```bash
uitestflow generate "Login, navigate to Settings, change notification preferences, save, verify success message, navigate back to dashboard" \
  --output tests/settings.yaml
```

## Guided Execution

### Enable Guided Execution

```bash
uitestflow run test.yaml --with-claude
```

### What Happens During Guided Execution?

For each test step:

1. **Pre-Step Analysis**
   - Captures current page state (URL, title, console logs)
   - Sends to Claude for context

2. **Step Execution**
   - Executes the step normally
   - If selector fails, requests alternatives from Claude

3. **Post-Step Validation**
   - Claude validates the step completed successfully
   - Checks for unexpected page changes or errors

4. **Error Recovery** (if step fails)
   - Sends error and page state to Claude
   - Claude suggests recovery actions
   - Attempts recovery automatically

### Selector Adaptation

When a selector doesn't work, Claude suggests alternatives:

```
Original selector: button.submit
  ❌ Failed: Element not found

Claude suggestions:
  1. button[type="submit"]
  2. input[type="submit"]
  3. .btn-primary

Trying alternative 1...
  ✅ Success: button[type="submit"]
```

The working selector is saved for future runs.

### Error Recovery Examples

**Timing Issues**

```
Error: Element not visible yet
Recovery: Wait additional 2 seconds
Result: ✅ Element now visible, continuing
```

**Navigation**

```
Error: Unexpected redirect to /confirm
Recovery: Accept the redirect, continue test
Result: ✅ Adapted to new flow
```

**Form Validation**

```
Error: Form validation error appeared
Recovery: Clear the field and re-enter value
Result: ✅ Validation passed
```

### Configuration

Control guidance behavior in `.env`:

```bash
# Detail level: minimal, standard, verbose
UITESTFLOW_MCP_GUIDANCE_DETAIL_LEVEL=standard

# Max retries per step
UITESTFLOW_MCP_GUIDANCE_MAX_RETRIES=3

# Timeout for guidance requests
UITESTFLOW_MCP_GUIDANCE_TIMEOUT=30

# Enable selector adaptation
UITESTFLOW_MCP_SELECTOR_ADAPTATION_ENABLED=true
UITESTFLOW_MCP_SELECTOR_MAX_ALTERNATIVES=3

# Enable error recovery
UITESTFLOW_MCP_ERROR_RECOVERY_ENABLED=true
UITESTFLOW_MCP_ERROR_RECOVERY_MAX_ATTEMPTS=2
```

## CLI Usage

### Generate Command

```bash
uitestflow generate DESCRIPTION [OPTIONS]
```

**Options:**

- `--output FILE`: Save to file (default: stdout)
- `--base-url URL`: Base URL for test
- `--model MODEL`: Claude model to use
- `--temperature FLOAT`: Generation temperature (0.0-1.0)
- `--dry-run`: Show preview without saving
- `--verbose`: Show detailed generation info

### Run with Claude

```bash
uitestflow run TEST_FILE [OPTIONS]
```

**Options:**

- `--with-claude`: Enable guided execution
- `--model MODEL`: Claude model for guidance
- `--no-guidance`: Disable guidance for this run
- `--guided-only`: Show guidance without execution (dry run)

### MCP Server Command

```bash
uitestflow mcp-server [OPTIONS]
```

**Options:**

- `--port PORT`: Server port (default: 3001)
- `--transport TYPE`: stdio or http (default: stdio)
- `--headless / --headed`: Browser mode

### MCP Status Command

```bash
uitestflow mcp-status
```

Shows:

- MCP server status
- Available tools
- Connected browsers
- Configuration
- Health check

## API Usage

### Generate Test via API

```python
import httpx

async def generate_test():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8018/api/mcp/generate",
            json={
                "description": "Login with admin credentials",
                "base_url": "http://example.com",
                "model": "claude-3-5-haiku-20241022",
                "temperature": 0.3,
            },
            headers={"Authorization": f"Bearer {api_key}"}
        )

        data = response.json()
        test_id = data["test_id"]
        test_definition = data["test_definition"]

        return test_id, test_definition
```

### Execute with Guidance

```python
async def execute_test(test_id):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8018/api/mcp/execute",
            json={
                "test_id": test_id,
                "with_claude": True,
                "guidance_level": "standard",
            },
            headers={"Authorization": f"Bearer {api_key}"}
        )

        run_id = response.json()["run_id"]
        return run_id
```

### Stream Results via WebSocket

```python
import asyncio
import websockets

async def stream_execution(run_id):
    uri = f"ws://localhost:8018/ws/mcp/execute/{run_id}?token={api_key}"

    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)

            if data["type"] == "step_started":
                print(f"Starting: {data['step_name']}")

            elif data["type"] == "claude_guidance":
                print(f"Guidance: {data['guidance']}")

            elif data["type"] == "step_completed":
                print(f"Completed: {data['step_name']} - {data['success']}")

            elif data["type"] == "test_completed":
                print(f"Test finished: {data['passed']}")
                break
```

### Get Feedback

```python
async def get_feedback(run_id):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8018/api/mcp/feedback/{run_id}",
            headers={"Authorization": f"Bearer {api_key}"}
        )

        feedback = response.json()

        for step in feedback["steps"]:
            print(f"Step: {step['name']}")
            if step.get("claude_guidance"):
                print(f"  Guidance: {step['claude_guidance']}")
            if step.get("adapted_selector"):
                print(f"  Used selector: {step['adapted_selector']}")
```

## Configuration

### Environment Variables

See `.env.mcp.example` for complete list. Key variables:

```bash
# Enable MCP features
UITESTFLOW_MCP_ENABLED=true

# API key
ANTHROPIC_API_KEY=your-key-here

# Model settings
UITESTFLOW_MCP_CLAUDE_MODEL=claude-3-5-haiku-20241022
UITESTFLOW_MCP_CLAUDE_TEMPERATURE=0.3

# Guidance settings
UITESTFLOW_MCP_GUIDANCE_DETAIL_LEVEL=standard
UITESTFLOW_MCP_GUIDANCE_MAX_RETRIES=3

# Features
UITESTFLOW_MCP_SELECTOR_ADAPTATION_ENABLED=true
UITESTFLOW_MCP_ERROR_RECOVERY_ENABLED=true
```

### Configuration Hierarchy

1. **CLI arguments** (highest priority)
2. **Environment variables**
3. **`.env` file**
4. **Profile configuration**
5. **Default values** (lowest priority)

Example:

```bash
# .env sets model to haiku
UITESTFLOW_MCP_CLAUDE_MODEL=claude-3-5-haiku-20241022

# CLI overrides to sonnet
uitestflow generate "test" --model claude-3-5-sonnet-20241022
```

### Profile Configuration

```yaml
# .uitest_profiles.yaml
profiles:
  production:
    mcp:
      enabled: true
      claude_model: claude-3-5-haiku-20241022
      guidance_enabled: true
      guidance_level: minimal
```

## Advanced Features

### Custom Prompts

Customize test generation prompts:

```python
from uitestflow.llm.prompts import TestGenerationPrompt

custom_prompt = TestGenerationPrompt(
    system="You are a QA engineer specializing in e-commerce tests...",
    user_template="Generate a test for: {description}...",
)

generator = ClaudeTestGenerator(prompt=custom_prompt)
```

### Batch Generation

Generate multiple tests:

```python
descriptions = [
    "Login test",
    "Registration test",
    "Password reset test",
]

async def batch_generate():
    generator = ClaudeTestGenerator()

    tasks = [
        generator.generate_test(desc)
        for desc in descriptions
    ]

    tests = await asyncio.gather(*tasks)
    return tests
```

### Cache Configuration

Reduce API calls by caching responses:

```bash
UITESTFLOW_MCP_CACHE_RESPONSES=true
UITESTFLOW_MCP_CACHE_TTL_SECONDS=3600
```

### Page State Capture

Control what data is sent to Claude:

```bash
# Include console logs (recommended)
UITESTFLOW_MCP_PAGE_STATE_CAPTURE_CONSOLE=true

# Include cookies (may contain sensitive data)
UITESTFLOW_MCP_PAGE_STATE_CAPTURE_COOKIES=false

# Include localStorage (may contain sensitive data)
UITESTFLOW_MCP_PAGE_STATE_CAPTURE_STORAGE=false
```

## Troubleshooting

### API Key Issues

**Problem**: "Invalid API key"

**Solution**:

```bash
# Verify key is set
echo $ANTHROPIC_API_KEY

# Test key directly
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

### Generation Failures

**Problem**: Test generation fails or produces invalid YAML

**Solutions**:

1. Check your description is clear and specific
2. Try a different model (Sonnet instead of Haiku)
3. Increase timeout: `UITESTFLOW_MCP_CLAUDE_TIMEOUT=120`
4. Enable verbose logging: `UITESTFLOW_MCP_LOG_LEVEL=DEBUG`

### Guidance Timeout

**Problem**: Guidance requests timeout during execution

**Solutions**:

1. Increase timeout: `UITESTFLOW_MCP_GUIDANCE_TIMEOUT=60`
2. Reduce detail level: `UITESTFLOW_MCP_GUIDANCE_DETAIL_LEVEL=minimal`
3. Disable guidance for specific steps in YAML:

   ```yaml
   steps:
     - name: "Fast step"
       action: "click"
       selector: "button"
       llm_config:
         enabled: false
   ```

### Selector Adaptation Not Working

**Problem**: Selector adaptation doesn't find alternatives

**Solutions**:

1. Ensure feature is enabled: `UITESTFLOW_MCP_SELECTOR_ADAPTATION_ENABLED=true`
2. Increase alternatives: `UITESTFLOW_MCP_SELECTOR_MAX_ALTERNATIVES=5`
3. Provide better initial selector (use data-testid attributes)
4. Check page state is being captured properly

### Rate Limiting

**Problem**: "Rate limit exceeded" errors

**Solutions**:

1. Enable response caching: `UITESTFLOW_MCP_CACHE_RESPONSES=true`
2. Reduce guidance frequency (use minimal detail level)
3. Batch requests: `UITESTFLOW_MCP_BATCH_REQUESTS=true`
4. Upgrade Anthropic API plan

## Best Practices

### Test Generation

1. **Be Specific**: Clear descriptions produce better tests
2. **Use Haiku**: Fastest and most cost-effective for most tests
3. **Include Expected Outcomes**: Help Claude understand success criteria
4. **Mention Data-TestID**: If your app uses test IDs, mention them
5. **Review Generated Tests**: Always review before committing

### Guided Execution

1. **Start with Standard Level**: Adjust based on results
2. **Use for Complex Tests**: Simple tests don't need guidance
3. **Monitor Costs**: Guidance adds API calls
4. **Enable Caching**: Reuse responses for identical scenarios
5. **Log Everything**: Keep logs for debugging

### Selector Strategy

1. **Prefer Stable Selectors**: data-testid > id > class > xpath
2. **Let Claude Adapt**: Don't over-specify selectors
3. **Review Adaptations**: Check what selectors Claude chose
4. **Update Tests**: Use adapted selectors in future versions

### Security

1. **Protect API Keys**: Never commit keys to git
2. **Use Environment Variables**: Keep keys in .env
3. **Limit Page State**: Don't send cookies/storage unless needed
4. **Review Generated Tests**: Check for hardcoded secrets
5. **Rotate Keys**: Regularly rotate API keys

### Performance

1. **Cache Responses**: Enable caching for repeated scenarios
2. **Use Haiku**: Faster and cheaper than Sonnet/Opus
3. **Batch When Possible**: Generate multiple tests together
4. **Disable for Simple Steps**: Skip guidance for trivial actions
5. **Monitor Usage**: Track API calls and costs

### Maintenance

1. **Version Tests**: Track when tests were generated
2. **Update Prompts**: Refine prompts based on results
3. **Monitor Failures**: Look for patterns in adapted selectors
4. **Keep MCP Updated**: Update to latest version
5. **Document Quirks**: Note app-specific guidance needs

---

## Additional Resources

- [MCP API Reference](./MCP_API.md)
- [UITestFlow Documentation](../README.md)
- [Anthropic API Docs](https://docs.anthropic.com)
- [Model Context Protocol](https://modelcontextprotocol.io)

## Support

- GitHub Issues: <https://github.com/preset-io/ui-test-flow/issues>
- Discussions: <https://github.com/preset-io/ui-test-flow/discussions>
- Email: <support@preset.io>
