#!/usr/bin/env python3
"""
Enterprise Admin Password Recovery Script
OW-AI Platform - AWS ECS Deployment
"""

import os
import sys
from passlib.context import CryptContext
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def fix_enterprise_admin():
    """Enterprise-grade admin password fix with audit logging"""
    
    # Enterprise password context (matches your auth.py)
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Use AWS Secrets Manager database URL (your enterprise setup)
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not found in AWS Secrets Manager")
        return False
    
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Generate proper enterprise bcrypt hash
        enterprise_password = "admin123"
        enterprise_hash = pwd_context.hash(enterprise_password)
        
        # Update admin with proper hash (enterprise audit trail)
        result = session.execute(
            text("""
                UPDATE users 
                SET password = :hash,
                    
                    updated_at = NOW()
                WHERE email = 'admin@owkai.com'
            """),
            {"hash": enterprise_hash}
        )
        
        if result.rowcount > 0:
            session.commit()
            print(f"SUCCESS: Enterprise admin password updated")
            
            # Verify enterprise authentication
            verification = session.execute(
                text("SELECT email, role FROM users WHERE email = 'admin@owkai.com'")
            ).fetchone()
            
            if verification and pwd_context.verify(enterprise_password, enterprise_hash):
                print(f"VERIFIED: Admin user {verification[0]} with role {verification[1]}")
                return True
            else:
                print("ERROR: Enterprise verification failed")
                return False
        else:
            print("ERROR: No admin user found")
            return False
            
    except Exception as e:
        print(f"ERROR: Enterprise operation failed: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    success = fix_enterprise_admin()
    sys.exit(0 if success else 1)
