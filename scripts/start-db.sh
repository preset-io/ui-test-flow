#!/bin/bash
# Quick script to start just the database services for local development

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

echo "Starting UITestFlow database services..."
echo ""

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed or not in PATH"
    echo "Please install Docker from https://www.docker.com/get-started"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: docker-compose is not installed or not in PATH"
    echo "Please install docker-compose"
    exit 1
fi

# Start only the database services
echo "Starting PostgreSQL and Redis..."
docker-compose up -d postgres redis

# Wait for PostgreSQL to be ready
echo ""
echo "Waiting for PostgreSQL to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker-compose exec -T postgres pg_isready -U uitest &> /dev/null; then
        echo "PostgreSQL is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "Attempt $attempt/$max_attempts - waiting..."
    sleep 1
done

if [ $attempt -eq $max_attempts ]; then
    echo "ERROR: PostgreSQL failed to start within 30 seconds"
    exit 1
fi

# Wait for Redis to be ready
echo ""
echo "Waiting for Redis to be ready..."
max_attempts=10
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker-compose exec -T redis redis-cli ping &> /dev/null; then
        echo "Redis is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "Attempt $attempt/$max_attempts - waiting..."
    sleep 1
done

if [ $attempt -eq $max_attempts ]; then
    echo "ERROR: Redis failed to start within 10 seconds"
    exit 1
fi

echo ""
echo "✅ Database services are running!"
echo ""
echo "Connection details:"
echo "  PostgreSQL: postgresql://uitest:uitest@localhost:5432/uitest"
echo "  Redis: redis://localhost:6379/0"
echo ""
echo "You can now start the UITestFlow server with:"
echo "  uitestflow serve"
echo "  or: make serve"
echo ""
echo "To stop the database services:"
echo "  docker-compose down"
