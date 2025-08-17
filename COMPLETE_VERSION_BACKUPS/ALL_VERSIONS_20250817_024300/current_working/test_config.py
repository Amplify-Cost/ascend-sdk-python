#!/usr/bin/env python3
"""
Test script to verify AWS Secrets Manager integration
Run this to make sure everything is working
"""

from enterprise_config import config

def test_secrets():
    """Test all secrets can be retrieved"""
    
    print("🧪 Testing Enterprise Configuration...")
    print(f"Environment: {config.environment}")
    print(f"Using vault: {config.use_vault}")
    print()
    
    # Test each secret
    secrets_to_test = [
        'database',
        'jwt-private-key', 
        'jwt-public-key',
        'webhook-signing'
    ]
    
    results = {}
    
    for secret_name in secrets_to_test:
        print(f"Testing secret: {secret_name}")
        secret_value = config.get_secret(secret_name)
        
        if secret_value:
            # Show first 20 characters for verification (security)
            preview = secret_value[:20] + "..." if len(secret_value) > 20 else secret_value
            print(f"  ✅ Retrieved: {preview}")
            results[secret_name] = True
        else:
            print(f"  ❌ Failed to retrieve")
            results[secret_name] = False
        print()
    
    # Test database URL
    print("Testing database URL...")
    db_url = config.get_database_url()
    if db_url:
        # Hide password in URL for security
        safe_url = db_url.split('@')[1] if '@' in db_url else db_url
        print(f"  ✅ Database URL: postgresql://***:***@{safe_url}")
    else:
        print(f"  ❌ Database URL failed")
    print()
    
    # Summary
    success_count = sum(results.values())
    total_count = len(results)
    
    print("📊 Results Summary:")
    print(f"  Secrets retrieved: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("  🎉 All tests passed! Enterprise config is working.")
        return True
    else:
        print("  ⚠️  Some tests failed. Check your AWS configuration.")
        return False

if __name__ == "__main__":
    test_secrets()