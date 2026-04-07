"""
Middleware for FastAPI application.

Provides rate limiting, request tracking, and structured logging.
"""

import json
import logging
import os
import time
import uuid
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


# Configure structured logging
logging.basicConfig(
    level=os.getenv("UITESTFLOW_LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    if os.getenv("LOG_FORMAT", "json") == "text"
    else None,
)
logger = logging.getLogger(__name__)


# ============================================================================
# Rate Limiting Middleware
# ============================================================================


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using in-memory storage.

    For production deployments with multiple workers, consider using Redis-backed
    rate limiting via slowapi or similar library.

    Configuration via environment variables:
    - RATE_LIMIT_ENABLED: Enable/disable rate limiting (default: true)
    - RATE_LIMIT_PER_MINUTE: Requests per minute per IP (default: 100)
    - RATE_LIMIT_BURST: Burst allowance multiplier (default: 1.5)
    """

    def __init__(self, app):
        super().__init__(app)
        self.enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        self.rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
        self.burst_multiplier = float(os.getenv("RATE_LIMIT_BURST", "1.5"))
        self.max_burst = int(self.rate_limit_per_minute * self.burst_multiplier)

        # In-memory storage: {ip_address: [(timestamp, count), ...]}
        self._requests: dict[str, list[tuple[float, int]]] = defaultdict(list)

        # Exempt paths (health checks, metrics, etc.)
        self.exempt_paths = {
            "/health",
            "/",
            "/api/version",
            "/metrics",
        }

        logger.info(
            "Rate limiting initialized",
            extra={
                "enabled": self.enabled,
                "rate_limit_per_minute": self.rate_limit_per_minute,
                "max_burst": self.max_burst,
            },
        )

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.

        Handles X-Forwarded-For and X-Real-IP headers for reverse proxy setups.
        """
        # Check proxy headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, use the first one
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        client = request.client
        return client.host if client else "unknown"

    def _is_rate_limited(self, ip: str) -> tuple[bool, dict]:
        """
        Check if IP address is rate limited.

        Returns:
            Tuple of (is_limited, rate_limit_info)
        """
        now = time.time()
        minute_ago = now - 60

        # Clean up old entries
        self._requests[ip] = [(ts, count) for ts, count in self._requests[ip] if ts > minute_ago]

        # Count requests in the last minute
        total_requests = sum(count for _, count in self._requests[ip])

        # Check if rate limit exceeded
        is_limited = total_requests >= self.max_burst

        rate_limit_info = {
            "limit": self.rate_limit_per_minute,
            "remaining": max(0, self.max_burst - total_requests),
            "reset": int(now + 60),
        }

        if not is_limited:
            # Add current request
            self._requests[ip].append((now, 1))

        return is_limited, rate_limit_info

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting if disabled or path is exempt
        if not self.enabled or request.url.path in self.exempt_paths:
            return await call_next(request)

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Check rate limit
        is_limited, rate_info = self._is_rate_limited(client_ip)

        if is_limited:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "client_ip": client_ip,
                    "path": request.url.path,
                    "limit": rate_info["limit"],
                },
            )

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate Limit Exceeded",
                    "detail": f"Too many requests. Limit: {rate_info['limit']}/minute",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": rate_info["reset"] - int(time.time()),
                },
                headers={
                    "X-RateLimit-Limit": str(rate_info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(rate_info["reset"]),
                    "Retry-After": str(rate_info["reset"] - int(time.time())),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])

        return response


# ============================================================================
# Request Tracking Middleware
# ============================================================================


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Request tracking middleware that adds request IDs and structured logging.

    Adds the following to each request:
    - Unique request ID (available as request.state.request_id)
    - Request/response logging with timing
    - Correlation ID support (via X-Request-ID header)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tracking."""
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        # Record start time
        start_time = time.time()

        # Log request
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("User-Agent", "unknown"),
        }

        logger.info("Request started", extra=log_data)

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error
            duration_ms = (time.time() - start_time) * 1000
            error_data = {
                **log_data,
                "duration_ms": round(duration_ms, 2),
                "error": str(e),
                "error_type": type(e).__name__,
            }
            logger.error("Request failed", extra=error_data, exc_info=True)

            # Return error response with request ID
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Server Error",
                    "detail": "An unexpected error occurred",
                    "code": "INTERNAL_ERROR",
                    "request_id": request_id,
                },
                headers={"X-Request-ID": request_id},
            )

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Add request ID to response
        response.headers["X-Request-ID"] = request_id

        # Log response
        response_data = {
            **log_data,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }

        if response.status_code >= 400:
            logger.warning("Request completed with error", extra=response_data)
        else:
            logger.info("Request completed", extra=response_data)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        client = request.client
        return client.host if client else "unknown"


# ============================================================================
# Structured Logging Formatter
# ============================================================================


class StructuredLogFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Outputs logs in JSON format for easy parsing by log aggregation systems
    (e.g., ELK, Splunk, CloudWatch).
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # Add any extra attributes
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
            } and not key.startswith("_"):
                log_data[key] = value

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


# ============================================================================
# Logging Configuration
# ============================================================================


def configure_logging() -> None:
    """
    Configure structured logging for the application.

    Uses JSON format for production, text format for development.
    """
    log_format = os.getenv("LOG_FORMAT", "json")
    log_level = os.getenv("UITESTFLOW_LOG_LEVEL", "INFO")

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler()

    if log_format == "json":
        handler.setFormatter(StructuredLogFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

    root_logger.addHandler(handler)

    logger.info(
        "Logging configured",
        extra={"log_format": log_format, "log_level": log_level},
    )
