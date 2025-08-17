#!/bin/bash

echo "🔒 FIXING SECURE COOKIE CONFIGURATION"
echo "===================================="
echo "🎯 Master Prompt Compliance: Ensure secure cookie settings"

# Check current cookie configuration
echo "🔍 Checking current cookie configuration in main.py..."

# Look for cookie configuration patterns
echo ""
echo "📊 Current cookie patterns:"
grep -n -i "cookie\|httponly\|secure\|samesite" main.py | head -10

echo ""
echo "🔧 Adding/fixing secure cookie configuration..."

# Create a temporary fix file
cat > fix_cookie_security.py << 'COOKIE_FIX_EOF'
import re

# Read the current main.py
with open('main.py', 'r') as f:
    content = f.read()

# Check if secure cookie middleware already exists
if 'cookie_security_middleware' in content:
    print("✅ Cookie security middleware found, enhancing...")
    
    # Enhance existing middleware
    enhanced_middleware = '''
@app.middleware("http")
async def cookie_security_middleware(request: Request, call_next):
    """Master Prompt compliant: Enhanced cookie security middleware"""
    
    # Log cookie-only authentication attempts
    if request.url.path.startswith("/auth/"):
        print(f"🍪 Cookie auth request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    # Enhanced security headers for cookie protection
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Ensure all auth cookies are secure (FIXED)
    if "Set-Cookie" in response.headers:
        cookie_value = response.headers["Set-Cookie"]
        if "access_token" in cookie_value or "session_token" in cookie_value:
            # Force Master Prompt compliance with proper secure settings
            if "HttpOnly" not in cookie_value:
                cookie_value += "; HttpOnly"
            if "Secure" not in cookie_value:
                cookie_value += "; Secure"
            if "SameSite=Strict" not in cookie_value:
                cookie_value += "; SameSite=Strict"
            
            response.headers["Set-Cookie"] = cookie_value
            print(f"🔒 Secured cookie: {cookie_value[:50]}...")
    
    return response
'''
    
    # Replace the existing middleware with enhanced version
    content = re.sub(
        r'@app\.middleware\("http"\)\s*async def cookie_security_middleware.*?return response',
        enhanced_middleware.strip(),
        content,
        flags=re.DOTALL
    )
    
else:
    print("❌ Cookie security middleware not found, adding...")
    
    # Add the middleware before the compliance endpoint
    middleware_code = '''

# Master Prompt Cookie Security Middleware (FIXED)
@app.middleware("http")
async def cookie_security_middleware(request: Request, call_next):
    """Master Prompt compliant: Enhanced cookie security middleware"""
    
    # Log cookie-only authentication attempts
    if request.url.path.startswith("/auth/"):
        print(f"🍪 Cookie auth request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    # Enhanced security headers for cookie protection
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Ensure all auth cookies are secure (FIXED)
    if "Set-Cookie" in response.headers:
        cookie_value = response.headers["Set-Cookie"]
        if "access_token" in cookie_value or "session_token" in cookie_value:
            # Force Master Prompt compliance with proper secure settings
            if "HttpOnly" not in cookie_value:
                cookie_value += "; HttpOnly"
            if "Secure" not in cookie_value:
                cookie_value += "; Secure"
            if "SameSite=Strict" not in cookie_value:
                cookie_value += "; SameSite=Strict"
            
            response.headers["Set-Cookie"] = cookie_value
            print(f"🔒 Secured cookie: {cookie_value[:50]}...")
    
    return response

'''
    
    # Find a good place to insert (before compliance endpoint)
    if '@app.get("/auth/master-prompt-compliance")' in content:
        content = content.replace(
            '@app.get("/auth/master-prompt-compliance")',
            middleware_code + '@app.get("/auth/master-prompt-compliance")'
        )
    else:
        # Add at the end
        content += middleware_code

# Also ensure COOKIE_CONFIG has secure settings
if 'COOKIE_CONFIG' in content:
    secure_config = '''
# Secure cookie configuration (FIXED)
COOKIE_CONFIG = {
    "httponly": True,
    "secure": True,  # HTTPS only
    "samesite": "strict",
    "max_age": 86400,  # 24 hours
    "path": "/",
    "domain": None  # Will be set dynamically
}
'''
    
    # Replace existing COOKIE_CONFIG
    content = re.sub(
        r'COOKIE_CONFIG\s*=\s*{[^}]*}',
        secure_config.strip(),
        content,
        flags=re.DOTALL
    )

# Write the fixed content
with open('main.py', 'w') as f:
    f.write(content)

print("✅ Secure cookie configuration fixed!")
COOKIE_FIX_EOF

# Run the fix
echo "🔧 Applying secure cookie fix..."
python3 fix_cookie_security.py

# Verify the fix
echo ""
echo "🔍 Verifying secure cookie configuration..."
echo "📊 Cookie security patterns found:"
grep -n -A 2 -B 1 "HttpOnly\|Secure\|SameSite" main.py | head -15

echo ""
echo "📊 Cookie middleware patterns:"
grep -n -A 5 "cookie_security_middleware" main.py | head -10

# Check for COOKIE_CONFIG
echo ""
echo "📊 Cookie configuration:"
grep -n -A 8 "COOKIE_CONFIG" main.py

echo ""
echo "✅ SECURE COOKIE CONFIGURATION FIX COMPLETE!"
echo "============================================="
echo "🔒 Enhanced secure cookie settings applied"
echo "🍪 Cookie security middleware updated"
echo "📋 Master Prompt compliance maintained"

# Cleanup
rm -f fix_cookie_security.py

echo ""
echo "🧪 Test the fix with:"
echo "===================="
echo "grep -A 5 -B 2 'HttpOnly.*Secure\\|Secure.*HttpOnly' main.py"
echo "grep -A 5 'cookie_security_middleware' main.py"
