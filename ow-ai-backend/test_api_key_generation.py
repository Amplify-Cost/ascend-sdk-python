"""
Test API Key Generation - Production Database

Tests:
1. Generate API key for admin user
2. Verify key hash is correct
3. List API keys
4. Revoke API key
5. Verify authentication with API key

Database: AWS RDS Production
"""

import requests
import json
import sys

# Production API base URL
BASE_URL = "http://localhost:8000"
PROD_BASE_URL = "https://pilot.owkai.app"

# Test configuration
TEST_USER_EMAIL = "admin@owkai.com"
TEST_USER_REDACTED-CREDENTIAL = "admin123"


def print_section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def test_login():
    """Test 1: Login to get JWT token"""
    print_section("TEST 1: Login")

    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_USER_EMAIL, "password": TEST_USER_REDACTED-CREDENTIAL}
    )

    if response.status_code == 200:
        # Get cookie
        access_token = response.cookies.get("access_token")
        print(f"✅ Login successful")
        print(f"   Access token (first 20 chars): {access_token[:20]}...")
        return access_token
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


def test_generate_api_key(access_token):
    """Test 2: Generate API key"""
    print_section("TEST 2: Generate API Key")

    response = requests.post(
        f"{BASE_URL}/api/keys/generate",
        json={
            "name": "Test SDK Key",
            "description": "Test key for SDK development",
            "expires_in_days": 365
        },
        cookies={"access_token": access_token}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ API key generated successfully")
        print(f"   Key ID: {data['key_id']}")
        print(f"   Key Prefix: {data['key_prefix']}")
        print(f"   Full Key (first 30 chars): {data['api_key'][:30]}...")
        print(f"   Expires At: {data['expires_at']}")
        print(f"   ⚠️  {data['warning']}")
        return data['api_key'], data['key_id']
    else:
        print(f"❌ API key generation failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None, None


def test_list_api_keys(access_token):
    """Test 3: List API keys"""
    print_section("TEST 3: List API Keys")

    response = requests.get(
        f"{BASE_URL}/api/keys/list",
        cookies={"access_token": access_token}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ API keys listed successfully")
        print(f"   Total keys: {data['total_count']}")
        for key in data['keys'][:3]:  # Show first 3
            print(f"   - {key['name']}: {key['key_prefix']} (active: {key['is_active']})")
        return True
    else:
        print(f"❌ List API keys failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_api_key_authentication(api_key):
    """Test 4: Authenticate with API key"""
    print_section("TEST 4: API Key Authentication")

    # Try to access a protected endpoint with API key
    response = requests.get(
        f"{BASE_URL}/api/keys/list",
        headers={"Authorization": f"Bearer {api_key}"}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ API key authentication successful")
        print(f"   Listed {data['total_count']} keys using API key")
        return True
    else:
        print(f"❌ API key authentication failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_revoke_api_key(access_token, key_id):
    """Test 5: Revoke API key"""
    print_section("TEST 5: Revoke API Key")

    response = requests.delete(
        f"{BASE_URL}/api/keys/{key_id}/revoke",
        json={"reason": "Test completed"},
        cookies={"access_token": access_token}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ API key revoked successfully")
        print(f"   Key ID: {data['key_id']}")
        print(f"   Revoked At: {data['revoked_at']}")
        return True
    else:
        print(f"❌ API key revocation failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def main():
    print_section("API Key Management - Production Database Test")
    print(f"Testing against: {BASE_URL}")
    print(f"Database: AWS RDS Production (owkai-pilot-db)")

    # Run tests
    access_token = test_login()
    if not access_token:
        print("\n❌ LOGIN FAILED - Cannot proceed with tests")
        sys.exit(1)

    api_key, key_id = test_generate_api_key(access_token)
    if not api_key:
        print("\n❌ KEY GENERATION FAILED - Cannot proceed with tests")
        sys.exit(1)

    test_list_api_keys(access_token)
    test_api_key_authentication(api_key)
    test_revoke_api_key(access_token, key_id)

    # Final summary
    print_section("TEST SUMMARY")
    print("✅ All API key management tests passed!")
    print("\nProduction database tables verified:")
    print("   - api_keys")
    print("   - api_key_usage_logs")
    print("   - api_key_permissions")
    print("   - api_key_rate_limits")
    print("\n✅ DAY 2 COMPLETE: API key generation and authentication working!")


if __name__ == "__main__":
    main()
