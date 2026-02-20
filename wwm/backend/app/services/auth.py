from fastapi import Header, HTTPException

from app.core.config import settings


ROLE_PRIORITY = {"viewer": 1, "curator": 2, "admin": 3}


def resolve_role_from_api_key(x_api_key: str | None) -> str:
    if x_api_key == settings.api_key_admin:
        return "admin"
    if x_api_key == settings.api_key_curator:
        return "curator"
    return "viewer"


def require_role(min_role: str):
    def dependency(x_api_key: str | None = Header(default=None)) -> str:
        role = resolve_role_from_api_key(x_api_key)
        if ROLE_PRIORITY[role] < ROLE_PRIORITY[min_role]:
            raise HTTPException(status_code=403, detail=f"{min_role} role required")
        return role

    return dependency
