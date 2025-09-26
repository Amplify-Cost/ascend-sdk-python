#!/bin/bash
set -e

echo "🏢 ENTERPRISE: Starting OW-AI Backend..."

# Run database migrations
echo "📊 Running database migrations..."
alembic upgrade head || echo "⚠️ Migration failed, continuing..."

# Start the application
echo "🚀 Starting application server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
