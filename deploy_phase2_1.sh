#!/bin/bash
# OW-AI Phase 2.1 Deployment Script

echo "🚀 OW-AI Phase 2.1: Deploying Immutable Audit System"
echo "====================================================="

# Check if we're in the right directory
if [ ! -d "ow-ai-backend" ]; then
    echo "❌ Error: Must run from OW_AI_Project root directory"
    exit 1
fi

echo "📊 Running database migrations..."
cd ow-ai-backend
python -m alembic upgrade head

if [ $? -ne 0 ]; then
    echo "❌ Database migration failed"
    exit 1
fi

echo "✅ Database migrations completed"

echo "🚂 Deploying to Railway..."
cd ..
railway up

echo "✅ Phase 2.1 Deployment Complete!"
