#!/bin/bash
set -e

# ARCH-003 Fix: Clear Python bytecode cache
echo "🧹 Clearing Python bytecode cache..."
find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find /app -type f -name "*.pyc" -delete 2>/dev/null || true
find /app -type f -name "*.pyo" -delete 2>/dev/null || true
echo "✅ Python cache cleared"

echo "🏢 ENTERPRISE: Starting OW-AI Backend..."

# Wait for database
echo "⏳ Waiting for database..."
sleep 5

# CR-20251208-ADMIN: Removed hardcoded admin user creation
# Users are now created ONLY via onboard_pilot_customer.py script

echo "🔧 Running Alembic migrations..."
alembic upgrade head || echo "⚠️ Migration failed or already applied"

echo "🚀 Starting application server..."
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000
