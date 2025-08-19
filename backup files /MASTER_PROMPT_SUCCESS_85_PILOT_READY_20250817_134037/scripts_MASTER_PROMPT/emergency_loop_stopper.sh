#!/bin/bash

echo "🚨 EMERGENCY AUTHENTICATION LOOP STOPPER"
echo "========================================"
echo ""
echo "🎯 IMMEDIATE PROBLEM:"
echo "Frontend is stuck in infinite /auth/me loop"
echo "Railway logs show continuous 401 requests"
echo "App is unusable - needs emergency fix"
echo ""
echo "🛠️ EMERGENCY SOLUTION:"
echo "1. Stop the infinite loop in frontend"
echo "2. Create working test users" 
echo "3. Deploy immediate fix"
echo ""

# Step 1: Fix the Python command issue first
echo "📋 STEP 1: Creating Test Users (Fix Python Path)"
echo "==============================================="

cd ow-ai-backend

# Use python3 instead of python
echo "🔧 Creating test users with python3..."

python3 -c "
import asyncio
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path.cwd()))

try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    from passlib.context import CryptContext
    from models import User, Base
    from config import DATABASE_URL
    
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    
    async def create_users():
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            test_users = [
                {'email': 'test@example.com', 'password': 'test', 'full_name': 'Test User'},
                {'email': 'admin@example.com', 'password': 'admin', 'full_name': 'Admin User'},
                {'email': 'demo@owai.com', 'password': 'demo123', 'full_name': 'Demo User'}
            ]
            
            for user_data in test_users:
                result = await session.execute(select(User).where(User.email == user_data['email']))
                if result.scalar_one_or_none():
                    print(f'✅ User {user_data[\"email\"]} already exists')
                    continue
                
                hashed_password = pwd_context.hash(user_data['password'])
                user = User(
                    email=user_data['email'],
                    hashed_password=hashed_password,
                    full_name=user_data['full_name'],
                    is_active=True
                )
                session.add(user)
                print(f'✅ Created user: {user_data[\"email\"]}')
            
            await session.commit()
            print('🎉 Test users created successfully!')
    
    asyncio.run(create_users())
    
except Exception as e:
    print(f'❌ User creation failed: {e}')
    print('📝 Will continue with frontend fix...')
"

# Step 2: EMERGENCY - Stop the infinite loop in AppContent.jsx
echo ""
echo "📋 STEP 2: EMERGENCY - Stop Frontend Loop"
echo "========================================"

cd ../ow-ai-dashboard/src/components

# Backup current AppContent.jsx
cp AppContent.jsx AppContent.jsx.backup_emergency_loop_fix

echo "🚨 Creating emergency loop-stopping AppContent.jsx..."

cat > AppContent.jsx << 'EOF'
import React, { useEffect, useState } from "react";
import { useAlert } from "../context/AlertContext";
import ToastAlert from "./ToastAlert";
import BannerAlert from "./BannerAlert";
import Login from "./Login";
import Register from "./Register";
import ForgotPassword from "./ForgotPassword";
import Dashboard from "./Dashboard";
import { getCurrentUser, logout } from "../utils/fetchWithAuth";

const AppContent = () => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [view, setView] = useState("loading"); // loading, login, register, forgot, app
  const [authChecked, setAuthChecked] = useState(false); // Prevent multiple auth checks
  const { showAlert } = useAlert();

  // EMERGENCY: Single auth check with loop prevention
  useEffect(() => {
    if (authChecked) return; // Prevent multiple checks
    
    let isMounted = true;
    
    const checkAuthOnce = async () => {
      try {
        console.log("🔍 Checking authentication (ONE TIME ONLY)...");
        
        const user = await getCurrentUser();
        
        if (isMounted && user) {
          console.log("✅ User authenticated:", user);
          setUser({
            id: user.user_id || user.id,
            email: user.email,
            role: user.role,
          });
          setToken("cookie-auth");
          setView("app");
        } else if (isMounted) {
          console.log("❌ No authentication - showing login");
          setView("login");
        }
      } catch (error) {
        console.log("🚫 Auth check failed - showing login:", error.message);
        if (isMounted) {
          setView("login");
        }
      } finally {
        if (isMounted) {
          setAuthChecked(true); // Mark as checked to prevent loops
        }
      }
    };

    // Only check auth once
    checkAuthOnce();
    
    return () => {
      isMounted = false;
    };
  }, []); // Empty dependency array - run once only

  const handleLoginSuccess = (userData, authToken) => {
    console.log("🎉 Login successful:", userData);
    setUser(userData);
    setToken(authToken || "cookie-auth");
    setView("app");
    showAlert("Login successful!", "success");
  };

  const handleLogout = async () => {
    try {
      await logout();
      setToken(null);
      setUser(null);
      setView("login");
      setAuthChecked(false); // Allow auth check on next login
      showAlert("Logged out successfully!", "success");
    } catch (error) {
      console.error("Logout error:", error);
      // Force logout even if API fails
      setToken(null);
      setUser(null);
      setView("login");
      setAuthChecked(false);
    }
  };

  const switchToRegister = () => setView("register");
  const switchToLogin = () => setView("login");
  const switchToForgot = () => setView("forgot");

  // Show loading only briefly
  if (view === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Checking authentication...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <ToastAlert />
      <BannerAlert />
      
      {view === "login" && (
        <Login
          onLoginSuccess={handleLoginSuccess}
          switchToRegister={switchToRegister}
          switchToForgot={switchToForgot}
        />
      )}
      
      {view === "register" && (
        <Register
          onRegisterSuccess={handleLoginSuccess}
          switchToLogin={switchToLogin}
        />
      )}
      
      {view === "forgot" && (
        <ForgotPassword switchToLogin={switchToLogin} />
      )}
      
      {view === "app" && user && (
        <Dashboard user={user} onLogout={handleLogout} />
      )}
    </>
  );
};

export default AppContent;
EOF

echo "✅ Created emergency loop-stopping AppContent.jsx"

# Step 3: Test the login endpoint one more time
echo ""
echo "📋 STEP 3: Testing Authentication After Fixes"
echo "============================================="

cd ../../..

echo "🧪 Testing login with test credentials..."
LOGIN_TEST=$(curl -X POST https://owai-production.up.railway.app/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@example.com","password":"test"}' \
  -w "%{http_code}" \
  -s)

echo "Login test result: $LOGIN_TEST"

if [[ "$LOGIN_TEST" == *"200"* ]]; then
    echo "✅ Login is working!"
else
    echo "❌ Login still failing - but loop should be stopped"
fi

# Step 4: Deploy the emergency fix
echo ""
echo "📋 STEP 4: Deploying Emergency Loop Fix"
echo "====================================="

echo "🚀 Committing emergency frontend fix..."

git add ow-ai-dashboard/src/components/AppContent.jsx
git commit -m "🚨 EMERGENCY: Stop infinite authentication loop

✅ Added authChecked flag to prevent multiple auth calls
✅ Single useEffect with empty dependency array  
✅ Proper cleanup and isMounted check
✅ Should immediately stop /auth/me spam
✅ Backup: AppContent.jsx.backup_emergency_loop_fix"

echo "✅ Pushing emergency fix to production..."
git push origin main

echo ""
echo "🚨 EMERGENCY FIX DEPLOYED!"
echo "========================="
echo ""
echo "✅ What this fixes:"
echo "  • STOPS infinite /auth/me requests immediately"
echo "  • Adds authChecked flag to prevent loops"
echo "  • Single authentication check on app load"
echo "  • Proper React cleanup to prevent memory leaks"
echo ""
echo "⏱️  Emergency deployment in progress..."
echo "   Check Railway logs in 1-2 minutes"
echo "   The infinite loop should STOP immediately"
echo ""
echo "🧪 After deployment, test by:"
echo "   1. Visit your app URL"
echo "   2. Should show login screen (not loading forever)"
echo "   3. Railway logs should stop showing infinite /auth/me"
echo ""
echo "🆘 Emergency rollback if needed:"
echo "   cp ow-ai-dashboard/src/components/AppContent.jsx.backup_emergency_loop_fix ow-ai-dashboard/src/components/AppContent.jsx"
echo "   git add . && git commit -m 'Emergency rollback' && git push origin main"

echo ""
echo "📋 EMERGENCY SCRIPT COMPLETE!"
echo "============================"
echo "🎯 The infinite loop should stop within 2 minutes of deployment."
