#!/bin/bash
# Script to set up UITestFlow database on local PostgreSQL installation
# Works with PostgreSQL installed via Homebrew, apt, or any other method

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Default database configuration
DB_NAME="${DB_NAME:-uitestflow}"
DB_USER="${DB_USER:-uitest}"
DB_PASSWORD="${DB_PASSWORD:-uitest}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "=========================================="
echo "UITestFlow Local PostgreSQL Setup"
echo "=========================================="
echo ""
echo "Database Configuration:"
echo "  Host:     $DB_HOST"
echo "  Port:     $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User:     $DB_USER"
echo ""

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "ERROR: psql command not found"
    echo ""
    echo "Please install PostgreSQL:"
    echo "  macOS:   brew install postgresql@16"
    echo "  Ubuntu:  sudo apt install postgresql postgresql-contrib"
    echo "  Fedora:  sudo dnf install postgresql postgresql-server"
    echo ""
    exit 1
fi

# Check PostgreSQL version
POSTGRES_VERSION=$(psql --version | awk '{print $3}' | cut -d'.' -f1)
echo "Detected PostgreSQL version: $POSTGRES_VERSION"
echo ""

# Check if PostgreSQL is running
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" &> /dev/null; then
    echo "ERROR: PostgreSQL is not running on $DB_HOST:$DB_PORT"
    echo ""
    echo "Start PostgreSQL:"
    echo "  macOS (Homebrew):  brew services start postgresql@16"
    echo "  Linux (systemd):   sudo systemctl start postgresql"
    echo "  Manual:            pg_ctl -D /path/to/data start"
    echo ""
    exit 1
fi

echo "✓ PostgreSQL is running"
echo ""

# Create user if it doesn't exist
echo "Creating database user '$DB_USER'..."
if psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
    echo "✓ User '$DB_USER' already exists"
else
    psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" || {
        echo ""
        echo "Note: If you got 'peer authentication failed', try:"
        echo "  sudo -u postgres psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';\""
        echo ""
        echo "Or set PGUSER and PGPASSWORD environment variables:"
        echo "  export PGUSER=postgres"
        echo "  export PGPASSWORD=yourpassword"
        echo ""
        exit 1
    }
    echo "✓ User '$DB_USER' created"
fi

# Create database if it doesn't exist
echo ""
echo "Creating database '$DB_NAME'..."
if psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "✓ Database '$DB_NAME' already exists"
else
    psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" || {
        echo ""
        echo "Note: If you got authentication errors, try:"
        echo "  sudo -u postgres psql -c \"CREATE DATABASE $DB_NAME OWNER $DB_USER;\""
        exit 1
    }
    echo "✓ Database '$DB_NAME' created"
fi

# Grant privileges
echo ""
echo "Granting privileges..."
psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null || true
echo "✓ Privileges granted"

# Test connection
echo ""
echo "Testing connection..."
if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" &> /dev/null; then
    echo "✓ Connection successful"
else
    echo "✗ Connection failed"
    echo ""
    echo "Try connecting manually:"
    echo "  PGPASSWORD='$DB_PASSWORD' psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
    exit 1
fi

# Create .env file if it doesn't exist
ENV_FILE="$PROJECT_ROOT/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo ""
    echo "Creating .env file..."
    cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
    echo "✓ Created .env from .env.example"
fi

# Update DATABASE_URL in .env
echo ""
echo "Updating DATABASE_URL in .env..."
DATABASE_URL="postgresql+asyncpg://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"

if grep -q "^DATABASE_URL=" "$ENV_FILE"; then
    # Update existing line (works on both macOS and Linux)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|^DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|" "$ENV_FILE"
    else
        sed -i "s|^DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|" "$ENV_FILE"
    fi
    echo "✓ Updated DATABASE_URL in .env"
else
    echo "DATABASE_URL=$DATABASE_URL" >> "$ENV_FILE"
    echo "✓ Added DATABASE_URL to .env"
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Database Connection Details:"
echo "  Connection URL: $DATABASE_URL"
echo "  Direct psql:    PGPASSWORD='$DB_PASSWORD' psql -h $DB_HOST -U $DB_USER -d $DB_NAME"
echo ""
echo "The tables will be created automatically when you start the server:"
echo "  uitestflow serve"
echo ""
echo "To verify the setup worked:"
echo "  export DATABASE_URL='$DATABASE_URL'"
echo "  uitestflow serve"
echo ""
