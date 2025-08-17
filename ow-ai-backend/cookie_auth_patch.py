async def reject_bearer_tokens(request: Request):
    """
    Reject Bearer tokens for enterprise cookie-only authentication
    But be more selective about which paths to protect
    """
    auth_header = request.headers.get("authorization", "")
    
    # Only reject Bearer tokens on specific sensitive paths
    protected_paths = [
        "/auth/",
        "/admin/",
        "/enterprise/"
    ]
    
    # Check if this is a protected path
    is_protected = any(request.url.path.startswith(path) for path in protected_paths)
    
    if auth_header.startswith("Bearer ") and is_protected:
        logger.warning(f"Rejected Bearer token attempt from {request.client.host}")
        raise HTTPException(
            status_code=401,
            detail="Bearer tokens not allowed. Use cookie authentication.",
            headers={"WWW-Authenticate": "Cookie"}
        )
    
    # For other paths, allow Bearer tokens but prefer cookies
    return True
