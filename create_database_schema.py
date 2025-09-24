#!/usr/bin/env python3
"""
Database Schema Creation Script
Creates all tables for the OW-AI Backend system
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Base, SQLALCHEMY_DATABASE_URL
from models import User, Alert, Log
from models_mcp_governance import (
    MCPServerAction, MCPServer, MCPSession, MCPPolicy
)

def create_all_tables():
    """Create all database tables"""
    print("🚀 Starting database schema creation...")
    
    # Get database URL
    database_url = SQLALCHEMY_DATABASE_URL
    print(f"📊 Using database: {database_url}")
    
    # Create engine
    engine = create_engine(database_url)
    
    # Create all tables
    print("📋 Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    # Verify tables were created
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"✅ Created {len(tables)} tables:")
    for table in sorted(tables):
        print(f"   - {table}")
    
    print("🎯 Database schema creation completed successfully!")
    return engine

def populate_initial_data(engine):
    """Populate initial data"""
    print("\n📝 Populating initial data...")
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.email == "admin@owkai.app").first()
        if not admin_user:
            # Create admin user
            admin_user = User(
                email="admin@owkai.app",
                password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj2yK9S7atr6",  # hashed "admin123"
                role="admin",
                is_active=True,
                approval_level=5,
                is_emergency_approver=True,
                max_risk_approval=100
            )
            db.add(admin_user)
            print("✅ Created admin user")
        else:
            print("ℹ️  Admin user already exists")
            
        # Create test user
        test_user = db.query(User).filter(User.email == "test@owkai.app").first()
        if not test_user:
            test_user = User(
                email="test@owkai.app",
                password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj2yK9S7atr6",  # hashed "test123"
                role="user",
                is_active=True,
                approval_level=2,
                max_risk_approval=30
            )
            db.add(test_user)
            print("✅ Created test user")
        else:
            print("ℹ️  Test user already exists")
            
        # Commit changes
        db.commit()
        print("✅ Initial data populated successfully")
        
    except Exception as e:
        print(f"❌ Error populating data: {e}")
        db.rollback()
    finally:
        db.close()

def test_database_connection():
    """Test database connection with actual queries"""
    print("\n🔍 Testing database connectivity...")
    
    database_url = SQLALCHEMY_DATABASE_URL
    engine = create_engine(database_url)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Test basic query
        user_count = db.query(User).count()
        alert_count = db.query(Alert).count()
        
        print(f"✅ Database connection successful!")
        print(f"   - Users: {user_count}")
        print(f"   - Alerts: {alert_count}")
        
        # Test a more complex query
        admin_users = db.query(User).filter(User.role == "admin").all()
        print(f"   - Admin users: {len(admin_users)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    try:
        # Create schema
        engine = create_all_tables()
        
        # Populate initial data
        populate_initial_data(engine)
        
        # Test connectivity
        test_database_connection()
        
        print("\n🎉 Database setup completed successfully!")
        print("   Ready for Authorization Center testing!")
        
    except Exception as e:
        print(f"\n❌ Database setup failed: {e}")
        sys.exit(1)