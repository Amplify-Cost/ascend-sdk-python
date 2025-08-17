#!/bin/bash

# 🎯 Master Prompt Compliance: Startup script for Railway deployment
# Handle PORT environment variable properly

PORT=${PORT:-8000}
echo "🚀 Starting OW-AI Backend on port $PORT"

# Start uvicorn with proper port
exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
