from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from token_utils import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def verify_token(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user_id = payload.get("sub") or payload.get("user_id")
    email = payload.get("email")
    role = payload.get("role", "user")

    if not user_id:
        raise HTTPException(status_code=400, detail="'user_id' (sub) missing in token")

    return {
        "user_id": user_id,
        "email": email,
        "role": role,
    }
