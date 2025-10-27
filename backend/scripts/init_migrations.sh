#!/bin/bash
#
# Database Migration Initialization Script
# This script initializes the database and runs all pending migrations
#

set -e

echo "=== SOC Platform - Database Migration Initialization ==="
echo

# Load environment variables
if [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Check if PostgreSQL is running
echo "Checking PostgreSQL connection..."
if ! pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT > /dev/null 2>&1; then
    echo "ERROR: PostgreSQL is not running on $POSTGRES_HOST:$POSTGRES_PORT"
    echo "Please start PostgreSQL before running migrations"
    exit 1
fi

echo "✓ PostgreSQL is running"
echo

# Create database if it doesn't exist
echo "Creating database if needed..."
psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -tc "SELECT 1 FROM pg_database WHERE datname = '$POSTGRES_DB'" | grep -q 1 || \
    psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -c "CREATE DATABASE $POSTGRES_DB"

echo "✓ Database $POSTGRES_DB is ready"
echo

# Run migrations
echo "Running database migrations..."
cd ..
python3 -m alembic upgrade head

echo
echo "✓ Database migrations completed successfully"
echo
echo "=== Migration Summary ==="
python3 -m alembic current
echo
echo "All done!"