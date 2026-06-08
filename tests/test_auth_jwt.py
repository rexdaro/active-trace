import pytest
from app.core.auth import create_access_token, verify_token, create_refresh_token
from datetime import timedelta

def test_create_and_verify_token():
    data = {"sub": "user123"}
    token = create_access_token(data)
    assert token is not None
    
    decoded = verify_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user123"

def test_verify_invalid_token():
    assert verify_token("invalid.token.string") is None

def test_create_refresh_token():
    data = {"sub": "user123"}
    token = create_refresh_token(data)
    assert token is not None
    
    decoded = verify_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user123"
    assert decoded["type"] == "refresh"

def test_verify_expired_token():
    data = {"sub": "user123"}
    # Token that expired 1 hour ago
    expired_token = create_access_token(data, expires_delta=timedelta(hours=-1))
    
    assert verify_token(expired_token) is None
