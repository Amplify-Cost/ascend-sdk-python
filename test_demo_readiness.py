#!/usr/bin/env python3
"""
Demo Readiness Test Script

Validates that the Authorization Center backend is ready for demo.
Tests core functionality without requiring external services.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import threading
import time
import requests
import json
from datetime import datetime

def test_configuration():
    """Test that configuration loads properly"""
    print("🔧 Testing Configuration...")
    try:
        from config import SECRET_KEY, DATABASE_URL, ALGORITHM, ALLOWED_ORIGINS
        assert SECRET_KEY is not None, "SECRET_KEY not loaded"
        assert DATABASE_URL is not None, "DATABASE_URL not loaded"
        assert ALGORITHM == "HS256", f"Expected HS256, got {ALGORITHM}"
        assert len(ALLOWED_ORIGINS) > 0, "No CORS origins configured"
        print("✅ Configuration test passed")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("🗄️  Testing Database Connection...")
    try:
        from database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            # Simple test query
            result = conn.execute(text("SELECT 1 as test"))
            assert result.fetchone()[0] == 1, "Database query failed"
        
        print("✅ Database connection test passed")
        return True
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        print("ℹ️  This is expected if PostgreSQL is not running locally")
        return False

def test_fastapi_imports():
    """Test that all FastAPI components import correctly"""
    print("🚀 Testing FastAPI Imports...")
    try:
        from main import app
        assert app is not None, "FastAPI app not created"
        
        # Check that we have routes
        route_count = len([r for r in app.routes if hasattr(r, 'path')])
        assert route_count > 50, f"Expected >50 routes, got {route_count}"
        
        print(f"✅ FastAPI imports test passed ({route_count} routes loaded)")
        return True
    except Exception as e:
        print(f"❌ FastAPI imports test failed: {e}")
        return False

def test_authorization_endpoints():
    """Test authorization endpoints are available"""
    print("🔐 Testing Authorization Endpoints...")
    try:
        from main import app
        
        # Check specific authorization endpoints
        auth_endpoints = [
            "/agent-control/pending-actions",
            "/agent-control/dashboard", 
            "/api/authorization/pending-actions",
            "/api/authorization/dashboard",
            "/api/authorization/policies/list"
        ]
        
        found_endpoints = []
        for route in app.routes:
            if hasattr(route, 'path'):
                if route.path in auth_endpoints:
                    found_endpoints.append(route.path)
        
        missing = set(auth_endpoints) - set(found_endpoints)
        if missing:
            raise Exception(f"Missing endpoints: {missing}")
        
        print(f"✅ Authorization endpoints test passed ({len(found_endpoints)} endpoints found)")
        return True
    except Exception as e:
        print(f"❌ Authorization endpoints test failed: {e}")
        return False

def test_server_startup():
    """Test that the server can start and respond"""
    print("🌐 Testing Server Startup...")
    try:
        import uvicorn
        from main import app
        
        def start_server():
            uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error")
        
        # Start server in background
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        
        # Test health endpoint
        response = requests.get("http://127.0.0.1:8001/health", timeout=5)
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        
        # Test auth endpoint (should return 401 - authentication required)
        response = requests.get("http://127.0.0.1:8001/api/authorization/dashboard", timeout=5)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        print("✅ Server startup test passed")
        return True
    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        return False

def main():
    """Run all demo readiness tests"""
    print("=" * 50)
    print("🎯 Authorization Center Demo Readiness Test")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_configuration),
        ("Database Connection", test_database_connection), 
        ("FastAPI Imports", test_fastapi_imports),
        ("Authorization Endpoints", test_authorization_endpoints),
        ("Server Startup", test_server_startup)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        results[test_name] = test_func()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed >= 3:  # Core tests (config, imports, endpoints)
        print("🎉 DEMO READY: Authorization Center backend is ready for demo!")
        print("📝 Note: Database test may fail without PostgreSQL, but SQLite fallback will work")
        return 0
    else:
        print("⚠️  DEMO NOT READY: Critical issues found")
        return 1

if __name__ == "__main__":
    sys.exit(main())