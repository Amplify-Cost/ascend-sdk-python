#!/usr/bin/env python3
"""
Enterprise Router Loading Diagnostic Script
Identifies why smart-rules router is not loading in Railway deployment
"""

import os
import sys
import importlib

def diagnose_router_loading():
    print("🔍 OW-AI Enterprise Router Loading Diagnosis")
    print("=" * 60)
    
    # Check if we're in the right directory
    current_dir = os.getcwd()
    print(f"📁 Current directory: {current_dir}")
    
    # Check for routes directory
    routes_dir = os.path.join(current_dir, "routes")
    if os.path.exists(routes_dir):
        print("✅ Routes directory exists")
        route_files = os.listdir(routes_dir)
        print(f"📄 Route files found: {route_files}")
    else:
        print("❌ Routes directory missing")
        return
    
    # Check for smart_rules_routes.py specifically
    smart_rules_file = os.path.join(routes_dir, "smart_rules_routes.py")
    if os.path.exists(smart_rules_file):
        print("✅ smart_rules_routes.py exists")
    else:
        print("❌ smart_rules_routes.py missing")
        return
    
    print("\n🔧 TESTING ROUTER IMPORTS")
    print("=" * 40)
    
    # Test importing smart_rules_routes
    try:
        # Add current directory to Python path
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        print("🧪 Testing: from routes.smart_rules_routes import router")
        from routes.smart_rules_routes import router as smart_rules_router
        print(f"✅ Smart rules router imported successfully: {type(smart_rules_router)}")
        
        # Check if router has endpoints
        if hasattr(smart_rules_router, 'routes'):
            print(f"📋 Router has {len(smart_rules_router.routes)} endpoints:")
            for route in smart_rules_router.routes:
                print(f"   {route.methods} {route.path}")
        else:
            print("⚠️  Router has no routes attribute")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 This explains why smart-rules endpoints return 404")
        return False
    except Exception as e:
        print(f"❌ General Error: {e}")
        return False
    
    print("\n🔧 TESTING DEPENDENCIES")
    print("=" * 30)
    
    # Test critical imports that smart_rules_routes needs
    dependencies_to_test = [
        "models",
        "database", 
        "dependencies",
        "schemas"
    ]
    
    for dep in dependencies_to_test:
        try:
            print(f"🧪 Testing: import {dep}")
            importlib.import_module(dep)
            print(f"✅ {dep} imported successfully")
        except ImportError as e:
            print(f"❌ {dep} import failed: {e}")
            print(f"💡 This could prevent smart_rules_routes from loading")
        except Exception as e:
            print(f"⚠️  {dep} import warning: {e}")
    
    print("\n🔧 MAIN.PY ANALYSIS")
    print("=" * 25)
    
    # Check main.py content
    main_file = os.path.join(current_dir, "main.py")
    if os.path.exists(main_file):
        print("✅ main.py exists")
        
        with open(main_file, 'r') as f:
            main_content = f.read()
        
        # Check for smart_rules mentions
        if "smart_rules" in main_content:
            print("✅ smart_rules mentioned in main.py")
        else:
            print("❌ smart_rules NOT mentioned in main.py")
            print("💡 This explains the 404 errors")
        
        # Check for ROUTE_MODULES
        if "ROUTE_MODULES" in main_content:
            print("✅ ROUTE_MODULES system found")
        else:
            print("❌ ROUTE_MODULES system missing")
        
        # Check for router inclusions
        smart_rules_includes = main_content.count("smart_rules")
        print(f"📊 smart_rules mentioned {smart_rules_includes} times in main.py")
        
    else:
        print("❌ main.py missing")
        return False
    
    print("\n📋 ENTERPRISE DIAGNOSIS SUMMARY")
    print("=" * 50)
    
    if "smart_rules" not in main_content:
        print("🚨 ROOT CAUSE: smart_rules router not included in main.py")
        print("🔧 FIX NEEDED: Add smart_rules to ROUTE_MODULES and router inclusion")
    else:
        print("🔍 Router mentioned in main.py but not loading properly")
        print("🔧 FIX NEEDED: Check router inclusion syntax and error handling")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Review main.py router loading section")  
    print("2. Ensure smart_rules is in ROUTER_NAMES list")
    print("3. Verify router inclusion in FastAPI app")
    print("4. Check for silent import failures")
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Enterprise Router Diagnosis...")
    diagnose_router_loading()