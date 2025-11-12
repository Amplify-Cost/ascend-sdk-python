#!/usr/bin/env python3
"""Test JWT decoding to find the real error"""

import jwt
from datetime import datetime, timedelta, UTC
from security.jwt_security import secure_jwt_decode

# Create a test token
SECRET_KEY = "test-secret-key-12345"
ALGORITHM = "HS256"

# Create token with exp
payload = {
    "sub": "123",
    "email": "test@example.com",
    "role": "user",
    "exp": datetime.now(UTC) + timedelta(minutes=30),
    "iat": datetime.now(UTC)
}

token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
print(f"✅ Token created: {token[:50]}...")
print(f"✅ Payload: {payload}")

# Test 1: Decode with standard jwt.decode
print("\n--- Test 1: Standard jwt.decode ---")
try:
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    print(f"✅ Decoded successfully: {decoded}")
except Exception as e:
    print(f"❌ Failed: {e}")

# Test 2: Decode with options["require"]
print("\n--- Test 2: jwt.decode with options['require'] ---")
try:
    options = {
        "verify_signature": True,
        "verify_exp": True,
        "require": ["sub", "exp"]
    }
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options=options)
    print(f"✅ Decoded successfully: {decoded}")
except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Decode with secure_jwt_decode
print("\n--- Test 3: secure_jwt_decode ---")
try:
    decoded = secure_jwt_decode(
        token=token,
        secret_key=SECRET_KEY,
        algorithms=[ALGORITHM],
        required_claims=["sub", "exp"],
        operation_name="test"
    )
    print(f"✅ Decoded successfully: {decoded}")
except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()

print("\n--- All tests complete ---")
