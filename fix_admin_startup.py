# Add this to the beginning of main.py after imports
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🔧 Running enterprise startup checks...")
    try:
        from database import get_db
        from auth_utils import hash_password
        from sqlalchemy import text
        
        db = next(get_db())
        
        # Fix admin password on startup
        correct_hash = hash_password("admin123")
        result = db.execute(text("""
            UPDATE users 
            SET password = :hash
            WHERE email = 'admin@owkai.com'
        """), {"hash": correct_hash})
        
        if result.rowcount > 0:
            db.commit()
            print("✅ Admin password synchronized")
        
    except Exception as e:
        print(f"⚠️ Startup admin fix failed: {e}")
    
    yield
    # Shutdown
    print("🔧 Enterprise shutdown complete")

# Replace the FastAPI app creation line with:
# app = FastAPI(lifespan=lifespan)
