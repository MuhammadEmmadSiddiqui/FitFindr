"""Authentication module — JWT + bcrypt"""
from .router import router as auth_router
from .service import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

__all__ = [
    "auth_router",
    "hash_password",
    "verify_password",
    "create_access_token",
    "get_current_user",
]
