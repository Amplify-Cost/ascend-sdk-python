from sqlalchemy import create_engine, text
from auth_utils import hash_password
import secrets
import string

DATABASE_URL = "postgresql://owkai_admin:OWKAI_secure123@owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com:5432/owkai_pilot"

def generate_temp_password():
    """Generate secure temporary password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(12))

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Find users without passwords (likely SSO users)
        result = conn.execute(text("""
            SELECT id, email 
            FROM users 
            WHERE password IS NULL OR password = ''
        """))
        
        sso_users = result.fetchall()
        print(f"Found {len(sso_users)} users without passwords:")
        
        for user in sso_users:
            temp_password = generate_temp_password()
            hashed_password = hash_password(temp_password)
            
            conn.execute(text("""
                UPDATE users 
                SET password = :password 
                WHERE id = :user_id
            """), {
                "password": hashed_password,
                "user_id": user[0]
            })
            
            print(f"  {user[1]}: temp password = {temp_password}")
        
        conn.commit()
        print("\n✅ All users now have passwords")
        print("🔑 Users can now authenticate with their temporary passwords")
        
except Exception as e:
    print(f"Error: {e}")
