"""Chỉ cho BE gọi: kiểm header X-Internal-Key."""
import secrets

from fastapi import Header, HTTPException, status

from app.core.config import settings


def require_internal_key(x_internal_key: str | None = Header(default=None)) -> None:
    if not settings.internal_key:
        return
    if not x_internal_key or not secrets.compare_digest(x_internal_key, settings.internal_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sai X-Internal-Key")
