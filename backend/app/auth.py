"""Auth dependencies for Bearer-protected routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .accounts import accounts

_bearer = HTTPBearer(auto_error=False)


def require_auth(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> dict[str, Any]:
    token = creds.credentials if creds else None
    ctx = accounts.resolve_token(token)
    if not ctx:
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Bearer token. Sign up/login or use demo token 'demo'.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return ctx


AuthContext = Annotated[dict[str, Any], Depends(require_auth)]
