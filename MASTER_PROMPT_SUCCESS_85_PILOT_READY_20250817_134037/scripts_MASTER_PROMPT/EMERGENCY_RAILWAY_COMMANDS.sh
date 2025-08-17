# ENTERPRISE SECRETS ROTATION - Railway Commands
# Execute these commands in your Railway project

# 1. Set new SECRET_KEY
railway variables set SECRET_KEY="7925a571e0e820c66a9e4de5854a4bd4d991c8e60b937c383113bc67fcce2907"

# 2. Set other configuration
railway variables set ALGORITHM="HS256"
railway variables set ACCESS_TOKEN_EXPIRE_MINUTES="30"
railway variables set REFRESH_TOKEN_EXPIRE_DAYS="7"
railway variables set ENVIRONMENT="production"
railway variables set ALLOWED_ORIGINS="https://passionate-elegance-production.up.railway.app,https://owai-production.up.railway.app"

# 3. CRITICAL: Rotate OPENAI_API_KEY manually
# - Go to https://platform.openai.com/api-keys
# - Create new API key
# - railway variables set OPENAI_API_KEY=<new_key>
# - Delete old API key from OpenAI dashboard

# 4. DATABASE_URL is managed by Railway automatically
# - No action needed unless you suspect database compromise

# 5. Deploy changes
railway up

# 6. Verify deployment
railway logs