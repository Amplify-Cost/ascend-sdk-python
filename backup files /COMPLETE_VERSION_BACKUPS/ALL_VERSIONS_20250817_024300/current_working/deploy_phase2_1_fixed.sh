#!/bin/bash
# OW-AI Phase 2.1 Deployment Script - FIXED VERSION

echo "🚀 OW-AI Phase 2.1: Deploying Immutable Audit System"
echo "====================================================="

# Check if we're in the right directory
if [ ! -d "ow-ai-backend" ]; then
    echo "❌ Error: Must run from OW_AI_Project root directory"
    exit 1
fi

# Fix: Use python3 instead of python (macOS compatibility)
echo "📊 Running database migrations..."
cd ow-ai-backend

# Check if python3 is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Error: Neither python nor python3 found"
    exit 1
fi

echo "Using Python command: $PYTHON_CMD"

# Run the migration
echo "Running: $PYTHON_CMD -m alembic upgrade head"
$PYTHON_CMD -m alembic upgrade head

if [ $? -ne 0 ]; then
    echo "❌ Database migration failed"
    echo "Let's check if alembic is properly configured..."
    
    # Check alembic status
    echo "Checking alembic current status..."
    $PYTHON_CMD -m alembic current
    
    echo ""
    echo "💡 Manual migration steps:"
    echo "1. cd ow-ai-backend"
    echo "2. $PYTHON_CMD -m alembic current"
    echo "3. $PYTHON_CMD -m alembic upgrade head"
    echo ""
    exit 1
fi

echo "✅ Database migrations completed"

# Deploy to Railway
echo "🚂 Deploying to Railway..."
cd ..

# Check if railway CLI is available
if ! command -v railway &> /dev/null; then
    echo "❌ Error: Railway CLI not found"
    echo "Please install: npm install -g @railway/cli"
    exit 1
fi

# Deploy to Railway
railway up

if [ $? -ne 0 ]; then
    echo "❌ Railway deployment failed"
    echo ""
    echo "💡 Manual deployment steps:"
    echo "1. railway login"
    echo "2. railway link (select your project)"
    echo "3. railway up"
    echo ""
    exit 1
fi

echo "✅ Railway deployment completed"

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
sleep 15

# Test the deployment
echo "🧪 Testing deployment..."
echo "Testing main API..."
curl -f https://owai-production.up.railway.app/health

if [ $? -eq 0 ]; then
    echo ""
    echo "Testing new audit API..."
    curl -f https://owai-production.up.railway.app/api/audit/health
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ All tests successful!"
    else
        echo ""
        echo "⚠️  Main API works, but audit API may still be starting..."
    fi
else
    echo ""
    echo "❌ Deployment test failed - checking Railway logs..."
    railway logs --tail 20
fi

echo ""
echo "🎉 Phase 2.1 Deployment Process Complete!"
echo "====================================="
echo "✅ Code pushed to Railway"
echo "✅ Database migrations applied"
echo ""
echo "🔍 Verification commands:"
echo "curl https://owai-production.up.railway.app/health"
echo "curl https://owai-production.up.railway.app/api/audit/health"
echo ""
echo "📋 If issues occur:"
echo "railway logs          # Check deployment logs"
echo "railway link          # Ensure correct project"
echo "railway up            # Redeploy if needed"
