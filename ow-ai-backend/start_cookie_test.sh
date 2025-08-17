#!/bin/bash

echo "🚀 Starting Cookie Authentication Test Server..."
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "main_simple.py" ]; then
    echo "❌ main_simple.py not found. Run setup script first."
    exit 1
fi

# Start the server
echo "Starting server on http://localhost:8002"
echo "Press Ctrl+C to stop"
echo ""

python3 main_simple.py
