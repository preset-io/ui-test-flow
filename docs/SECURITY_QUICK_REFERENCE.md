# Security Features Quick Reference

## SECRET_KEY Configuration

### Generate Secure Key

```bash
openssl rand -hex 32
```

### Set in Environment

```bash
# .env file
SECRET_KEY=your-generated-key-here

# Or export
export SECRET_KEY=$(openssl rand -hex 32)
```

### Production Requirement

- **MUST** be set in production
- Application **WILL NOT START** without it
- Default dev key is automatically rejected

## Rate Limiting

### Default Configuration

```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_BURST=1.5  # Allows bursts to 150 req/min
```

### Exempt Endpoints

- `/health`
- `/`
- `/api/version`
- `/metrics`

### Response Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1673456789
```

### Rate Limit Error

```json
{
  "error": "Rate Limit Exceeded",
  "detail": "Too many requests. Limit: 100/minute",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 45,
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Request Tracking

### Request ID Header

```bash
# Client sends correlation ID
curl -H "X-Request-ID: my-id-123" https://api.example.com/api/tests

# Server includes in response
X-Request-ID: my-id-123
```

### All Errors Include Request ID

```json
{
  "error": "Not Found",
  "detail": "Test not found",
  "code": "NOT_FOUND",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Structured Logging

### Configuration

```bash
# Production (JSON)
LOG_FORMAT=json

# Development (text)
LOG_FORMAT=text

# Log level
UITESTFLOW_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### JSON Log Example

```json
{
  "timestamp": "2025-01-15T10:30:45.123456",
  "level": "INFO",
  "message": "Request completed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "GET",
  "path": "/api/tests",
  "status_code": 200,
  "duration_ms": 45.23,
  "client_ip": "192.168.1.100"
}
```

## Environment Variables Summary

### Required (Production)

```bash
SECRET_KEY=<secure-random-key>
UITESTFLOW_ENV=production
DATABASE_URL=postgresql://...
```

### Security Settings

```bash
# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_BURST=1.5

# Logging
LOG_FORMAT=json
UITESTFLOW_LOG_LEVEL=INFO
```

### Optional Security

```bash
# CORS
CORS_ORIGINS=https://app.example.com,https://admin.example.com

# Monitoring
SENTRY_DSN=https://...
```

## Client Integration

### Handle Rate Limits

```python
import time
import requests

def api_call_with_retry(url):
    response = requests.get(url)

    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        time.sleep(retry_after)
        response = requests.get(url)

    return response
```

### Track Requests

```python
import uuid
import requests

correlation_id = str(uuid.uuid4())
response = requests.get(
    "https://api.example.com/api/tests",
    headers={"X-Request-ID": correlation_id}
)

if not response.ok:
    error = response.json()
    print(f"Error: {error['detail']}")
    print(f"Request ID: {error['request_id']}")
    # Use request_id for support
```

## Testing

### Test Rate Limiting

```bash
# Make rapid requests
for i in {1..105}; do
  curl http://localhost:8000/api/tests
done

# Should see 429 after hitting limit
```

### Test Request Tracking

```bash
# Check headers
curl -v http://localhost:8000/api/tests | grep X-Request-ID

# Send custom request ID
curl -H "X-Request-ID: test-123" http://localhost:8000/api/tests
```

### Verify Security

```bash
# Health check
curl http://localhost:8000/health

# Should return rate limit headers
curl -v http://localhost:8000/api/tests | grep X-RateLimit
```

## Monitoring Queries

### Rate Limit Events

```
# Log query (JSON format)
message:"Rate limit exceeded" | stats count by client_ip

# Alert if > 100 rate limit events per hour from single IP
```

### Error Tracking

```
# Find errors by request ID
request_id:"550e8400-e29b-41d4-a716-446655440000"

# Error rate
level:"ERROR" | stats count by hour
```

### Performance

```
# Slow requests
duration_ms:>1000 | sort -duration_ms

# Average response time
stats avg(duration_ms) by path
```

## Troubleshooting

### App Won't Start

```bash
# Check SECRET_KEY is set
echo $SECRET_KEY

# Generate if missing
export SECRET_KEY=$(openssl rand -hex 32)
```

### Too Many Rate Limit Errors

```bash
# Increase limits
export RATE_LIMIT_PER_MINUTE=200
export RATE_LIMIT_BURST=2.0

# Or disable
export RATE_LIMIT_ENABLED=false
```

### Can't Find Request in Logs

```bash
# Search by request ID
grep "request_id.*550e8400" /var/log/uitestflow/app.log

# Or with jq for JSON logs
cat app.log | jq 'select(.request_id=="550e8400...")'
```

## Common Scenarios

### Scenario: User Reports Error

1. Ask for request ID from error message
2. Search logs: `grep request_id:<id>`
3. Review full request trace
4. Identify root cause

### Scenario: High Traffic Event

1. Monitor rate limit headers
2. Increase limits if needed:

   ```bash
   RATE_LIMIT_PER_MINUTE=500
   ```

3. Consider disabling temporarily:

   ```bash
   RATE_LIMIT_ENABLED=false
   ```

4. Re-enable after event

### Scenario: Security Incident

1. Check logs for suspicious patterns:

   ```bash
   level:"WARNING" | stats count by client_ip
   ```

2. Block IP at rate limiter or firewall
3. Review request IDs for affected requests
4. Rotate SECRET_KEY if compromised

## Best Practices

1. **Always use HTTPS** in production
2. **Rotate SECRET_KEY** regularly (quarterly)
3. **Monitor rate limits** and adjust as needed
4. **Use request IDs** in support tickets
5. **Enable structured logging** in production
6. **Set up alerts** for rate limiting events
7. **Review logs** regularly for security events
8. **Keep secrets in vault**, not environment variables

## Additional Resources

- Full documentation: [SECURITY.md](../SECURITY.md)
- Migration guide: [SECURITY_MIGRATION.md](./SECURITY_MIGRATION.md)
- FastAPI security: <https://fastapi.tiangolo.com/tutorial/security/>
- JWT best practices: <https://tools.ietf.org/html/rfc8725>
