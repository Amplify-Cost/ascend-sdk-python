# OW-AI API Documentation

## Base URL
- **Production**: `https://pilot.owkai.app`
- **Development**: `http://localhost:8000`

## Authentication

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

## Core Endpoints

### Agent Actions

#### List Actions
```http
GET /agent-control/actions?status=pending&limit=50
Authorization: Bearer <token>
```

**Response:**
```json
{
  "actions": [
    {
      "id": 1,
      "action_type": "database_write",
      "description": "Update user permissions",
      "risk_score": 85.5,
      "status": "pending",
      "created_at": "2025-10-23T10:30:00Z"
    }
  ],
  "total": 42
}
```

#### Create Action
```http
POST /agent-control/actions
Authorization: Bearer <token>
Content-Type: application/json

{
  "action_type": "system_modification",
  "description": "Install security patch",
  "metadata": {
    "target_system": "production-web-01"
  }
}
```

### Smart Rules

#### List Rules
```http
GET /api/smart-rules
Authorization: Bearer <token>
```

#### Create Rule
```http
POST /api/smart-rules
Authorization: Bearer <token>

{
  "name": "High-Risk Detection",
  "condition": "risk_score > 80",
  "action": "require_approval",
  "enabled": true
}
```

### Alerts

#### List Alerts
```http
GET /alerts?status=active&severity=high
Authorization: Bearer <token>
```

#### Acknowledge Alert
```http
POST /alerts/{id}/acknowledge
Authorization: Bearer <token>

{
  "notes": "Reviewed and resolved"
}
```

### Analytics

#### Performance Metrics
```http
GET /analytics/performance
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_actions": 1247,
  "approved": 892,
  "denied": 234,
  "approval_rate": 71.5,
  "average_response_time": 45.3
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request format"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "detail": "Admin access required"
}
```

## Rate Limiting

- **Authenticated**: 100 requests/minute
- **Unauthenticated**: 10 requests/minute
- **Admin**: 500 requests/minute
