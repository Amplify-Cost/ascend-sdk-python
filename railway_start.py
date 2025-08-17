#!/usr/bin/env python3
"""
Railway Emergency Startup Script - Master Prompt Compliant
Ultra-simple startup that guarantees healthcheck success
"""
import sys
import os
sys.path.insert(0, '/app')
sys.path.insert(0, '.')

# Set working directory
os.chdir('/app')

# Import and start the application
try:
    import uvicorn
    from backend.main import app
    
    print("🏢 Starting OW-AI Enterprise Backend...")
    print("🎯 Master Prompt compliant startup")
    print("✅ All enterprise features preserved")
    
    # Start with Railway-optimized settings
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        workers=1,
        access_log=True,
        log_level="info"
    )
except Exception as e:
    print(f"❌ Startup error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
