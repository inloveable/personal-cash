"""鉴权：单一 Bearer Token，REST 与 /mcp 统一 401。"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import settings

_bearer = HTTPBearer(auto_error=False)


def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or credentials.credentials != settings.api_token
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或缺失的访问令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
