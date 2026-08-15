import pytest
from datetime import datetime, timedelta
from jose import jwt
from backend.core.auth import verify_password, get_password_hash, create_access_token
from backend.config import settings

def test_password_hashing():
    plain_password = "super_secret_password"
    hashed_password = get_password_hash(plain_password)
    
    assert plain_password != hashed_password
    assert verify_password(plain_password, hashed_password) is True
    assert verify_password("wrong_password", hashed_password) is False

def test_create_access_token():
    data = {"sub": "testuser"}
    token = create_access_token(data)
    
    decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == "testuser"
    assert "exp" in decoded

def test_create_access_token_with_expiry():
    data = {"sub": "admin"}
    expires = timedelta(minutes=10)
    token = create_access_token(data, expires_delta=expires)
    
    decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == "admin"
