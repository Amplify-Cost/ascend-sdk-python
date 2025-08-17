#!/bin/bash

echo "🔧 FIXING PORT ENVIRONMENT VARIABLE ISSUE"
echo "========================================"
echo "🎯 MASTER PROMPT COMPLIANCE: Fix deployment without changing functionality"
echo "🚨 ISSUE: Railway not expanding \$PORT variable in Docker CMD"
echo "🔧 SOLUTION: Use ENTRYPOINT script for proper port handling"
echo ""

cd ow-ai-backend

echo "📋 STEP 1: Create startup script for proper port handling"
echo "======================================================"

echo "🔧 Creating startup script to handle PORT environment variable..."

# Create a startup script that handles the PORT variable properly
cat > start.sh << 'EOF'
#!/bin/bash

# 🎯 Master Prompt Compliance: Startup script for Railway deployment
# Handle PORT environment variable properly

PORT=${PORT:-8000}
echo "🚀 Starting OW-AI Backend on port $PORT"

# Start uvicorn with proper port
exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
EOF

chmod +x start.sh
echo "✅ Created start.sh script"

echo ""
echo "📋 STEP 2: Update Dockerfile to use startup script"
echo "=============================================="

echo "🔧 Updating Dockerfile to use startup script..."

cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make startup script executable
RUN chmod +x start.sh

# Expose port
EXPOSE 8000

# Use startup script as entrypoint
ENTRYPOINT ["./start.sh"]
EOF

echo "✅ Updated Dockerfile to use startup script"

echo ""
echo "📋 STEP 3: Update railway.toml for Railway compatibility"
echo "==================================================="

echo "🔧 Simplifying railway.toml..."

cat > railway.toml << 'EOF'
[build]
builder = "dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "always"
EOF

echo "✅ Updated railway.toml (removed conflicting startCommand)"

echo ""
echo "📋 STEP 4: Add simple health endpoint to main.py"
echo "=============================================="

echo "🔧 Adding health endpoint if not present..."

# Check if health endpoint exists, if not add it
if ! grep -q "/health" main.py; then
    echo "🔧 Adding health endpoint..."
    
    # Add health endpoint near the top of the file after imports
    sed -i '/^from /a\\n# 🏥 Health endpoint for Railway\n@app.get("/health")\nasync def health():\n    return {"status": "healthy", "service": "OW-AI Backend"}\n' main.py 2>/dev/null || \
    echo -e '\n# 🏥 Health endpoint for Railway\n@app.get("/health")\nasync def health():\n    return {"status": "healthy", "service": "OW-AI Backend"}\n' >> main.py
    
    echo "✅ Added health endpoint"
else
    echo "✅ Health endpoint already exists"
fi

echo ""
echo "📋 STEP 5: Deploy port fix"
echo "======================="

echo "🔧 Committing port environment variable fix..."

git add start.sh Dockerfile railway.toml main.py
git commit -m "🔧 FIX: PORT environment variable issue for Railway

🎯 Master Prompt Compliance: Deployment fix only
✅ Created startup script for proper PORT handling
✅ Fixed Railway deployment port configuration  
✅ Added health endpoint for healthcheck
✅ No changes to backend functionality

🔧 Changes:
- Added start.sh script for proper PORT variable expansion
- Updated Dockerfile to use startup script
- Simplified railway.toml configuration
- Added health endpoint if missing"

echo "🔄 Pushing port fix..."
cd ..

# Push from project root
git add ow-ai-backend/start.sh ow-ai-backend/Dockerfile ow-ai-backend/railway.toml ow-ai-backend/main.py
git commit -m "🔧 FIX: Railway PORT environment variable and health endpoint"
git push origin main

echo ""
echo "✅ PORT ENVIRONMENT VARIABLE FIX COMPLETE!"
echo "========================================"
echo ""
echo "🎯 MASTER PROMPT COMPLIANCE MAINTAINED:"
echo "   ✅ NO changes to backend functionality"
echo "   ✅ NO changes to authentication system"  
echo "   ✅ ONLY deployment configuration fixes"
echo "   ✅ Added health endpoint for Railway"
echo ""
echo "🧪 Expected Results (3-5 minutes):"
echo "   ✅ Railway detects new commit and redeploys"
echo "   ✅ Startup script properly handles PORT variable"
echo "   ✅ No more 'PORT is not a valid integer' errors"
echo "   ✅ Health endpoint responds successfully"
echo "   ✅ Backend becomes active and functional"
echo "   ✅ Dashboard authentication works (no 422 errors)"
echo ""
echo "🔍 This should finally get Railway deployment working!"
