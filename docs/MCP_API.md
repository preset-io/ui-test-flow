# UITestFlow MCP API Reference

Complete API reference for MCP-powered test generation and execution endpoints.

## Table of Contents

1. [Authentication](#authentication)
2. [Endpoints](#endpoints)
3. [Request/Response Models](#requestresponse-models)
4. [WebSocket Protocol](#websocket-protocol)
5. [Error Codes](#error-codes)
6. [Rate Limiting](#rate-limiting)
7. [Examples](#examples)

## Authentication

All API requests require authentication using Bearer tokens.

### Obtaining a Token

```http
POST /api/auth/token
Content-Type: application/json

{
  "username": "your-username",
  "password": "your-password"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Using the Token

Include in Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Endpoints

### Generate Test

Generate a test definition from natural language description.

```http
POST /api/mcp/generate
```

**Request Body:**

```json
{
  "description": "Login with admin credentials and verify dashboard loads",
  "base_url": "http://example.com",
  "model": "claude-3-5-haiku-20241022",
  "temperature": 0.3,
  "include_metadata": true,
  "auto_save": false,
  "tags": ["authentication", "smoke-test"]
}
```

**Parameters:**

- `description` (string, required): Natural language test description
- `base_url` (string, optional): Base URL for the test
- `model` (string, optional): Claude model to use (default: haiku)
- `temperature` (float, optional): 0.0-1.0 (default: 0.3)
- `include_metadata` (boolean, optional): Include MCPMetadata (default: true)
- `auto_save` (boolean, optional): Save to file automatically (default: false)
- `tags` (array[string], optional): Tags to add to test

**Response: 200 OK**

```json
{
  "test_id": "550e8400-e29b-41d4-a716-446655440000",
  "test_definition": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "login_test",
    "version": "1.0",
    "description": "Test login functionality with admin credentials",
    "url": "http://example.com",
    "steps": [
      {
        "name": "Navigate to login page",
        "action": "goto",
        "url": "http://example.com/login",
        "timeout": 30000
      },
      {
        "name": "Fill username",
        "action": "fill",
        "selector": "input[name='username']",
        "value": "admin"
      }
    ],
    "evaluators": [
      {
        "name": "all_steps_completed",
        "type": "all_steps_completed",
        "required": true,
        "weight": 1.0
      }
    ],
    "mcp_metadata": {
      "generated_by": "claude",
      "generation_model": "claude-3-5-haiku-20241022",
      "generation_timestamp": "2024-01-15T10:30:00Z",
      "generation_prompt": "Login with admin credentials...",
      "generation_temperature": 0.3,
      "tokens_used": 1247
    },
    "created_at": "2024-01-15T10:30:00Z"
  },
  "file_path": null
}
```

**Response: 400 Bad Request**

```json
{
  "error": "validation_error",
  "message": "Invalid request parameters",
  "details": {
    "temperature": "Must be between 0.0 and 1.0"
  }
}
```

---

### Execute Test

Execute a test with optional Claude guidance.

```http
POST /api/mcp/execute
```

**Request Body:**

```json
{
  "test_id": "550e8400-e29b-41d4-a716-446655440000",
  "with_claude": true,
  "guidance_level": "standard",
  "profile": "staging",
  "browser_config": {
    "headless": true,
    "browser_type": "chromium"
  }
}
```

**Parameters:**

- `test_id` (string, required): UUID of test to execute
- `test_definition` (object, optional): Inline test definition (alternative to test_id)
- `with_claude` (boolean, optional): Enable guided execution (default: false)
- `guidance_level` (string, optional): minimal/standard/verbose (default: standard)
- `profile` (string, optional): Profile to use for execution
- `browser_config` (object, optional): Override browser configuration

**Response: 202 Accepted**

```json
{
  "run_id": "660e8400-e29b-41d4-a716-446655440000",
  "test_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "created_at": "2024-01-15T10:35:00Z",
  "websocket_url": "ws://localhost:8018/ws/mcp/execute/660e8400-e29b-41d4-a716-446655440000"
}
```

---

### Get Execution Status

Get current status of a test execution.

```http
GET /api/mcp/execute/{run_id}
```

**Response: 200 OK**

```json
{
  "run_id": "660e8400-e29b-41d4-a716-446655440000",
  "test_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "started_at": "2024-01-15T10:35:05Z",
  "current_step": 3,
  "total_steps": 8,
  "progress_percent": 37.5
}
```

**Status Values:**

- `queued`: Waiting to start
- `running`: Currently executing
- `completed`: Finished successfully
- `failed`: Finished with errors
- `aborted`: Cancelled by user

---

### Get Claude Feedback

Get Claude's guidance and feedback for a test run.

```http
GET /api/mcp/feedback/{run_id}
```

**Query Parameters:**

- `page` (integer, optional): Page number (default: 1)
- `page_size` (integer, optional): Results per page (default: 50)

**Response: 200 OK**

```json
{
  "run_id": "660e8400-e29b-41d4-a716-446655440000",
  "test_name": "login_test",
  "completed_at": "2024-01-15T10:35:30Z",
  "total_steps": 8,
  "steps": [
    {
      "step_index": 0,
      "step_name": "Navigate to login page",
      "success": true,
      "duration_ms": 1200,
      "claude_guidance": "Page loaded successfully. Login form is visible.",
      "page_state": {
        "url": "http://example.com/login",
        "title": "Login - Example App",
        "console_errors": []
      }
    },
    {
      "step_index": 1,
      "step_name": "Fill username",
      "success": true,
      "duration_ms": 250,
      "claude_guidance": "Username field filled correctly.",
      "adapted_selector": null
    },
    {
      "step_index": 2,
      "step_name": "Click login button",
      "success": true,
      "duration_ms": 800,
      "claude_guidance": "Button clicked. Waiting for navigation.",
      "adapted_selector": "button[type='submit']",
      "adaptation_reason": "Original selector '.login-btn' not found. Used semantic alternative."
    }
  ],
  "summary": {
    "total_guidance_requests": 8,
    "total_adaptations": 1,
    "total_recoveries": 0,
    "guidance_latency_avg_ms": 450
  },
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_pages": 1,
    "total_items": 8
  }
}
```

---

### Get MCP Status

Get MCP server and feature status.

```http
GET /api/mcp/status
```

**Response: 200 OK**

```json
{
  "mcp_enabled": true,
  "mcp_server": {
    "running": true,
    "transport": "http",
    "host": "localhost",
    "port": 3001,
    "uptime_seconds": 3600
  },
  "claude": {
    "enabled": true,
    "model": "claude-3-5-haiku-20241022",
    "api_key_configured": true,
    "last_request_at": "2024-01-15T10:35:00Z"
  },
  "features": {
    "generation_enabled": true,
    "guided_execution_enabled": true,
    "selector_adaptation_enabled": true,
    "error_recovery_enabled": true
  },
  "tools": [
    {
      "name": "navigate",
      "description": "Navigate to a URL"
    },
    {
      "name": "click",
      "description": "Click an element"
    }
  ],
  "health": "healthy"
}
```

---

### Cancel Execution

Cancel a running test execution.

```http
POST /api/mcp/execute/{run_id}/cancel
```

**Response: 200 OK**

```json
{
  "run_id": "660e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled",
  "message": "Test execution cancelled successfully"
}
```

---

## Request/Response Models

### TestGenerationRequest

```typescript
{
  description: string;           // Required
  base_url?: string;
  model?: string;               // Default: "claude-3-5-haiku-20241022"
  temperature?: number;         // Default: 0.3
  max_tokens?: number;          // Default: 4096
  include_metadata?: boolean;   // Default: true
  auto_save?: boolean;          // Default: false
  output_path?: string;
  tags?: string[];
}
```

### TestExecutionRequest

```typescript
{
  test_id?: string;             // Required if no test_definition
  test_definition?: object;     // Required if no test_id
  with_claude?: boolean;        // Default: false
  guidance_level?: "minimal" | "standard" | "verbose";  // Default: "standard"
  profile?: string;
  browser_config?: {
    headless?: boolean;
    browser_type?: "chromium" | "firefox" | "webkit";
    viewport?: {
      width: number;
      height: number;
    };
  };
}
```

### TestDefinition

```typescript
{
  id: string;
  name: string;
  version: string;
  description?: string;
  url?: string;
  steps: TestStep[];
  evaluators: Evaluator[];
  browser_config?: BrowserConfig;
  auth_config?: AuthConfig;
  mcp_metadata?: MCPMetadata;
  llm_config?: LLMConfig;
  created_at: string;
  updated_at: string;
}
```

### TestStep

```typescript
{
  name: string;
  action: string;
  selector?: string;
  value?: any;
  url?: string;
  timeout?: number;
  screenshot?: boolean;
  description?: string;
  wait_before?: number;
  wait_after?: number;
}
```

### MCPMetadata

```typescript
{
  generated_by: "claude" | "mcp";
  generation_model: string;
  generation_timestamp: string;
  generation_prompt: string;
  generation_temperature: number;
  tokens_used?: number;
  generation_config?: object;
}
```

---

## WebSocket Protocol

Connect to WebSocket for real-time execution updates.

### Connection

```javascript
const ws = new WebSocket(
  `ws://localhost:8018/ws/mcp/execute/${runId}?token=${authToken}`
);
```

### Message Types

**step_started**

```json
{
  "type": "step_started",
  "run_id": "660e8400-e29b-41d4-a716-446655440000",
  "step_index": 2,
  "step_name": "Click login button",
  "timestamp": "2024-01-15T10:35:10Z"
}
```

**claude_guidance**

```json
{
  "type": "claude_guidance",
  "run_id": "660e8400-e29b-41d4-a716-446655440000",
  "step_index": 2,
  "guidance": "Button clicked successfully. Waiting for navigation.",
  "detail_level": "standard",
  "timestamp": "2024-01-15T10:35:11Z"
}
```

**selector_adapted**

```json
{
  "type": "selector_adapted",
  "run_id": "660e8400-e29b-41d4-a716-446655440000",
  "step_index": 2,
  "original_selector": ".login-btn",
  "adapted_selector": "button[type='submit']",
  "reason": "Original selector not found. Using semantic alternative.",
  "timestamp": "2024-01-15T10:35:11Z"
}
```

**screenshot_captured**

```json
{
  "type": "screenshot_captured",
  "run_id": "660e8400-e29b-41d4-a716-446655440000",
  "step_index": 2,
  "screenshot_url": "/api/runs/660e8400.../screenshots/step_2.png",
  "timestamp": "2024-01-15T10:35:12Z"
}
```

**step_completed**

```json
{
  "type": "step_completed",
  "run_id": "660e8400-e29b-41d4-a716-446655440000",
  "step_index": 2,
  "step_name": "Click login button",
  "success": true,
  "duration_ms": 800,
  "timestamp": "2024-01-15T10:35:12Z"
}
```

**error_recovery**

```json
{
  "type": "error_recovery",
  "run_id": "660e8400-e29b-41d4-a716-446655440000",
  "step_index": 3,
  "error": "Element not visible",
  "recovery_action": "Wait additional 2 seconds",
  "recovery_success": true,
  "timestamp": "2024-01-15T10:35:15Z"
}
```

**test_completed**

```json
{
  "type": "test_completed",
  "run_id": "660e8400-e29b-41d4-a716-446655440000",
  "passed": true,
  "duration_ms": 15000,
  "steps_executed": 8,
  "steps_passed": 8,
  "steps_failed": 0,
  "timestamp": "2024-01-15T10:35:25Z"
}
```

---

## Error Codes

### HTTP Status Codes

- `200 OK`: Request successful
- `202 Accepted`: Request accepted, processing asynchronously
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `502 Bad Gateway`: Claude API error
- `503 Service Unavailable`: MCP server unavailable
- `504 Gateway Timeout`: Request timeout

### Error Response Format

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional context"
  },
  "error_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-01-15T10:35:00Z"
}
```

### Common Error Codes

- `validation_error`: Invalid request parameters
- `authentication_failed`: Invalid credentials
- `api_key_missing`: Anthropic API key not configured
- `api_key_invalid`: Invalid Anthropic API key
- `rate_limit_exceeded`: Too many requests
- `claude_api_error`: Claude API returned an error
- `mcp_server_unavailable`: MCP server not running
- `test_not_found`: Test ID not found
- `run_not_found`: Run ID not found
- `generation_failed`: Test generation failed
- `execution_failed`: Test execution failed
- `timeout`: Request timed out

---

## Rate Limiting

### Limits

- **Generation**: 10 requests per minute
- **Execution**: 5 concurrent executions
- **Feedback**: 100 requests per minute
- **Status**: 100 requests per minute

### Rate Limit Headers

```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1642248600
```

### Rate Limit Response

```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Please try again later.",
  "retry_after": 42,
  "limit": 10,
  "window_seconds": 60
}
```

---

## Examples

### Python Client

```python
import httpx
import asyncio

class MCPClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def generate_test(self, description: str, **kwargs):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/mcp/generate",
                json={"description": description, **kwargs},
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def execute_test(self, test_id: str, with_claude: bool = True):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/mcp/execute",
                json={"test_id": test_id, "with_claude": with_claude},
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def get_feedback(self, run_id: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/mcp/feedback/{run_id}",
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()


# Usage
async def main():
    client = MCPClient("http://localhost:8018", "your-api-key")

    # Generate test
    result = await client.generate_test(
        "Login with admin/password123 and verify dashboard"
    )
    test_id = result["test_id"]

    # Execute test
    execution = await client.execute_test(test_id, with_claude=True)
    run_id = execution["run_id"]

    # Wait for completion (simplified)
    await asyncio.sleep(10)

    # Get feedback
    feedback = await client.get_feedback(run_id)
    print(f"Test {'passed' if feedback['passed'] else 'failed'}")

asyncio.run(main())
```

### JavaScript/TypeScript Client

```typescript
class MCPClient {
  constructor(private baseUrl: string, private apiKey: string) {}

  async generateTest(description: string, options = {}) {
    const response = await fetch(`${this.baseUrl}/api/mcp/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify({ description, ...options }),
    });

    if (!response.ok) throw new Error('Generation failed');
    return response.json();
  }

  async executeTest(testId: string, withClaude = true) {
    const response = await fetch(`${this.baseUrl}/api/mcp/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify({ test_id: testId, with_claude: withClaude }),
    });

    if (!response.ok) throw new Error('Execution failed');
    return response.json();
  }

  streamExecution(runId: string, onMessage: (data: any) => void) {
    const ws = new WebSocket(
      `ws://${this.baseUrl}/ws/mcp/execute/${runId}?token=${this.apiKey}`
    );

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    return ws;
  }
}

// Usage
const client = new MCPClient('localhost:8018', 'your-api-key');

const result = await client.generateTest('Login test');
const execution = await client.executeTest(result.test_id);

const ws = client.streamExecution(execution.run_id, (data) => {
  console.log(`Event: ${data.type}`, data);
});
```

---

For more examples and detailed guides, see [MCP_GUIDE.md](./MCP_GUIDE.md).
