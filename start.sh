#!/bin/bash

# Exit on any error
set -e

echo "🚀 Starting Tech11 Backend..."

# Wait for database to be ready (if using external DB)
echo "⏳ Waiting for database to be ready..."

# Check if alembic directory and config exist
echo "🔍 Checking alembic configuration..."
if [ ! -f "alembic.ini" ]; then
    echo "❌ alembic.ini not found!"
    exit 1
fi

if [ ! -d "alembic" ]; then
    echo "❌ alembic directory not found!"
    exit 1
fi

echo "✅ Alembic configuration found"

# Run database migrations
echo "📊 Running database migrations..."
cd /app && uv run alembic upgrade head

# Check if migrations were successful
if [ $? -eq 0 ]; then
    echo "✅ Database migrations completed successfully"
else
    echo "❌ Database migrations failed"
    exit 1
fi

# Start the FastAPI application
echo "🌟 Starting FastAPI application..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
