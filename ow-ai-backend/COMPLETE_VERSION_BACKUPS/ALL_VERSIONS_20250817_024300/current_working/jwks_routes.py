"""
JWKS (JSON Web Key Set) routes for RS256 public key distribution
"""

from fastapi import APIRouter, HTTPException
from .jwt_manager import get_jwt_manager

router = APIRouter()

@router.get("/.well-known/jwks.json")
async def get_jwks():
    """Public JWKS endpoint for token verification
    
    This endpoint provides the public keys needed to verify RS256 JWT tokens.
    Standard location: https://your-domain.com/.well-known/jwks.json
    """
    try:
        jwt_mgr = get_jwt_manager()
        jwks = jwt_mgr.get_jwks()
        return jwks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate JWKS: {str(e)}")

@router.get("/oauth/.well-known/jwks.json")
async def get_oauth_jwks():
    """OAuth2-compliant JWKS endpoint
    
    Alternative path for OAuth2 compliance
    """
    return await get_jwks()

@router.get("/jwks")
async def get_jwks_simple():
    """Simple JWKS endpoint (alternative path)"""
    return await get_jwks()
