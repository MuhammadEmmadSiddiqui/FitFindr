"""Auth request/response schemas"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """New user registration payload"""
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Login credentials"""
    username: str
    password: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded token payload"""
    username: Optional[str] = None


class UserResponse(BaseModel):
    """Public user info returned to clients"""
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
