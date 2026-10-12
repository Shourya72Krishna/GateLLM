import secrets

from fastapi import Header, HTTPException

from app.config import settings
from app.ratelimit import check_rate_limit


async def require_api_key(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization[len("Bearer "):].strip()
    if not secrets.compare_digest(token.encode(), settings.gateway_api_key.encode()):
        raise HTTPException(status_code=401, detail="Invalid API key")
    check_rate_limit(token)
    return token