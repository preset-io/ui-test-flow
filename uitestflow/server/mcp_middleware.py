"""
MCP-specific middleware for request validation, logging, and error handling.

Provides middleware components specifically for MCP endpoints including
rate limiting, request validation, and response formatting.
"""

import logging
import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger(__name__)


# ============================================================================
# Rate Limiting for MCP Endpoints
# ============================================================================


class MCPRateLimiter:
    """
    Rate limiter specifically for MCP endpoints.

    Implements token bucket algorithm with separate limits for generation
    and execution endpoints.
    """

    def __init__(
        self,
        generation_limit: int = 10,  # requests per minute
        execution_limit: int = 20,  # requests per minute
        window_seconds: int = 60,
    ):
        """
        Initialize rate limiter.

        Args:
            generation_limit: Max generation requests per window
            execution_limit: Max execution requests per window
            window_seconds: Time window in seconds
        """
        self.generation_limit = generation_limit
        self.execution_limit = execution_limit
        self.window_seconds = window_seconds

        # Track requests per client
        self._generation_requests: dict[str, list[float]] = defaultdict(list)
        self._execution_requests: dict[str, list[float]] = defaultdict(list)

    def _clean_old_requests(self, requests: list[float], window: float) -> list[float]:
        """Remove requests outside the time window."""
        current_time = time.time()
        return [req_time for req_time in requests if current_time - req_time < window]

    def check_generation_limit(self, client_id: str) -> tuple[bool, int]:
        """
        Check if generation request is allowed.

        Args:
            client_id: Client identifier (IP or API key)

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        current_time = time.time()

        # Clean old requests
        self._generation_requests[client_id] = self._clean_old_requests(
            self._generation_requests[client_id], self.window_seconds
        )

        # Check limit
        request_count = len(self._generation_requests[client_id])
        if request_count >= self.generation_limit:
            return False, 0

        # Add current request
        self._generation_requests[client_id].append(current_time)
        remaining = self.generation_limit - request_count - 1

        return True, remaining

    def check_execution_limit(self, client_id: str) -> tuple[bool, int]:
        """
        Check if execution request is allowed.

        Args:
            client_id: Client identifier (IP or API key)

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        current_time = time.time()

        # Clean old requests
        self._execution_requests[client_id] = self._clean_old_requests(
            self._execution_requests[client_id], self.window_seconds
        )

        # Check limit
        request_count = len(self._execution_requests[client_id])
        if request_count >= self.execution_limit:
            return False, 0

        # Add current request
        self._execution_requests[client_id].append(current_time)
        remaining = self.execution_limit - request_count - 1

        return True, remaining


# Global rate limiter instance
_rate_limiter = MCPRateLimiter()


# ============================================================================
# MCP Request Validation Middleware
# ============================================================================


class MCPValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for validating MCP-specific requests.

    Checks API key presence, validates request format, and adds
    MCP-specific headers.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with MCP validation.

        Args:
            request: Incoming request
            call_next: Next middleware in chain

        Returns:
            Response
        """
        # Only apply to MCP endpoints
        if not request.url.path.startswith("/api/mcp"):
            return await call_next(request)

        # Check API key for non-status endpoints
        if request.url.path != "/api/mcp/status":
            api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")

            if not api_key:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Unauthorized",
                        "detail": "API key required for MCP endpoints",
                        "code": "API_KEY_REQUIRED",
                    },
                    headers={"WWW-Authenticate": "ApiKey"},
                )

            # Basic API key format validation
            if not api_key.startswith("sk-ant-"):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Unauthorized",
                        "detail": "Invalid API key format",
                        "code": "INVALID_API_KEY",
                    },
                )

        # Rate limiting
        client_id = request.headers.get(
            "X-API-Key", request.client.host if request.client else "unknown"
        )

        if request.url.path == "/api/mcp/generate" and request.method == "POST":
            allowed, remaining = _rate_limiter.check_generation_limit(client_id)
            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate Limit Exceeded",
                        "detail": f"Generation rate limit exceeded. Try again in {_rate_limiter.window_seconds} seconds.",
                        "code": "RATE_LIMIT_EXCEEDED",
                    },
                    headers={
                        "X-RateLimit-Limit": str(_rate_limiter.generation_limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time() + _rate_limiter.window_seconds)),
                        "Retry-After": str(_rate_limiter.window_seconds),
                    },
                )

        elif request.url.path == "/api/mcp/execute" and request.method == "POST":
            allowed, remaining = _rate_limiter.check_execution_limit(client_id)
            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate Limit Exceeded",
                        "detail": f"Execution rate limit exceeded. Try again in {_rate_limiter.window_seconds} seconds.",
                        "code": "RATE_LIMIT_EXCEEDED",
                    },
                    headers={
                        "X-RateLimit-Limit": str(_rate_limiter.execution_limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time() + _rate_limiter.window_seconds)),
                        "Retry-After": str(_rate_limiter.window_seconds),
                    },
                )

        # Process request
        response = await call_next(request)

        # Add MCP-specific headers
        response.headers["X-MCP-Server"] = "UITestFlow-MCP"
        response.headers["X-MCP-Version"] = "1.0"

        return response


# ============================================================================
# MCP Logging Middleware
# ============================================================================


class MCPLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging MCP-specific requests and responses.

    Logs generation requests, execution requests, and any errors
    with MCP-specific context.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with logging.

        Args:
            request: Incoming request
            call_next: Next middleware in chain

        Returns:
            Response
        """
        # Only log MCP endpoints
        if not request.url.path.startswith("/api/mcp"):
            return await call_next(request)

        start_time = time.time()
        request_id = request.state.request_id if hasattr(request.state, "request_id") else "unknown"

        # Log request
        logger.info(
            f"MCP Request: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown",
            },
        )

        # Process request
        try:
            response = await call_next(request)
            duration_ms = int((time.time() - start_time) * 1000)

            # Log response
            logger.info(
                f"MCP Response: {response.status_code} in {duration_ms}ms",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "path": request.url.path,
                },
            )

            # Add duration header
            response.headers["X-Response-Time"] = f"{duration_ms}ms"

            return response

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            logger.error(
                f"MCP Error: {e!s} after {duration_ms}ms",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "duration_ms": duration_ms,
                    "path": request.url.path,
                },
                exc_info=True,
            )

            # Re-raise to let error handlers deal with it
            raise


# ============================================================================
# MCP Response Formatting Middleware
# ============================================================================


class MCPResponseMiddleware(BaseHTTPMiddleware):
    """
    Middleware for formatting MCP responses.

    Ensures consistent response format across all MCP endpoints.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with response formatting.

        Args:
            request: Incoming request
            call_next: Next middleware in chain

        Returns:
            Formatted response
        """
        # Only apply to MCP endpoints
        if not request.url.path.startswith("/api/mcp"):
            return await call_next(request)

        response = await call_next(request)

        # Add standard MCP metadata headers
        response.headers["X-MCP-Timestamp"] = str(int(time.time()))

        return response


# ============================================================================
# Exports
# ============================================================================


__all__ = [
    "MCPLoggingMiddleware",
    "MCPRateLimiter",
    "MCPResponseMiddleware",
    "MCPValidationMiddleware",
]
