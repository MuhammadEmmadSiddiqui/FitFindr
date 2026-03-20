"""Unit tests for authentication service (password hashing and JWT)."""
import pytest
from datetime import timedelta
from jose import jwt

from src.auth.service import hash_password, verify_password, create_access_token
from src.config import settings


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def test_hash_password_is_not_plain():
    """Hashed password must differ from the plain-text input."""
    plain = "mysecretpassword"
    hashed = hash_password(plain)
    assert hashed != plain


def test_hash_password_is_bcrypt():
    """Result should be a bcrypt hash (starts with $2b$)."""
    hashed = hash_password("anypassword")
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")


def test_verify_correct_password():
    """verify_password returns True when plain matches the hash."""
    plain = "correctpassword"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed) is True


def test_verify_wrong_password():
    """verify_password returns False for a password that doesn't match."""
    hashed = hash_password("correctpassword")
    assert verify_password("wrongpassword", hashed) is False


def test_verify_empty_string_fails():
    """verify_password returns False when checking empty string against a real hash."""
    hashed = hash_password("somepassword")
    assert verify_password("", hashed) is False


def test_two_hashes_of_same_password_differ():
    """bcrypt uses a random salt — identical inputs produce different hashes."""
    plain = "samepassword"
    hash1 = hash_password(plain)
    hash2 = hash_password(plain)
    assert hash1 != hash2
    # But both must verify correctly
    assert verify_password(plain, hash1)
    assert verify_password(plain, hash2)


# ---------------------------------------------------------------------------
# JWT token creation
# ---------------------------------------------------------------------------

def test_create_access_token_contains_sub():
    """Token payload must contain the 'sub' claim we passed in."""
    token = create_access_token({"sub": "testuser"})
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "testuser"


def test_create_access_token_contains_exp():
    """Token payload must contain an 'exp' (expiry) claim."""
    token = create_access_token({"sub": "testuser"})
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert "exp" in payload


def test_create_access_token_custom_expiry():
    """Custom expires_delta is respected (token should be valid for that window)."""
    token = create_access_token({"sub": "testuser"}, expires_delta=timedelta(minutes=5))
    # If the token were already expired this decode would raise; absence of exception = pass
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "testuser"


def test_token_invalid_secret_fails():
    """Decoding with a wrong secret must raise JWTError."""
    from jose import JWTError
    token = create_access_token({"sub": "testuser"})
    with pytest.raises(JWTError):
        jwt.decode(token, "wrong-secret", algorithms=[settings.ALGORITHM])


def test_token_wrong_algorithm_fails():
    """Decoding with a wrong algorithm must raise JWTError."""
    from jose import JWTError
    token = create_access_token({"sub": "testuser"})
    with pytest.raises(JWTError):
        jwt.decode(token, settings.SECRET_KEY, algorithms=["RS256"])
