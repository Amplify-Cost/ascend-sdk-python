#!/usr/bin/env python3
"""
Create test users for authentication testing
"""
import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from models import User, Base
from config import DATABASE_URL

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_test_users():
    """Create test users in the database"""
    try:
        # Create async engine
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        # Create tables if they don't exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Create session
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Test users to create
            test_users = [
                {
                    "email": "test@example.com",
                    "password": "test",
                    "full_name": "Test User",
                    "is_active": True
                },
                {
                    "email": "admin@example.com", 
                    "password": "admin",
                    "full_name": "Admin User",
                    "is_active": True
                },
                {
                    "email": "demo@owai.com",
                    "password": "demo123",
                    "full_name": "Demo User", 
                    "is_active": True
                }
            ]
            
            created_users = []
            for user_data in test_users:
                # Check if user already exists
                existing_user = await session.execute(
                    select(User).where(User.email == user_data["email"])
                )
                if existing_user.scalar_one_or_none():
                    print(f"✅ User {user_data['email']} already exists")
                    continue
                
                # Create new user
                hashed_password = pwd_context.hash(user_data["password"])
                user = User(
                    email=user_data["email"],
                    hashed_password=hashed_password,
                    full_name=user_data["full_name"],
                    is_active=user_data["is_active"]
                )
                session.add(user)
                created_users.append(user_data["email"])
                print(f"✅ Created user: {user_data['email']}")
            
            await session.commit()
            
            print(f"\n🎉 SUCCESS: Created {len(created_users)} test users")
            print("📋 Available test credentials:")
            for user_data in test_users:
                print(f"   Email: {user_data['email']}, Password: {user_data['password']}")
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Add necessary imports at the top
    from sqlalchemy import select
    
    print("🚀 Creating test users for authentication...")
    success = asyncio.run(create_test_users())
    
    if success:
        print("\n✅ Test users created successfully!")
        print("🧪 You can now test login with:")
        print("   Email: test@example.com, Password: test")
        print("   Email: admin@example.com, Password: admin") 
        sys.exit(0)
    else:
        print("\n❌ Failed to create test users")
        sys.exit(1)
