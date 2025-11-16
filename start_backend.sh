#!/bin/bash
# Backend Startup Script for OW-AI Project

echo "🔧 Stopping existing backend processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
pkill -9 -f "uvicorn|main.py" 2>/dev/null
sleep 2

echo "✅ Port 8000 cleared"
echo ""

echo "🚀 Starting backend on port 8000..."
echo ""

# Set environment variables
export DATABASE_URL="postgresql://mac_001@localhost:5432/owkai_pilot"
export SECRET_KEY="e54161f274a84e1426a6e0569d929bb6665cb968977c96fc3167d213ec584aca"
export ALGORITHM="HS256"
export ALLOWED_ORIGINS="http://localhost:5173"

# Start backend
cd /Users/mac_001/OW_AI_Project/ow-ai-backend
python3 main.py
