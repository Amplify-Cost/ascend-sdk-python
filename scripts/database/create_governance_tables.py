#!/usr/bin/env python3
"""
Create MCP Governance Tables
Creates the required database tables for Policy Management functionality
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database import Base, SQLALCHEMY_DATABASE_URL

# Import the models to register them with SQLAlchemy
from models_mcp_governance import MCPPolicy, MCPServer, MCPSession, MCPServerAction

def create_governance_tables():
    """Create all governance tables"""
    try:
        # Use database URL from database.py
        database_url = SQLALCHEMY_DATABASE_URL
        print(f"🔗 Connecting to database...")
        
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
        
        # Create all tables
        print("🏗️ Creating MCP Governance tables...")
        Base.metadata.create_all(bind=engine, checkfirst=True)
        
        print("✅ All governance tables created successfully!")
        
        # List created tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%mcp%'
                ORDER BY table_name
            """))
            
            tables = result.fetchall()
            print("📋 Created governance tables:")
            for table in tables:
                print(f"  ✓ {table[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating governance tables: {e}")
        return False

if __name__ == "__main__":
    print("🏢 ENTERPRISE: Creating MCP Governance Database Tables")
    print("=" * 60)
    
    success = create_governance_tables()
    
    if success:
        print("\n✅ SUCCESS: All governance tables created!")
        print("🧠 Policy Management database ready for use")
        sys.exit(0)
    else:
        print("\n❌ FAILED: Could not create governance tables")
        sys.exit(1)