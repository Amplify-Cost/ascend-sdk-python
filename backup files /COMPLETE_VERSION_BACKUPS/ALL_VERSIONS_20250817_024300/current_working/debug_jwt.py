#!/usr/bin/env python3
"""
Debug JWT timing issues
"""

import jwt
import time
from datetime import datetime
from jwt_manager import jwt_manager
import uuid

def debug_token_timing():
    """Debug token timing issues"""
    
    print("🔍 Debugging JWT Token Timing...")
    
    # Get current time
    now = datetime.utcnow()
    current_timestamp = int(now.timestamp())
    
    print(f"Current time: {now}")
    print(f"Current timestamp: {current_timestamp}")
    print()
    
    # Create token
    print("Creating token...")
    session_id = str(uuid.uuid4())
    
    token = jwt_manager.create_access_token(
        user_id="debug_user",
        role="admin",
        tenant_id="debug_corp",
        session_id=session_id
    )
    
    print(f"Token created: {token[:50]}...")
    print()
    
    # Decode token WITHOUT verification to see contents
    print("Decoding token (no verification)...")
    try:
        decoded_unverified = jwt.decode(token, options={"verify_signature": False})
        
        print("Token contents:")
        print(f"  iss: {decoded_unverified.get('iss')}")
        print(f"  aud: {decoded_unverified.get('aud')}")
        print(f"  iat: {decoded_unverified.get('iat')} (issued at)")
        print(f"  nbf: {decoded_unverified.get('nbf')} (not before)")
        print(f"  exp: {decoded_unverified.get('exp')} (expires)")
        print()
        
        # Check timing
        token_iat = decoded_unverified.get('iat')
        token_nbf = decoded_unverified.get('nbf')
        
        print("Timing analysis:")
        print(f"  Current timestamp: {current_timestamp}")
        print(f"  Token iat: {token_iat}")
        print(f"  Token nbf: {token_nbf}")
        print(f"  Difference (current - iat): {current_timestamp - token_iat} seconds")
        print(f"  Difference (current - nbf): {current_timestamp - token_nbf} seconds")
        print()
        
        if current_timestamp >= token_nbf:
            print("✅ Token timing looks good (current time >= nbf)")
        else:
            print(f"❌ Token timing issue: current time is {token_nbf - current_timestamp} seconds before nbf")
        print()
        
    except Exception as e:
        print(f"Error decoding token: {e}")
        return
    
    # Try verification
    print("Testing verification...")
    try:
        verified = jwt_manager.verify_token(token)
        print("✅ Token verification successful!")
        print(f"User: {verified.get('sub')}")
        print(f"Role: {verified.get('role')}")
    except Exception as e:
        print(f"❌ Token verification failed: {e}")
        
        # Try with a longer delay
        print("Waiting 2 seconds and trying again...")
        time.sleep(2)
        try:
            verified = jwt_manager.verify_token(token)
            print("✅ Token verification successful after delay!")
        except Exception as e2:
            print(f"❌ Still failing after delay: {e2}")

if __name__ == "__main__":
    debug_token_timing()