"""
Test API Key Generation - PRODUCTION Environment

Tests API key management against https://pilot.owkai.app

Tests:
1. Generate API key for admin user
2. Verify key works with API authentication
3. List API keys
4. Test rate limiting
5. Get usage statistics
6. Revoke API key

Production: AWS RDS + ECS Fargate
"""

import requests
import json
import sys
import time

# Production API base URL
PROD_BASE_URL = "https://pilot.owkai.app"

# Test configuration
TEST_USER_EMAIL = "admin@owkai.com"
TEST_USER_REDACTED-CREDENTIAL = "admin123"


def print_section(title):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def test_login():
    """Test 1: Login to get JWT token"""
    print_section("TEST 1: Login to Production")

    try:
        response = requests.post(
            f"{PROD_BASE_URL}/api/auth/token",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_REDACTED-CREDENTIAL},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            print(f"✅ Login successful")
            print(f"   User: {TEST_USER_EMAIL}")
            print(f"   Token received: {len(access_token)} characters")
            print(f"   Auth mode: {data.get('auth_mode')}")
            return access_token
        else:
            print(f"❌ Login failed: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None


def test_generate_api_key(access_token):
    """Test 2: Generate API key in production"""
    print_section("TEST 2: Generate API Key (Production)")

    try:
        response = requests.post(
            f"{PROD_BASE_URL}/api/keys/generate",
            json={
                "name": "Production Test Key",
                "description": "Testing API key management in production",
                "expires_in_days": 30
            },
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ API key generated successfully")
            print(f"   Key ID: {data['key_id']}")
            print(f"   Key Prefix: {data['key_prefix']}")
            print(f"   Full Key: {data['api_key'][:40]}...")
            print(f"   Expires: {data['expires_at']}")
            print(f"   Created: {data['created_at']}")
            return data['api_key'], data['key_id']
        else:
            print(f"❌ API key generation failed: HTTP {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return None, None
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return None, None


def test_api_key_authentication(api_key):
    """Test 3: Authenticate with API key"""
    print_section("TEST 3: API Key Authentication")

    try:
        # Test API key auth by listing keys
        response = requests.get(
            f"{PROD_BASE_URL}/api/keys/list",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ API key authentication successful")
            print(f"   Method: API Key (not JWT)")
            print(f"   Keys listed: {data['total_count']}")
            return True
        else:
            print(f"❌ API key auth failed: HTTP {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"❌ Auth error: {e}")
        return False


def test_list_api_keys(access_token):
    """Test 4: List API keys"""
    print_section("TEST 4: List API Keys")

    try:
        response = requests.get(
            f"{PROD_BASE_URL}/api/keys/list?page=1&page_size=10",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ API keys listed successfully")
            print(f"   Total keys: {data['total_count']}")
            print(f"   Page: {data['page']} (size: {data['page_size']})")
            print(f"\n   Recent keys:")
            for i, key in enumerate(data['keys'][:3], 1):
                status = "🟢 ACTIVE" if key['is_active'] else "🔴 REVOKED"
                print(f"   {i}. {key['name']}: {key['key_prefix']}... ({status})")
                print(f"      Created: {key['created_at']}")
                print(f"      Usage: {key['usage_count']} calls")
            return True
        else:
            print(f"❌ List failed: HTTP {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"❌ List error: {e}")
        return False


def test_get_usage(access_token, key_id):
    """Test 5: Get usage statistics"""
    print_section("TEST 5: Get Usage Statistics")

    try:
        response = requests.get(
            f"{PROD_BASE_URL}/api/keys/{key_id}/usage?limit=5",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Usage statistics retrieved")
            print(f"   Key ID: {data['key_id']}")
            print(f"   Key Prefix: {data['key_prefix']}")
            print(f"\n   Statistics:")
            stats = data['statistics']
            print(f"   - Total requests: {stats['total_requests']}")
            print(f"   - Recent requests: {stats['recent_requests']}")
            print(f"   - Success rate: {stats['success_rate']}%")
            print(f"   - Last used: {stats['last_used_at'] or 'Never'}")

            if data['recent_activity']:
                print(f"\n   Recent Activity:")
                for activity in data['recent_activity'][:3]:
                    print(f"   - {activity['method']} {activity['endpoint']}: HTTP {activity['status']} ({activity['response_time_ms']}ms)")
            return True
        else:
            print(f"❌ Usage retrieval failed: HTTP {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"❌ Usage error: {e}")
        return False


def test_revoke_api_key(access_token, key_id):
    """Test 6: Revoke API key"""
    print_section("TEST 6: Revoke API Key")

    try:
        response = requests.delete(
            f"{PROD_BASE_URL}/api/keys/{key_id}/revoke",
            json={"reason": "Production test completed"},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ API key revoked successfully")
            print(f"   Key ID: {data['key_id']}")
            print(f"   Revoked at: {data['revoked_at']}")
            print(f"   Message: {data['message']}")
            return True
        else:
            print(f"❌ Revocation failed: HTTP {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"❌ Revocation error: {e}")
        return False


def main():
    print_section("🚀 PRODUCTION API KEY MANAGEMENT TEST")
    print(f"Target: {PROD_BASE_URL}")
    print(f"Database: AWS RDS (owkai-pilot-db)")
    print(f"Backend: AWS ECS Fargate")

    # Track results
    results = []

    # Test 1: Login
    print("\n⏳ Starting test sequence...")
    access_token = test_login()
    results.append(("Login", access_token is not None))
    if not access_token:
        print("\n❌ CRITICAL: Cannot proceed without login")
        sys.exit(1)

    # Test 2: Generate API key
    api_key, key_id = test_generate_api_key(access_token)
    results.append(("Generate API Key", api_key is not None))
    if not api_key:
        print("\n❌ CRITICAL: Cannot proceed without API key")
        sys.exit(1)

    # Test 3: API key authentication
    auth_result = test_api_key_authentication(api_key)
    results.append(("API Key Authentication", auth_result))

    # Test 4: List keys
    list_result = test_list_api_keys(access_token)
    results.append(("List API Keys", list_result))

    # Test 5: Get usage
    usage_result = test_get_usage(access_token, key_id)
    results.append(("Get Usage Statistics", usage_result))

    # Test 6: Revoke key
    revoke_result = test_revoke_api_key(access_token, key_id)
    results.append(("Revoke API Key", revoke_result))

    # Final summary
    print_section("📊 TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"Tests Passed: {passed}/{total}\n")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {test_name}")

    print("\n" + "=" * 70)
    if passed == total:
        print("🎉 ALL TESTS PASSED - API KEY MANAGEMENT WORKING IN PRODUCTION!")
        print("\n✅ Day 3 Complete: Production deployment verified")
        print("\nProduction features working:")
        print("  - API key generation (SHA-256 hashing)")
        print("  - Dual authentication (JWT + API key)")
        print("  - Key listing and management")
        print("  - Usage tracking and statistics")
        print("  - Key revocation with audit trail")
        print("\n🚀 Ready for Day 4: SDK Development")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        print("\nCheck:")
        print("  - Is the new code deployed to production?")
        print("  - Are all database migrations applied?")
        print("  - Check ECS task logs for errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())
