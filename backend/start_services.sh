#!/bin/bash

# SOC Platform - Service Startup Script

echo "============================================"
echo "SOC Platform - Starting Services"
echo "============================================"

# Check if Homebrew is available (macOS)
if command -v brew &> /dev/null; then
    echo "✓ Homebrew detected"

    # Start PostgreSQL
    echo ""
    echo "Starting PostgreSQL..."
    if brew services list | grep -q "postgresql.*started"; then
        echo "✓ PostgreSQL is already running"
    else
        brew services start postgresql@14 2>/dev/null || brew services start postgresql
        echo "✓ PostgreSQL started"
    fi

    # Start Redis
    echo ""
    echo "Starting Redis..."
    if brew services list | grep -q "redis.*started"; then
        echo "✓ Redis is already running"
    else
        brew services start redis
        echo "✓ Redis started"
    fi

    # Wait for services to be ready
    echo ""
    echo "Waiting for services to be ready..."
    sleep 3

    # Check PostgreSQL
    if lsof -i :5432 &> /dev/null; then
        echo "✓ PostgreSQL is listening on port 5432"
    else
        echo "⚠ PostgreSQL may not be ready yet"
    fi

    # Check Redis
    if lsof -i :6379 &> /dev/null; then
        echo "✓ Redis is listening on port 6379"
    else
        echo "⚠ Redis may not be ready yet"
    fi

else
    echo "⚠ Homebrew not found. Please start services manually:"
    echo ""
    echo "PostgreSQL:"
    echo "  sudo systemctl start postgresql"
    echo "  or"
    echo "  pg_ctl -D /usr/local/var/postgres start"
    echo ""
    echo "Redis:"
    echo "  sudo systemctl start redis"
    echo "  or"
    echo "  redis-server"
fi

echo ""
echo "============================================"
echo "Services startup complete"
echo "============================================"
echo ""
echo "To verify, run: python3 test_connectivity.py"