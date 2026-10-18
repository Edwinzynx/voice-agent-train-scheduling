import secrets
from fastapi import Header, HTTPException
from .config import config_manager


def require_admin(authorization: str = Header(default="")):
    settings = config_manager.settings
    expected = settings.admin_token
    if not expected:
        if settings.environment != "production":
            return
        raise HTTPException(status_code=503, detail="Admin access is not configured.")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Administrator authentication required.", headers={"WWW-Authenticate": "Bearer"})
