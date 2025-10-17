#!/usr/bin/env python3
"""
Authorization Center Demo Startup Script

Starts the backend server with proper configuration for demo purposes.
Includes SQLite fallback if PostgreSQL is not available.
"""

import os
import sys
import uvicorn
import logging
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def setup_demo_environment():
    """Setup environment variables for demo"""
    
    # Ensure we have all required environment variables
    demo_env = {
        'ENVIRONMENT': 'development',
        'SECRET_KEY': 'demo-secret-key-change-in-production-12345678901234567890',
        'ALGORITHM': 'HS256',
        'ACCESS_TOKEN_EXPIRE_MINUTES': '30',
        'REFRESH_TOKEN_EXPIRE_DAYS': '7',
        'ALLOWED_ORIGINS': 'http://localhost:3000,http://localhost:5173,https://pilot.owkai.app',
        'LOG_LEVEL': 'INFO',
        'OPENAI_API_KEY': 'demo-key-replace-with-real-key'
    }
    
    # Set environment variables if not already set
    for key, value in demo_env.items():
        if not os.getenv(key):
            os.environ[key] = value
    
    # Try PostgreSQL first, fall back to SQLite
    if not os.getenv('DATABASE_URL'):
        postgres_url = 'postgresql://localhost:5432/owai_dev'
        sqlite_url = 'sqlite:///./owai_demo.db'
        
        try:
            # Test PostgreSQL connection
            import psycopg2
            psycopg2.connect(
                host='localhost',
                port=5432,
                database='owai_dev',
                user='postgres',
                connect_timeout=3
            ).close()
            os.environ['DATABASE_URL'] = postgres_url
            print("✅ Using PostgreSQL database")
        except Exception:
            os.environ['DATABASE_URL'] = sqlite_url
            print("⚠️  PostgreSQL not available, using SQLite database")

def main():
    """Start the demo server"""
    print("🎯 Starting Authorization Center Demo Backend")
    print("=" * 50)
    
    # Setup environment
    setup_demo_environment()
    
    try:
        # Test imports first
        print("🔧 Testing imports...")
        from main import app
        print("✅ All imports successful")
        
        # Start the server
        print("\n🚀 Starting server on http://localhost:8000")
        print("📱 Frontend should connect to: http://localhost:8000")
        print("📖 API docs available at: http://localhost:8000/docs")
        print("\n⚠️  Press Ctrl+C to stop the server")
        print("=" * 50)
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False,
            access_log=True
        )
        
    except KeyboardInterrupt:
        print("\n👋 Demo server stopped")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()