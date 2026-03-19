"""Auth router — /auth/register, /auth/login, /auth/me"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..database.repository import UserRepository
from ..utils import get_logger
from .schemas import UserCreate, Token, UserResponse
from .service import hash_password, verify_password, create_access_token, get_current_user
from ..database.models import UserDB


logger = get_logger(__name__)
router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.

    Returns the created user (without the password hash).
    Raises 409 if username or email is already taken.
    """
    if UserRepository.get_by_username(db, payload.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered",
        )
    if UserRepository.get_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = UserRepository.create_user(
        db,
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    logger.info(f"New user registered: {user.username}")
    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    OAuth2-compatible login endpoint.

    Accepts ``username`` + ``password`` form fields (standard OAuth2 form).
    Returns a Bearer JWT token on success.
    """
    user = UserRepository.get_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    token = create_access_token({"sub": user.username})
    logger.info(f"User logged in: {user.username}")
    return Token(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(current_user: UserDB = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return current_user
