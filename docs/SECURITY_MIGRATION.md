# Security Enhancement Migration Guide

This guide helps you migrate from the previous version to the new security-enhanced version of UITestFlow.

## Overview of Changes

### 1. SECRET_KEY Management (CRITICAL)

**What Changed:**

- SECRET_KEY is now loaded from environment variable instead of hardcoded value
- Production deployments will fail to start if SECRET_KEY is not properly configured

**Action Required:**

1. Generate a secure SECRET_KEY:

   ```bash
   openssl rand -hex 32
   ```

2. Add to your `.env` file:

   ```bash
   SECRET_KEY=<your-generated-key-here>
   ```

3. For existing deployments, set the environment variable before restarting:

   ```bash
   export SECRET_KEY=$(openssl rand -hex 32)
   ```

**Impact:**

- **Breaking Change:** Production deployments will not start without SECRET_KEY
- Existing JWT tokens will be invalidated if you change the SECRET_KEY
- Users will need to re-authenticate after the SECRET_KEY change

### 2. Rate Limiting

**What Changed:**

- New rate limiting middleware added to prevent API abuse
- Default: 100 requests per minute per IP address
- Configurable burst allowance for traffic spikes

**Action Required:**

1. Review rate limits for your use case:

   ```bash
   # In .env
   RATE_LIMIT_ENABLED=true
   RATE_LIMIT_PER_MINUTE=100
   RATE_LIMIT_BURST=1.5
   ```

2. To disable during migration/testing:

   ```bash
   RATE_LIMIT_ENABLED=false
   ```

**Impact:**

- **Non-Breaking:** Disabled by default in development
- May affect clients making many rapid requests
- Health checks and metrics endpoints are exempt

### 3. Request Tracking & Structured Logging

**What Changed:**

- All requests now receive unique request IDs
- Structured JSON logging available
- Enhanced error responses with request IDs

**Action Required:**

1. Configure log format in `.env`:

   ```bash
   # For production (JSON)
   LOG_FORMAT=json

   # For development (human-readable)
   LOG_FORMAT=text
   ```

2. Update log aggregation tools to parse new JSON format

**Impact:**

- **Non-Breaking:** Works with existing logging
- Enhanced debugging capabilities
- Better integration with log aggregation systems

### 4. Enhanced Error Responses

**What Changed:**

- Error responses now include `request_id` field
- Better error messages with tracking support

**Action Required:**

- Update client code to use `request_id` for support requests
- Update error handling to expect new field

**Impact:**

- **Non-Breaking:** Existing error handling still works
- New `request_id` field added to all error responses

## Migration Steps

### Step 1: Update Environment Configuration

1. Copy the new `.env.example` to review changes:

   ```bash
   cp .env.example .env.new
   diff .env .env.new
   ```

2. Add required variables to your `.env`:

   ```bash
   # CRITICAL: Generate and set SECRET_KEY
   SECRET_KEY=$(openssl rand -hex 32)

   # Configure rate limiting
   RATE_LIMIT_ENABLED=true
   RATE_LIMIT_PER_MINUTE=100
   RATE_LIMIT_BURST=1.5

   # Configure logging
   LOG_FORMAT=json
   UITESTFLOW_LOG_LEVEL=INFO
   ```

### Step 2: Test in Development

1. Start the server in development mode:

   ```bash
   UITESTFLOW_ENV=development python -m uitestflow.server
   ```

2. Verify startup logs show middleware initialization:

   ```
   Starting UITestFlow server...
   Logging configured
   Rate limiting initialized
   Database initialized
   ```

3. Test rate limiting:

   ```bash
   # Make rapid requests
   for i in {1..105}; do
     curl http://localhost:8000/api/tests
   done

   # Should see 429 response after hitting limit
   ```

4. Test request tracking:

   ```bash
   # Check response headers
   curl -v http://localhost:8000/api/tests
   # Look for: X-Request-ID, X-RateLimit-* headers
   ```

### Step 3: Update Client Applications

If you have client applications, update them to:

1. Handle rate limit responses (429):

   ```python
   import time

   response = requests.get("https://api.example.com/api/tests")

   if response.status_code == 429:
       retry_after = int(response.headers.get("Retry-After", 60))
       print(f"Rate limited. Retry after {retry_after} seconds")
       time.sleep(retry_after)
       response = requests.get("https://api.example.com/api/tests")
   ```

2. Include request IDs in error reports:

   ```python
   try:
       response = requests.get("https://api.example.com/api/tests")
       response.raise_for_status()
   except requests.HTTPError as e:
       error_data = e.response.json()
       request_id = error_data.get("request_id", "unknown")
       print(f"Error occurred. Request ID: {request_id}")
       # Include request_id in support tickets
   ```

3. Support request correlation:

   ```python
   import uuid

   correlation_id = str(uuid.uuid4())
   response = requests.get(
       "https://api.example.com/api/tests",
       headers={"X-Request-ID": correlation_id}
   )
   # Track this ID in your logs
   ```

### Step 4: Update Monitoring & Alerting

1. Update log queries for new JSON format:

   ```
   # Old text format
   "Request completed - GET /api/tests - 200"

   # New JSON format
   {
     "message": "Request completed",
     "method": "GET",
     "path": "/api/tests",
     "status_code": 200,
     "duration_ms": 45.23,
     "request_id": "..."
   }
   ```

2. Add rate limiting alerts:

   ```
   # Alert when rate limiting is triggered frequently
   query: message:"Rate limit exceeded" | stats count by client_ip
   threshold: > 100 in 1 hour
   ```

3. Track request IDs in APM tools:

   ```
   # Use X-Request-ID header for distributed tracing
   ```

### Step 5: Deploy to Staging

1. Set environment variables:

   ```bash
   export UITESTFLOW_ENV=staging
   export SECRET_KEY=$(openssl rand -hex 32)
   export RATE_LIMIT_ENABLED=true
   export LOG_FORMAT=json
   ```

2. Deploy application:

   ```bash
   # Your deployment process
   ```

3. Run smoke tests:

   ```bash
   # Health check
   curl https://staging-api.example.com/health

   # Authenticated request
   curl -H "Authorization: Bearer $TOKEN" \
        https://staging-api.example.com/api/tests

   # Rate limit test
   # (make rapid requests to verify limiting)
   ```

4. Monitor logs for issues:

   ```bash
   # Check for errors
   tail -f /var/log/uitestflow/app.log | jq 'select(.level=="ERROR")'

   # Check rate limiting
   tail -f /var/log/uitestflow/app.log | jq 'select(.message=="Rate limit exceeded")'
   ```

### Step 6: Deploy to Production

1. **Pre-deployment checklist:**
   - [ ] SECRET_KEY generated and securely stored
   - [ ] Environment variables configured
   - [ ] Monitoring/alerting updated
   - [ ] Client applications updated
   - [ ] Rollback plan documented
   - [ ] Team notified of deployment

2. **Deployment:**

   ```bash
   export UITESTFLOW_ENV=production
   export SECRET_KEY=<your-production-secret>
   export RATE_LIMIT_ENABLED=true
   export RATE_LIMIT_PER_MINUTE=100
   export LOG_FORMAT=json

   # Your production deployment process
   ```

3. **Post-deployment verification:**

   ```bash
   # Health check
   curl https://api.example.com/health

   # Verify security
   curl https://api.example.com/ | jq
   # Should NOT show SECRET_KEY in any response

   # Verify rate limiting
   curl -v https://api.example.com/api/tests | grep X-RateLimit

   # Verify request tracking
   curl -v https://api.example.com/api/tests | grep X-Request-ID
   ```

4. **Monitor for issues:**
   - Watch error rates in APM
   - Check for rate limiting false positives
   - Monitor authentication failures
   - Review performance metrics

## Rollback Procedure

If you encounter issues:

### Quick Rollback

1. Revert to previous version:

   ```bash
   git revert <deployment-commit>
   # Redeploy previous version
   ```

2. Existing users remain authenticated (if SECRET_KEY unchanged)

### Partial Rollback (Disable Features)

1. Disable rate limiting only:

   ```bash
   export RATE_LIMIT_ENABLED=false
   # Restart application
   ```

2. Revert to text logging:

   ```bash
   export LOG_FORMAT=text
   # Restart application
   ```

## Troubleshooting

### Issue: Application Won't Start

**Error:** `RuntimeError: CRITICAL SECURITY ERROR: SECRET_KEY environment variable must be set in production`

**Solution:**

```bash
# Generate and set SECRET_KEY
export SECRET_KEY=$(openssl rand -hex 32)

# Or add to .env file
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
```

### Issue: Users Can't Authenticate

**Cause:** SECRET_KEY changed, invalidating existing tokens

**Solution:**

1. Users need to log in again
2. Communicate the change to users
3. Consider implementing token migration if needed

### Issue: Rate Limiting Too Aggressive

**Error:** Legitimate users receiving 429 responses

**Solution:**

```bash
# Increase limits
export RATE_LIMIT_PER_MINUTE=200
export RATE_LIMIT_BURST=2.0

# Or disable temporarily
export RATE_LIMIT_ENABLED=false
```

### Issue: Logs Too Verbose

**Solution:**

```bash
# Reduce log level
export UITESTFLOW_LOG_LEVEL=WARNING

# Or switch to text format for easier reading
export LOG_FORMAT=text
```

### Issue: Request IDs Not Showing in Logs

**Solution:**

1. Ensure RequestTrackingMiddleware is loaded:

   ```python
   # Check api.py
   app.add_middleware(RequestTrackingMiddleware)
   ```

2. Check log format configuration:

   ```bash
   # Should be json for structured logs
   export LOG_FORMAT=json
   ```

## Performance Considerations

### Rate Limiting

- **In-memory storage:** Works well for single-instance deployments
- **Multi-instance:** Consider Redis-backed rate limiting
- **High traffic:** May need to increase limits or use external rate limiter (nginx, Cloudflare)

### Request Tracking

- **Minimal overhead:** ~1-2ms per request
- **No database queries:** All tracking is in-memory
- **Scalable:** Works with any number of requests

### Logging

- **JSON format:** Slight overhead (~0.5ms) for formatting
- **Text format:** Minimal overhead for development
- **Log aggregation:** May need to adjust shipping frequency

## Security Considerations

### SECRET_KEY Rotation

To rotate the SECRET_KEY without downtime:

1. Support multiple keys (requires code changes)
2. Or: Rotate during maintenance window
3. Communicate to users that they'll need to re-authenticate

### Rate Limiting Bypass

- **Health checks:** Exempt from rate limiting
- **Internal services:** Consider IP allowlist
- **Admin users:** Consider higher limits per user role

### Request ID Security

- Request IDs are UUID v4 (random)
- No sensitive information in request IDs
- Safe to include in public error messages

## Support

For issues or questions:

1. Check logs with request ID
2. Review this migration guide
3. Consult SECURITY.md for detailed documentation
4. Open GitHub issue with request ID and logs

## Version History

- **v0.2.0** - Security enhancements (2025-01-15)
  - SECRET_KEY from environment variable
  - Rate limiting middleware
  - Request tracking and structured logging
  - Enhanced error responses

- **v0.1.0** - Initial release
  - Hardcoded SECRET_KEY (insecure)
  - No rate limiting
  - Basic error responses
