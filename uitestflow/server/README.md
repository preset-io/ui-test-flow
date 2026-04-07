# UITestFlow Server

FastAPI backend for the UITestFlow web UI, providing REST API and WebSocket support for test management and execution.

## Architecture

```
server/
├── api.py              # Main FastAPI application
├── database.py         # SQLAlchemy models and session management
├── auth.py            # JWT authentication and authorization
├── websocket.py       # WebSocket connection management
├── schemas.py         # Pydantic request/response models
└── routes/
    ├── auth.py        # Authentication endpoints
    ├── tests.py       # Test CRUD operations
    ├── runs.py        # Test run management
    ├── profiles.py    # Profile management
    └── analytics.py   # Statistics and trends
```

## Features

- **Async/Await**: Full async support with SQLAlchemy 2.0+ and asyncpg
- **JWT Authentication**: Secure token-based authentication
- **WebSocket Support**: Real-time test execution updates
- **Background Tasks**: Non-blocking test execution
- **CORS Configured**: Ready for web UI integration
- **OpenAPI Docs**: Auto-generated API documentation
- **Type Safety**: Full Pydantic validation

## API Endpoints

### Authentication

- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/logout` - Logout (client-side token deletion)

### Tests

- `GET /api/tests` - List test definitions (paginated, filterable)
- `POST /api/tests` - Create new test definition
- `GET /api/tests/{id}` - Get test definition
- `PUT /api/tests/{id}` - Update test definition
- `DELETE /api/tests/{id}` - Delete test definition

### Test Runs

- `GET /api/runs` - List test runs (paginated, filterable)
- `POST /api/runs` - Execute a test (background task)
- `GET /api/runs/{id}` - Get test run details
- `POST /api/runs/{id}/abort` - Abort running test
- `DELETE /api/runs/{id}` - Delete test run

### Profiles

- `GET /api/profiles` - List profiles
- `GET /api/profiles/{id}` - Get profile details

### Analytics

- `GET /api/analytics/summary` - Overall statistics
- `GET /api/analytics/trends` - Time-series data

### WebSocket

- `WS /ws/runs/{id}` - Real-time test run updates

### Health

- `GET /health` - Health check with DB status
- `GET /api/version` - API version info

## Setup

### 1. Database Setup

Install PostgreSQL and create database:

```bash
# Install PostgreSQL (macOS)
brew install postgresql
brew services start postgresql

# Create database and user
psql postgres
CREATE DATABASE uitestflow;
CREATE USER uitest WITH PASSWORD 'uitest';
GRANT ALL PRIVILEGES ON DATABASE uitestflow TO uitest;
\q
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://uitest:uitest@localhost:5432/uitestflow

# Authentication
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Server
HOST=0.0.0.0
PORT=8000
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize Database

```python
# In Python shell or script
import asyncio
from uitestflow.server import init_db

asyncio.run(init_db())
```

### 5. Run Server

```bash
# Development mode (auto-reload)
python -m uitestflow.server.api

# Or with uvicorn directly
uvicorn uitestflow.server.api:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at:

- API: <http://localhost:8000>
- Docs: <http://localhost:8000/api/docs>
- ReDoc: <http://localhost:8000/api/redoc>

## Usage Examples

### Authentication

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Response
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "...",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "member",
    "org_id": "..."
  }
}

# Use token in subsequent requests
curl http://localhost:8000/api/tests \
  -H "Authorization: Bearer eyJhbGc..."
```

### Create Test

```bash
curl -X POST http://localhost:8000/api/tests \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Login Test",
    "description": "Test login functionality",
    "url": "https://example.com",
    "steps": [
      {
        "name": "Navigate to login",
        "action": "goto",
        "url": "https://example.com/login"
      },
      {
        "name": "Fill username",
        "action": "fill",
        "selector": "input[name=username]",
        "value": "testuser"
      },
      {
        "name": "Fill password",
        "action": "fill",
        "selector": "input[name=password]",
        "value": "password123"
      },
      {
        "name": "Click login",
        "action": "click",
        "selector": "button[type=submit]"
      }
    ],
    "evaluators": [
      {
        "name": "All steps completed",
        "type": "all_steps_completed"
      }
    ]
  }'
```

### Execute Test

```bash
# Start test execution
curl -X POST http://localhost:8000/api/runs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "test_id": "test-uuid-here",
    "profile": "staging",
    "triggered_by": "api",
    "context": {
      "pr_number": "123",
      "commit_sha": "abc123"
    }
  }'

# Response (test runs in background)
{
  "id": "run-uuid",
  "test_id": "test-uuid",
  "status": "pending",
  "...": "..."
}

# Poll for status
curl http://localhost:8000/api/runs/run-uuid \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### WebSocket Updates

```javascript
// JavaScript client
const ws = new WebSocket('ws://localhost:8000/ws/runs/run-uuid-here');

ws.onopen = () => {
  console.log('Connected to test run updates');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);

  switch(data.type) {
    case 'status':
      console.log('Status changed:', data.data.status);
      break;
    case 'progress':
      console.log('Progress:', data.data.current_step, '/', data.data.total_steps);
      break;
    case 'screenshot':
      console.log('Screenshot available:', data.data.screenshot_url);
      break;
    case 'complete':
      console.log('Test completed:', data.data.result);
      break;
    case 'error':
      console.error('Test error:', data.data.error);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from test run updates');
};

// Send ping to keep connection alive
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping' }));
  }
}, 30000);
```

### Analytics

```bash
# Get summary statistics
curl http://localhost:8000/api/analytics/summary \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get trends
curl "http://localhost:8000/api/analytics/trends?period=30d" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Database Schema

### Organizations

```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    plan VARCHAR(50) NOT NULL,
    monthly_test_runs INTEGER,
    storage_gb INTEGER,
    retention_days INTEGER,
    settings JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### Users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    password_hash VARCHAR(255),
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP
);
```

### Test Definitions

```sql
CREATE TABLE test_definitions (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(20),
    url VARCHAR(500),
    steps JSONB NOT NULL,
    evaluators JSONB,
    browser_config JSONB,
    auth_config JSONB,
    timeout INTEGER,
    retry_config JSONB,
    tags TEXT[],
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);
```

### Test Runs

```sql
CREATE TABLE test_runs (
    id UUID PRIMARY KEY,
    test_id UUID REFERENCES test_definitions(id),
    org_id UUID REFERENCES organizations(id),
    test_name VARCHAR(255) NOT NULL,
    profile VARCHAR(100),
    triggered_by VARCHAR(50),
    context JSONB,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    result JSONB,
    video_url VARCHAR(500),
    trace_url VARCHAR(500),
    har_url VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

## Authentication Flow

1. User sends credentials to `/api/auth/login`
2. Server validates credentials and generates JWT token
3. Token includes user ID, org ID, and role
4. Client stores token (localStorage, cookie, etc.)
5. Client includes token in Authorization header: `Bearer <token>`
6. Server validates token on protected endpoints
7. Token expires after configured time (default: 24 hours)

## WebSocket Protocol

### Connection

```
Client -> Server: WebSocket handshake to /ws/runs/{run_id}
Server -> Client: {"type": "connected", "run_id": "...", ...}
```

### Messages

**Status Update**

```json
{
  "type": "status",
  "data": {
    "run_id": "...",
    "status": "running",
    "message": "Test execution started",
    "timestamp": "2025-11-12T..."
  },
  "timestamp": "2025-11-12T..."
}
```

**Progress Update**

```json
{
  "type": "progress",
  "data": {
    "run_id": "...",
    "status": "running",
    "current_step": 3,
    "total_steps": 10,
    "step_name": "Click login button",
    "message": "Executing step...",
    "screenshot_url": "https://...",
    "timestamp": "2025-11-12T..."
  },
  "timestamp": "2025-11-12T..."
}
```

**Complete**

```json
{
  "type": "complete",
  "data": {
    "run_id": "...",
    "result": {
      "status": "completed",
      "passed": true,
      "duration_ms": 5000
    },
    "timestamp": "2025-11-12T..."
  },
  "timestamp": "2025-11-12T..."
}
```

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=uitestflow.server tests/

# Run specific test file
pytest tests/test_api.py
```

### Code Quality

```bash
# Format code
black uitestflow/server/

# Lint
ruff check uitestflow/server/

# Type checking
mypy uitestflow/server/
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "uitestflow.server.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: uitestflow
      POSTGRES_USER: uitest
      POSTGRES_PASSWORD: uitest
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://uitest:uitest@db:5432/uitestflow
      SECRET_KEY: your-secret-key
    depends_on:
      - db

volumes:
  postgres_data:
```

### Production Checklist

- [ ] Change `SECRET_KEY` to secure random value
- [ ] Set `DATABASE_URL` to production database
- [ ] Configure CORS origins for production domains
- [ ] Enable HTTPS/TLS
- [ ] Set up database backups
- [ ] Configure logging and monitoring
- [ ] Set up rate limiting
- [ ] Review security headers
- [ ] Set up CI/CD pipeline
- [ ] Configure environment-specific settings

## Troubleshooting

### Database Connection Errors

```bash
# Check PostgreSQL is running
brew services list

# Check connection
psql postgresql://uitest:uitest@localhost:5432/uitestflow

# Reset database
python -c "import asyncio; from uitestflow.server import drop_db, init_db; asyncio.run(drop_db()); asyncio.run(init_db())"
```

### Import Errors

```bash
# Make sure you're in the project root
cd /path/to/uitestframework

# Install in development mode
pip install -e .
```

### WebSocket Connection Issues

- Check CORS configuration
- Verify WebSocket URL format
- Check firewall/proxy settings
- Test with WebSocket debugging tools

## Future Enhancements

- [ ] Celery task queue for long-running tests
- [ ] Redis caching for improved performance
- [ ] S3 integration for artifact storage
- [ ] Rate limiting middleware
- [ ] API key authentication
- [ ] Advanced RBAC (role-based access control)
- [ ] Audit logging
- [ ] Metrics and monitoring
- [ ] GraphQL API (optional)
- [ ] gRPC API (optional)

## Contributing

When adding new endpoints:

1. Create route handler in appropriate file under `routes/`
2. Add Pydantic schemas in `schemas.py`
3. Update database models if needed in `database.py`
4. Add authentication/authorization decorators
5. Include OpenAPI documentation (docstrings)
6. Write tests
7. Update this README

## License

See project root LICENSE file.
