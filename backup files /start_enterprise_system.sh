#!/bin/bash

# Enterprise System Startup Script
# ================================

echo "🏢 Starting OW-AI Enterprise System..."
echo "====================================="

# Function to check if port is in use
check_port() {
    if lsof -i :$1 > /dev/null 2>&1; then
        echo "⚠️  Port $1 is already in use"
        return 1
    fi
    return 0
}

# Start backend
echo "🚀 Starting Enterprise Backend (Port 8000)..."
cd ow-ai-backend
if check_port 8000; then
    python3 main.py &
    BACKEND_PID=$!
    echo "✅ Backend started (PID: $BACKEND_PID)"
else
    echo "❌ Cannot start backend - port 8000 in use"
fi

# Wait for backend to start
sleep 3

# Start frontend
echo "🚀 Starting Enterprise Frontend (Port 5174)..."
cd ../ow-ai-dashboard
if check_port 5174; then
    npm run dev &
    FRONTEND_PID=$!
    echo "✅ Frontend started (PID: $FRONTEND_PID)"
else
    echo "❌ Cannot start frontend - port 5174 in use"
fi

# Start SDK Portal
echo "🚀 Starting SDK Portal (Port 8001)..."
cd ../ow-ai-sdk
if check_port 8001; then
    python3 main.py &
    SDK_PID=$!
    echo "✅ SDK Portal started (PID: $SDK_PID)"
else
    echo "❌ Cannot start SDK portal - port 8001 in use"
fi

echo ""
echo "🎉 Enterprise System Status:"
echo "=============================="
echo "🔧 Backend API:     http://localhost:8000"
echo "🖥️  Frontend:       http://localhost:5174"  
echo "📚 SDK Portal:      http://localhost:8001"
echo ""
echo "🧪 Run validation:  ./validate_enterprise_integration.sh"
echo "🛑 Stop all:        pkill -f 'python3 main.py' && pkill -f 'npm run dev'"
