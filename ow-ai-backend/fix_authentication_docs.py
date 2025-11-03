"""
Fix authentication documentation to reflect actual cookie-based implementation
"""
from pathlib import Path

docs_dir = Path('../enterprise-docs')

# Updated authentication section
auth_docs = """## Authentication

OW-AI uses **cookie-based JWT authentication** for secure, browser-friendly access.

### How It Works
```
1. User submits credentials to /auth/login
2. Backend validates against database
3. JWT token generated and signed with RS256
4. Token sent in httpOnly cookie (not in response body)
5. Browser automatically includes cookie in all requests
6. Backend reads and validates JWT from cookie
7. User context attached to request
```

### Login Flow

**Request:**
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@company.com",
  "password": "password123"
}
```

**Response:**
```http
HTTP/1.1 200 OK
Set-Cookie: access_token=eyJ0eXAiOiJKV1QiLCJhbGc...; HttpOnly; Secure; SameSite=Strict; Path=/

{
  "message": "Login successful",
  "user": {
    "email": "user@company.com",
    "role": "approver"
  }
}
```

### Cookie Details

The authentication cookie has these properties:

- **Name**: `access_token`
- **HttpOnly**: ✅ (JavaScript cannot read it - XSS protection)
- **Secure**: ✅ (Only sent over HTTPS)
- **SameSite**: Strict (CSRF protection)
- **Max-Age**: 3600 seconds (1 hour)
- **Path**: / (sent with all requests)

### Automatic Authentication

Once logged in, the browser automatically includes the cookie:
```http
GET /api/smart-rules
Cookie: access_token=eyJ0eXAiOiJKV1QiLCJhbGc...

Response: 200 OK (authenticated automatically)
```

**You don't need to manually add Authorization headers** - the browser handles everything!

### Token Structure

Even though delivered via cookie, the token is still a JWT:
```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_abc123",
    "email": "user@company.com",
    "role": "approver",
    "iat": 1698765432,
    "exp": 1698769032
  },
  "signature": "..."
}
```

### API Client Usage

For programmatic API access (not browser), you can still use Bearer tokens:

**Option 1: Use Cookie (Recommended for web apps)**
```javascript
// Browser automatically handles cookies
fetch('https://pilot.owkai.app/api/smart-rules', {
  credentials: 'include'  // Important: include cookies
})
```

**Option 2: API Key (Coming soon)**
```http
GET /api/smart-rules
X-API-Key: sk_live_your_api_key_here
```

### Logout
```http
POST /auth/logout

Response:
Set-Cookie: access_token=; Max-Age=0; Path=/
```

The cookie is cleared and subsequent requests will be unauthenticated.

### Security Advantages

**Why Cookie-Based?**

1. **XSS Protection**: HttpOnly cookies can't be stolen by malicious JavaScript
2. **Automatic Handling**: No need to manually manage tokens
3. **Built-in Expiration**: Browser respects Max-Age
4. **Secure by Default**: Secure flag ensures HTTPS-only transmission

**Security Features:**
- ✅ JWT signed with RSA-2048 (can't be forged)
- ✅ HttpOnly (immune to XSS)
- ✅ Secure flag (HTTPS only)
- ✅ SameSite=Strict (CSRF protection)
- ✅ Short expiration (1 hour)
- ✅ Server-side validation on every request

### CSRF Protection

Your system uses cookie-based auth with CSRF protection disabled for authenticated requests (cookies + JWT signature provide sufficient security).

**Why this is safe:**
1. JWT signature proves the token wasn't tampered with
2. HttpOnly cookies can't be read by JavaScript
3. Same-origin policy prevents cross-site access
4. Short token expiration limits exposure

### Troubleshooting

**"Authentication required" errors:**
- Check that `credentials: 'include'` is set in fetch requests
- Verify cookies are enabled in browser
- Check that you're on the same domain (or CORS configured)

**Cookie not being set:**
- Verify you're using HTTPS in production
- Check that login response includes Set-Cookie header
- Ensure no browser extensions blocking cookies

**Token expired:**
- Tokens expire after 1 hour
- User will need to log in again
- Refresh token support coming soon
"""

# Read and update the API documentation
api_doc = docs_dir / 'api.md'
with open(api_doc, 'r') as f:
    content = f.read()

# Replace the authentication section
import re
# Find and replace authentication section
pattern = r'## Authentication.*?(?=## Core Endpoints|$)'
content = re.sub(pattern, auth_docs + '\n', content, flags=re.DOTALL)

with open(api_doc, 'w') as f:
    f.write(content)

print("✅ Updated api.md with cookie-based authentication")

# Regenerate HTML
import markdown

html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Documentation - OW-AI Enterprise Documentation</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.7;
            color: #2c3e50;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .nav {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            padding: 25px 40px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
        }}
        .nav-logo {{
            font-size: 24px;
            font-weight: bold;
            color: white;
        }}
        .nav-links {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }}
        .nav a {{
            color: white;
            text-decoration: none;
            padding: 8px 15px;
            border-radius: 6px;
            transition: all 0.3s;
            font-weight: 500;
            font-size: 14px;
        }}
        .nav a:hover {{
            background: rgba(255,255,255,0.2);
            transform: translateY(-2px);
        }}
        .content {{
            padding: 60px;
        }}
        h1 {{
            color: #2c3e50;
            font-size: 48px;
            margin-bottom: 20px;
            border-bottom: 4px solid #667eea;
            padding-bottom: 20px;
        }}
        h2 {{
            color: #34495e;
            font-size: 36px;
            margin: 50px 0 25px 0;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
        }}
        h3 {{
            color: #7f8c8d;
            font-size: 28px;
            margin: 35px 0 20px 0;
        }}
        h4 {{
            color: #95a5a6;
            font-size: 22px;
            margin: 25px 0 15px 0;
        }}
        p {{
            margin: 15px 0;
            font-size: 17px;
            line-height: 1.8;
        }}
        code {{
            background: #f8f9fa;
            padding: 3px 8px;
            border-radius: 4px;
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
            font-size: 14px;
            color: #e74c3c;
        }}
        pre {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 25px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 25px 0;
            font-size: 14px;
            line-height: 1.6;
        }}
        pre code {{
            background: none;
            color: #ecf0f1;
            padding: 0;
        }}
        ul, ol {{
            margin: 20px 0 20px 40px;
        }}
        li {{
            margin: 10px 0;
            font-size: 17px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 30px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 15px;
            text-align: left;
            border: 1px solid #e0e0e0;
        }}
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
        }}
        tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        .footer {{
            background: #2c3e50;
            color: white;
            padding: 40px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <div class="nav-logo">🛡️ OW-AI</div>
            <div class="nav-links">
                <a href="index.html">Home</a>
                <a href="product_overview.html">Overview</a>
                <a href="architecture.html">Architecture</a>
                <a href="api.html">API</a>
                <a href="user_guide.html">User Guide</a>
                <a href="admin_guide.html">Admin</a>
                <a href="security_compliance.html">Security</a>
            </div>
        </div>
        <div class="content">
            {content}
        </div>
        <div class="footer">
            <p>© 2025 OW-AI Enterprise Platform | Documentation Version 2.0</p>
        </div>
    </div>
</body>
</html>
"""

html_content = markdown.markdown(content, extensions=['fenced_code', 'tables', 'nl2br'])
html_file = docs_dir / 'api.html'

with open(html_file, 'w') as f:
    f.write(html_template.format(content=html_content))

print("✅ Regenerated api.html with correct authentication info")
print()
print("✅ Documentation now reflects your ACTUAL cookie-based implementation!")
