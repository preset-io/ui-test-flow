# Deployment Checklist for Security Enhancements

Use this checklist to ensure a smooth deployment of the security enhancements.

## Pre-Deployment

### 1. Review Changes

- [ ] Read [CHANGES_SUMMARY.md](./CHANGES_SUMMARY.md)
- [ ] Review [SECURITY.md](../SECURITY.md)
- [ ] Understand breaking changes (SECRET_KEY requirement)

### 2. Generate SECRET_KEY

- [ ] Generate secure SECRET_KEY:

  ```bash
  openssl rand -hex 32
  ```

- [ ] Store in secure vault (AWS Secrets Manager, HashiCorp Vault, etc.)
- [ ] **DO NOT** commit to version control
- [ ] **DO NOT** share in Slack/email

### 3. Update Environment Variables

#### Development

- [ ] Update `.env`:

  ```bash
  SECRET_KEY=<dev-key>
  RATE_LIMIT_ENABLED=false  # Optional: disable for dev
  LOG_FORMAT=text
  UITESTFLOW_LOG_LEVEL=DEBUG
  ```

#### Staging

- [ ] Update staging environment:

  ```bash
  UITESTFLOW_ENV=staging
  SECRET_KEY=<staging-key>
  RATE_LIMIT_ENABLED=true
  RATE_LIMIT_PER_MINUTE=100
  LOG_FORMAT=json
  UITESTFLOW_LOG_LEVEL=INFO
  ```

#### Production

- [ ] Update production environment:

  ```bash
  UITESTFLOW_ENV=production
  SECRET_KEY=<production-key>  # REQUIRED
  RATE_LIMIT_ENABLED=true
  RATE_LIMIT_PER_MINUTE=100
  RATE_LIMIT_BURST=1.5
  LOG_FORMAT=json
  UITESTFLOW_LOG_LEVEL=INFO
  ```

### 4. Update Infrastructure

#### Logging

- [ ] Update log aggregation to parse JSON format
- [ ] Create dashboards for:
  - Request rate by endpoint
  - Rate limiting events
  - Error rate by request ID
  - Response time percentiles

#### Monitoring

- [ ] Configure alerts:
  - Rate limiting events > 100/hour
  - Error rate > 1%
  - Response time p95 > 1000ms
  - Failed authentication attempts

#### Load Balancer / Reverse Proxy

- [ ] Verify X-Forwarded-For header is set
- [ ] Verify X-Real-IP header is set
- [ ] Test rate limiting with proxied requests

### 5. Update Client Applications

- [ ] Review client code for rate limit handling
- [ ] Add retry logic for 429 responses
- [ ] Add request ID to error reports
- [ ] Test with staging environment

## Deployment Steps

### Development Environment

1. **Pull latest code:**

   ```bash
   git pull origin main
   ```

2. **Install dependencies** (if any new ones):

   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables:**

   ```bash
   export SECRET_KEY=$(openssl rand -hex 32)
   export UITESTFLOW_ENV=development
   ```

4. **Start server:**

   ```bash
   python -m uitestflow.server
   ```

5. **Verify startup:**
   - [ ] Check logs for "Logging configured"
   - [ ] Check logs for "Rate limiting initialized"
   - [ ] Check logs for "Database initialized"

6. **Test endpoints:**

   ```bash
   # Health check
   curl http://localhost:8000/health

   # Check rate limit headers
   curl -v http://localhost:8000/api/tests | grep X-RateLimit

   # Check request ID
   curl -v http://localhost:8000/api/tests | grep X-Request-ID
   ```

### Staging Environment

1. **Deploy code:**

   ```bash
   # Your deployment process
   ```

2. **Verify environment variables:**

   ```bash
   # SSH to staging server
   echo $SECRET_KEY  # Should be set
   echo $RATE_LIMIT_ENABLED  # Should be "true"
   echo $LOG_FORMAT  # Should be "json"
   ```

3. **Start/restart service:**

   ```bash
   # Your service restart command
   systemctl restart uitestflow
   ```

4. **Verify startup:**

   ```bash
   # Check logs
   journalctl -u uitestflow -f

   # Look for:
   # - "Starting UITestFlow server..."
   # - "Logging configured"
   # - "Rate limiting initialized"
   # - "Database initialized"
   ```

5. **Run smoke tests:**

   ```bash
   # Health check
   curl https://staging-api.example.com/health

   # Authentication
   curl -X POST https://staging-api.example.com/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"test"}'

   # Rate limiting test
   for i in {1..105}; do
     curl https://staging-api.example.com/api/tests
   done
   # Should see 429 after ~100 requests
   ```

6. **Monitor for issues:**

   ```bash
   # Watch error logs
   tail -f /var/log/uitestflow/app.log | jq 'select(.level=="ERROR")'

   # Watch rate limiting
   tail -f /var/log/uitestflow/app.log | jq 'select(.message | contains("Rate limit"))'
   ```

### Production Environment

1. **Final pre-deployment checks:**
   - [ ] All staging tests passed
   - [ ] SECRET_KEY generated and stored securely
   - [ ] Team notified of deployment
   - [ ] Rollback plan documented
   - [ ] Off-hours deployment scheduled (if applicable)

2. **Deploy code:**

   ```bash
   # Your production deployment process
   ```

3. **Verify environment variables:**

   ```bash
   # Verify SECRET_KEY is set (DO NOT echo it)
   [ -n "$SECRET_KEY" ] && echo "SECRET_KEY is set" || echo "ERROR: SECRET_KEY not set"

   # Verify other vars
   echo $UITESTFLOW_ENV  # Should be "production"
   echo $RATE_LIMIT_ENABLED  # Should be "true"
   echo $LOG_FORMAT  # Should be "json"
   ```

4. **Start/restart service:**

   ```bash
   # Your service restart command
   systemctl restart uitestflow
   ```

5. **Verify startup:**

   ```bash
   # Check logs
   journalctl -u uitestflow -n 100

   # Should see:
   # - "Starting UITestFlow server..."
   # - "Logging configured"
   # - "Rate limiting initialized"
   # - "Database initialized"

   # Should NOT see:
   # - "CRITICAL SECURITY ERROR"
   # - Any stack traces on startup
   ```

6. **Verify endpoints:**

   ```bash
   # Health check
   curl https://api.example.com/health

   # Response headers
   curl -v https://api.example.com/api/version

   # Should see:
   # - X-Request-ID: <uuid>
   # - X-RateLimit-Limit: 100
   # - X-RateLimit-Remaining: <number>
   # - X-RateLimit-Reset: <timestamp>
   ```

7. **Monitor for first 30 minutes:**
   - [ ] Error rate normal (< 1%)
   - [ ] Response time normal (< 500ms p95)
   - [ ] No unexpected rate limiting
   - [ ] Authentication working
   - [ ] All endpoints responding

## Post-Deployment

### Immediate (First Hour)

- [ ] Monitor error rates
- [ ] Monitor response times
- [ ] Check for rate limiting false positives
- [ ] Verify logging aggregation working
- [ ] Test authentication flow
- [ ] Check database connections

### First Day

- [ ] Review rate limiting events
- [ ] Analyze performance metrics
- [ ] Check for any client-reported issues
- [ ] Verify all dashboards updated
- [ ] Test support workflow with request IDs

### First Week

- [ ] Analyze rate limiting patterns
- [ ] Adjust limits if needed
- [ ] Review and tune alerts
- [ ] Collect feedback from team
- [ ] Update documentation based on learnings

## Rollback Procedure

### If Critical Issues Occur

1. **Immediate rollback:**

   ```bash
   # Revert to previous version
   git revert <deployment-commit>

   # Or checkout previous release
   git checkout <previous-release-tag>

   # Redeploy
   ```

2. **Communicate:**
   - [ ] Notify team of rollback
   - [ ] Document issue and reason for rollback
   - [ ] Create incident report

3. **Investigate:**
   - [ ] Collect logs (especially with request IDs)
   - [ ] Analyze error patterns
   - [ ] Identify root cause

### If Partial Issues Occur

1. **Disable rate limiting:**

   ```bash
   export RATE_LIMIT_ENABLED=false
   systemctl restart uitestflow
   ```

2. **Switch to text logging:**

   ```bash
   export LOG_FORMAT=text
   systemctl restart uitestflow
   ```

3. **Monitor and adjust:**
   - [ ] Identify specific issue
   - [ ] Adjust configuration
   - [ ] Re-enable features gradually

## Verification Tests

### Manual Tests

```bash
# 1. Health check
curl https://api.example.com/health
# Expected: 200 OK

# 2. Version info
curl https://api.example.com/api/version
# Expected: 200 OK with version info

# 3. Authentication
curl -X POST https://api.example.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'
# Expected: 200 OK with access_token

# 4. Authenticated request
curl -H "Authorization: Bearer $TOKEN" \
     https://api.example.com/api/tests
# Expected: 200 OK

# 5. Request tracking
curl -H "X-Request-ID: test-123" \
     https://api.example.com/api/tests
# Expected: Response header X-Request-ID: test-123

# 6. Rate limiting
for i in {1..105}; do
  curl https://api.example.com/api/tests
done
# Expected: First ~100 succeed, then 429 responses

# 7. Error includes request ID
curl https://api.example.com/api/tests/invalid-id
# Expected: Error response with request_id field
```

### Automated Tests

```bash
# Run test suite
pytest tests/test_security_features.py -v

# Run integration tests
pytest tests/ -m integration -v

# Run performance tests
pytest tests/ -m slow -v
```

## Common Issues & Solutions

### Issue: App won't start

**Error:** `RuntimeError: CRITICAL SECURITY ERROR: SECRET_KEY environment variable must be set in production`

**Solution:**

```bash
export SECRET_KEY=$(openssl rand -hex 32)
systemctl restart uitestflow
```

### Issue: Too many 429 responses

**Cause:** Rate limit too low for traffic

**Solution:**

```bash
# Increase limit
export RATE_LIMIT_PER_MINUTE=200
export RATE_LIMIT_BURST=2.0
systemctl restart uitestflow
```

### Issue: Logs not showing up in aggregation

**Cause:** Log format changed to JSON

**Solution:**

1. Update log parser to handle JSON
2. Or temporarily switch to text:

   ```bash
   export LOG_FORMAT=text
   systemctl restart uitestflow
   ```

### Issue: Users can't authenticate

**Cause:** SECRET_KEY changed, invalidating tokens

**Solution:**

1. Users need to log in again
2. Communicate the change
3. Consider token migration if many users affected

## Success Criteria

Deployment is successful when:

- [ ] Application starts without errors
- [ ] All health checks pass
- [ ] Authentication works correctly
- [ ] Rate limiting is active and working
- [ ] Request IDs appear in all responses
- [ ] Logs are properly formatted and aggregated
- [ ] Error rate < 1%
- [ ] Response time p95 < 500ms
- [ ] No unexpected rate limiting of legitimate traffic
- [ ] Monitoring dashboards show data
- [ ] Alerts are firing appropriately (not too many, not too few)

## Contact & Support

- **Team Lead:** [Name]
- **On-Call:** [On-call rotation]
- **Incident Channel:** #incidents
- **Documentation:** docs/SECURITY*.md

## Appendix: Environment Variables Reference

### Required

```bash
SECRET_KEY=<secure-random-key>      # CRITICAL: Must be set in production
UITESTFLOW_ENV=production           # Environment: development/staging/production
DATABASE_URL=postgresql://...       # Database connection string
```

### Security

```bash
RATE_LIMIT_ENABLED=true            # Enable rate limiting
RATE_LIMIT_PER_MINUTE=100          # Requests per minute per IP
RATE_LIMIT_BURST=1.5               # Burst multiplier
```

### Logging

```bash
LOG_FORMAT=json                    # json or text
UITESTFLOW_LOG_LEVEL=INFO          # DEBUG/INFO/WARNING/ERROR/CRITICAL
```

### Optional

```bash
CORS_ORIGINS=https://app.example.com   # Allowed CORS origins
SENTRY_DSN=https://...                 # Error tracking
```
