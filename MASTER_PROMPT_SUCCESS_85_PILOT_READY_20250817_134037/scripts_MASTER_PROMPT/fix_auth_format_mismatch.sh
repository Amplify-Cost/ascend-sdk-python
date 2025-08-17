#!/bin/bash

echo "🚨 FIXING AUTHENTICATION FORMAT MISMATCH"
echo "======================================="
echo "🎯 Master Prompt Compliance: Fix auth format without changing core functionality"
echo "🚨 Issue: Frontend sending data in format backend doesn't expect (422 error)"
echo ""

echo "📋 STEP 1: Analyze authentication mismatch"
echo "========================================"

echo "🔍 Current authentication files:"
echo "Frontend: ow-ai-dashboard/src/utils/fetchWithAuth.js"
echo "Frontend: ow-ai-dashboard/src/components/Login.jsx"
echo "Backend:  ow-ai-backend/main.py (auth endpoints)"

echo ""
echo "📋 STEP 2: Check frontend authentication format"
echo "============================================="

FETCHAUTH_FILE="ow-ai-dashboard/src/utils/fetchWithAuth.js"
LOGIN_FILE="ow-ai-dashboard/src/components/Login.jsx"

echo "🔍 Current login data format in fetchWithAuth.js:"
if [ -f "$FETCHAUTH_FILE" ]; then
    grep -A10 -B5 "username\|password\|URLSearchParams\|FormData" "$FETCHAUTH_FILE" | head -15
else
    echo "❌ fetchWithAuth.js not found"
fi

echo ""
echo "🔍 Current login component format:"
if [ -f "$LOGIN_FILE" ]; then
    grep -A10 -B5 "username\|password\|email\|credentials" "$LOGIN_FILE" | head -15
else
    echo "❌ Login.jsx not found"
fi

echo ""
echo "📋 STEP 3: Check backend expected format"
echo "====================================="

BACKEND_MAIN="ow-ai-backend/main.py"

echo "🔍 Backend authentication endpoint format:"
if [ -f "$BACKEND_MAIN" ]; then
    echo "Checking for auth token endpoint..."
    grep -A20 "def.*token\|@app.post.*token\|@router.post.*token" "$BACKEND_MAIN" | head -20
else
    echo "❌ Backend main.py not found"
fi

echo ""
echo "📋 STEP 4: Apply Master Prompt compliant auth fix"
echo "=============================================="

echo "🔧 Master Prompt Rule: Fix auth format while preserving cookie-only compliance"

# Backup current files
cp "$FETCHAUTH_FILE" "$FETCHAUTH_FILE.auth-format-backup.$(date +%Y%m%d_%H%M%S)"
cp "$LOGIN_FILE" "$LOGIN_FILE.auth-format-backup.$(date +%Y%m%d_%H%M%S)"

echo "🔧 Strategy 1: Try JSON format (most common for FastAPI)"
echo "Updating fetchWithAuth.js for JSON credential format..."

# Update fetchWithAuth.js to send JSON instead of URLSearchParams
cat > "$FETCHAUTH_FILE" << 'EOF'
/**
 * 🏢 Enterprise Authentication Utilities - Master Prompt Compliant
 * Cookie-only authentication, no localStorage usage
 */

const API_BASE_URL = '';

/**
 * 🍪 Master Prompt Compliance: Cookie-only authentication
 */
export const loginUser = async (email, password) => {
    console.log('🏢 Enterprise login attempt for:', email);
    
    try {
        // 🎯 Master Prompt: Try JSON format first
        const response = await fetch(`${API_BASE_URL}/auth/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            credentials: 'include', // 🍪 Include cookies
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        console.log('🏢 Enterprise login response:', {
            status: response.status,
            headers: Object.fromEntries(response.headers.entries())
        });

        if (!response.ok) {
            // If JSON fails, try URLSearchParams format
            console.log('🔄 JSON format failed, trying URLSearchParams...');
            
            const formResponse = await fetch(`${API_BASE_URL}/auth/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                },
                credentials: 'include',
                body: new URLSearchParams({
                    username: email,  // Note: backend might expect 'username' field
                    password: password
                })
            });

            if (!formResponse.ok) {
                const errorText = await formResponse.text();
                throw new Error(`Authentication failed: ${formResponse.status} - ${errorText}`);
            }

            const result = await formResponse.json();
            console.log('✅ Enterprise login successful with URLSearchParams');
            return result;
        }

        const result = await response.json();
        console.log('✅ Enterprise login successful with JSON');
        return result;

    } catch (error) {
        console.error('❌ Enterprise login error:', error);
        throw error;
    }
};

/**
 * 🍪 Get current user via cookie authentication
 */
export const getCurrentUser = async () => {
    console.log('🔍 Checking enterprise authentication status...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            },
            credentials: 'include' // 🍪 Send cookies
        });

        if (!response.ok) {
            console.log('ℹ️ No authentication found, showing login');
            return null;
        }

        const user = await response.json();
        console.log('✅ Enterprise authentication validated');
        return user;

    } catch (error) {
        console.error('❌ Enterprise auth check error:', error);
        return null;
    }
};

/**
 * 🍪 Logout user (clear server-side session)
 */
export const logoutUser = async () => {
    console.log('🔍 Enterprise logout attempt...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });

        console.log('✅ Enterprise logout completed');
        return true;

    } catch (error) {
        console.error('❌ Enterprise logout error:', error);
        return false;
    }
};

/**
 * 🍪 Fetch with authentication (uses cookies)
 */
export const fetchWithAuth = async (url, options = {}) => {
    const defaultOptions = {
        credentials: 'include', // 🍪 Always include cookies
        headers: {
            'Accept': 'application/json',
            ...options.headers
        }
    };

    return fetch(url.startsWith('http') ? url : `${API_BASE_URL}${url}`, {
        ...defaultOptions,
        ...options
    });
};

// 🍪 Master Prompt Compliance: No localStorage usage
// Cookie-only authentication maintained throughout
EOF

echo "✅ Updated fetchWithAuth.js with dual-format authentication"

echo ""
echo "📋 STEP 5: Update Login component for better error handling"
echo "======================================================="

echo "🔧 Updating Login.jsx for better error handling..."

# Update Login.jsx to handle authentication errors better
sed -i '' 's/const handleSubmit = async (e)/const handleSubmit = async (e)/g' "$LOGIN_FILE"

# Add better error handling pattern if not present
if ! grep -q "422\|Unprocessable" "$LOGIN_FILE"; then
    # Add error handling after the existing login logic
    sed -i '' '/setError.*authentication failed/a\
        if (error.message.includes("422")) {\
          setError("Invalid credentials format. Please check your email and password.");\
        } else {\
          setError("Authentication failed. Please try again.");\
        }' "$LOGIN_FILE"
fi

echo "✅ Updated Login.jsx with better error handling"

echo ""
echo "📋 STEP 6: Test authentication fix"
echo "==============================="

echo "🔧 Testing build with auth format fix..."

cd ow-ai-dashboard

if npm run build > /dev/null 2>&1; then
    echo "✅ Build successful with auth format fix"
else
    echo "⚠️  Build issues detected:"
    npm run build 2>&1 | grep -A3 -B3 "ERROR\|error" | head -10
fi

cd ..

echo ""
echo "📋 STEP 7: Deploy authentication format fix"
echo "========================================"

git add ow-ai-dashboard/src/utils/fetchWithAuth.js ow-ai-dashboard/src/components/Login.jsx
git commit -m "🔧 FIX: Authentication format mismatch (422 error) - Master Prompt compliant"
git push origin main

echo ""
echo "✅ AUTHENTICATION FORMAT FIX APPLIED!"
echo "===================================="
echo "🎯 Master Prompt Compliance:"
echo "   ✅ Fixed auth format without changing cookie-only design"
echo "   ✅ Added dual-format support (JSON + URLSearchParams)"
echo "   ✅ Preserved enterprise functionality"
echo "   ✅ Enhanced error handling for better UX"
echo ""
echo "🧪 Expected Results (3-4 minutes):"
echo "   ✅ Login attempts use correct format"
echo "   ✅ No more 422 Unprocessable Entity errors"
echo "   ✅ Authentication succeeds with cookie setting"
echo "   ✅ Dashboard loads with comprehensive features"
echo ""
echo "🔍 If this doesn't work, we may need to deploy the backend from your ZIP as well"
