# UITestFlow Dockerfile - Multi-stage build for production deployment
# Stage 1: Base image with Python and system dependencies
FROM python:3.11-slim-bookworm AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies required for Playwright and PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for running the application
RUN groupadd -r uitest && useradd -r -g uitest -m -s /bin/bash uitest

# Set working directory
WORKDIR /app

# Stage 2: Builder stage for installing Python dependencies
FROM base AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium firefox webkit

# Stage 3: Production image
FROM base AS production

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

# Set PATH to use virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=uitest:uitest . /app

# Create directories for artifacts and ensure proper permissions
RUN mkdir -p /app/artifacts /app/logs /app/data && \
    chown -R uitest:uitest /app

# Switch to non-root user
USER uitest

# Expose ports
# 8080: FastAPI application
# 5555: Celery Flower (task monitoring)
EXPOSE 8080 5555

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health')" || exit 1

# Default command (can be overridden)
CMD ["uvicorn", "uitestflow.server.main:app", "--host", "0.0.0.0", "--port", "8080"]

# Stage 4: Development image
FROM builder AS development

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

# Copy application code
COPY . /app

# Create directories
RUN mkdir -p /app/artifacts /app/logs /app/data

# Expose additional ports for development
EXPOSE 8080 5555 8888

# Development command with hot reload
CMD ["uvicorn", "uitestflow.server.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]

# Stage 5: Test runner image
FROM development AS test

# Set test environment variables
ENV TESTING=1 \
    DATABASE_URL=postgresql://uitest:uitest@postgres:5432/uitest_test

# Run tests
CMD ["pytest", "-v", "--cov=uitestflow", "--cov-report=term-missing", "--cov-report=html"]

# Stage 6: CLI-only image (lightweight)
FROM base AS cli

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set PATH
ENV PATH="/opt/venv/bin:$PATH"

# Copy only CLI-related code
COPY --chown=uitest:uitest uitestflow/cli /app/uitestflow/cli
COPY --chown=uitest:uitest uitestflow/core /app/uitestflow/core
COPY --chown=uitest:uitest uitestflow/__init__.py /app/uitestflow/__init__.py

# Create directories
RUN mkdir -p /app/artifacts && chown -R uitest:uitest /app

# Switch to non-root user
USER uitest

# Set entrypoint to CLI
ENTRYPOINT ["uitestflow"]
CMD ["--help"]
