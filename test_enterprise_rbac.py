#!/usr/bin/env python3
"""
Test Enterprise RBAC + SSO System
"""

from rbac_manager import enterprise_rbac, Permission, AccessLevel
from sso_manager import enterprise_sso

def test_rbac_system():
    """Test the complete RBAC system"""
    
    print("🧪 Testing Enterprise RBAC System...")
    print()
    
    # Test all access levels
    for level in range(6):
        print(f"📋 Access Level {level}: {enterprise_rbac.get_access_level_name(level)}")
        
        role_summary = enterprise_rbac.get_role_summary(level)
        print(f"   Permissions: {role_summary['permission_count']}")
        print(f"   Can approve low risk: {role_summary['can_approve_low']}")
        print(f"   Can approve high risk: {role_summary['can_approve_high']}")
        print(f"   Can approve critical: {role_summary['can_approve_critical']}")
        print()
    
    # Test specific permissions
    print("🔐 Testing Specific Permissions...")
    
    test_cases = [
        (AccessLevel.BASIC, Permission.DASHBOARD_VIEW, True),
        (AccessLevel.BASIC, Permission.USERS_CREATE, False),
        (AccessLevel.ADMIN, Permission.USERS_CREATE, True),
        (AccessLevel.EXECUTIVE, Permission.AUTH_EMERGENCY_OVERRIDE, True),
        (AccessLevel.MANAGER, Permission.AUTH_APPROVE_HIGH, False),
        (AccessLevel.ADMIN, Permission.AUTH_APPROVE_HIGH, True),
    ]
    
    for level, permission, expected in test_cases:
        result = enterprise_rbac.has_permission(level, permission)
        status = "✅" if result == expected else "❌"
        print(f"   {status} Level {level} + {permission}: {result} (expected {expected})")
    
    print()
    
    # Test separation of duties
    print("⚖️ Testing Separation of Duties...")
    
    sod_tests = [
        ("high_risk_action", 75),
        ("critical_system_change", 95),
        ("user_role_change", 50),
    ]
    
    for action, risk_score in sod_tests:
        sod_requirement = enterprise_rbac.requires_separation_of_duties(action, risk_score)
        if sod_requirement:
            print(f"   🔒 {action} (risk {risk_score}): Requires {sod_requirement['required_approvers']} approvers")
        else:
            print(f"   ✅ {action} (risk {risk_score}): No SoD required")
    
    print()
    print("🎉 RBAC System Test Complete!")

def test_sso_system():
    """Test SSO provider configuration"""
    
    print("🌐 Testing Enterprise SSO System...")
    print()
    
    # Test provider configuration
    for provider_id, provider_config in enterprise_sso.providers.items():
        print(f"🔑 {provider_config['name']} ({provider_id}):")
        print(f"   Client ID configured: {bool(provider_config['client_id'])}")
        print(f"   Authorization URL: {provider_config['authorization_url']}")
        print(f"   Scopes: {', '.join(provider_config['scopes'])}")
        print()
    
    # Test group mappings
    print("👥 Testing Group to Access Level Mapping...")
    
    test_groups = [
        ["OW-AI-Executives"],
        ["OW-AI-Administrators", "IT-Support"],
        ["OW-AI-Managers"],
        ["OW-AI-PowerUsers"],
        ["OW-AI-BasicUsers", "All-Employees"],
        ["unknown-group"]
    ]
    
    for groups in test_groups:
        access_level = enterprise_sso.map_groups_to_access_level(groups)
        role_name = enterprise_rbac.get_access_level_name(access_level)
        print(f"   Groups {groups} → Level {access_level} ({role_name})")
    
    print()
    
    # Test enterprise profile creation
    print("👤 Testing Enterprise Profile Creation...")
    
    mock_user_info = {
        "email": "test.user@company.com",
        "given_name": "Test",
        "family_name": "User"
    }
    
    mock_groups = ["OW-AI-Managers", "Finance-Team"]
    
    profile = enterprise_sso.create_enterprise_user_profile(
        provider="okta",
        user_info=mock_user_info,
        groups=mock_groups
    )
    
    print(f"   ✅ Created profile for {profile['email']}")
    print(f"   Access Level: {profile['access_level']} ({enterprise_rbac.get_access_level_name(profile['access_level'])})")
    print(f"   Department: {profile['department']}")
    print(f"   SSO Groups: {', '.join(profile['sso_groups'])}")
    
    print()
    print("🎉 SSO System Test Complete!")

if __name__ == "__main__":
    test_rbac_system()
    print()
    test_sso_system()
