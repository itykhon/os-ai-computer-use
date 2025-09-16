from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request, status


def get_bearer_token_from_header(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth:
        return None
    if not auth.lower().startswith("bearer "):
        return None
    return auth[7:].strip()


def require_token(request: Request, expected_token: Optional[str]) -> None:
    if not expected_token:
        return
    provided = get_bearer_token_from_header(request)
    if provided != expected_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token")


