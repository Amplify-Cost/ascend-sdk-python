#!/usr/bin/env python3
"""
Test script to verify Enterprise JWT Manager
"""

from jwt_manager import jwt_manager
import uuid

def test_jwt_system():
    """Test the complete JWT system"""
    
    print("🧪 Testing Enterprise JWT System...")
    print()
    
    # Test token creation
    print("1. Creating access token...")
    
    # Sample user data
    user_id = "user_12345"
    role = "manager"
    tenant_id = "acme_corp"
    session_id = str(uuid.uuid4())
    
    try:
        # Create token
        access_token = jwt_manager.create_access_token(
            user_id=user_id,
            role=role,
            tenant_id=tenant_id,
            session_id=session_id,
            permissions=["read", "write", "approve"]
        )
        
        print(f"  ✅ Token created successfully")
        print(f"  📄 Token preview: {access_token[:50]}...")
        print()
        
        # Test token verification
        print("2. Verifying token...")
        
        decoded = jwt_manager.verify_token(access_token)
        
        print(f"  ✅ Token verified successfully")
        print(f"  👤 User ID: {decoded['sub']}")
        print(f"  🏢 Tenant: {decoded['tenant_id']}")
        print(f"  🔐 Role: {decoded['role']}")
        print(f"  ⏰ Expires: {decoded['exp']}")
        print(f"  🎫 Permissions: {decoded['permissions']}")
        print()
        
        # Test role permissions
        print("3. Testing role-based permissions...")
        
        for test_role in ["admin", "security", "manager", "approver", "analyst", "viewer"]:
            permissions = jwt_manager.get_role_permissions(test_role)
            print(f"  {test_role.upper()}: {', '.join(permissions)}")
        print()
        
        # Test refresh token
        print("4. Creating refresh token...")
        
        refresh_token = jwt_manager.create_refresh_token(user_id, session_id)
        print(f"  ✅ Refresh token created")
        print(f"  📄 Refresh token preview: {refresh_token[:50]}...")
        print()
        
        # Test different roles
        print("5. Testing different role tokens...")
        
        for test_role in ["admin", "analyst", "viewer"]:
            test_token = jwt_manager.create_access_token(
                user_id=f"test_{test_role}",
                role=test_role,
                tenant_id="test_corp",
                session_id=str(uuid.uuid4())
            )
            
            test_decoded = jwt_manager.verify_token(test_token)
            print(f"  ✅ {test_role.upper()} token: {test_decoded['sub']} - {test_decoded['role']}")
        
        print()
        print("🎉 All JWT tests passed! Enterprise JWT system is working perfectly.")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_jwt_system()