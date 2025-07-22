# config.py - FIXED VERSION
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Required environment variables
REQUIRED_ENV_VARS = {
    "SECRET_KEY": "JWT secret key for token signing",
    "DATABASE_URL": "PostgreSQL connection string", 
    "OPENAI_API_KEY": "OpenAI API key for LLM features"
}

# Validate all required environment variables exist
missing_vars = []
for var_name, description in REQUIRED_ENV_VARS.items():
    if not os.getenv(var_name):
        missing_vars.append(f"{var_name} - {description}")

if missing_vars:
    error_msg = "Missing required environment variables:\n" + "\n".join([f"  • {var}" for var in missing_vars])
    raise ValueError(error_msg)

# Securely load configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
DATABASE_URL = os.getenv("DATABASE_URL") 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Token expiration settings
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# CORS origins - load from environment
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
if not ALLOWED_ORIGINS or ALLOWED_ORIGINS == [""]:
    ALLOWED_ORIGINS = [
        "https://passionate-elegance-production.up.railway.app",
        "https://owai-production.up.railway.app",
        "http://localhost:3000",  # For development
        "http://localhost:5173"   # For Vite dev server
    ]

# Rate limiting settings
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
LOGIN_RATE_LIMIT = os.getenv("LOGIN_RATE_LIMIT", "5/minute")
REGISTER_RATE_LIMIT = os.getenv("REGISTER_RATE_LIMIT", "3/minute")

print(f"✅ Configuration loaded successfully")
print(f"✅ Allowed CORS origins: {ALLOWED_ORIGINS}")
print(f"✅ Access token expires in: {ACCESS_TOKEN_EXPIRE_MINUTES} minutes")