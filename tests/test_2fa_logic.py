import pytest
from app.services.auth import generate_totp_secret, verify_totp_token, generate_totp_token

def test_totp_generation_and_verification():
    secret = generate_totp_secret()
    token = generate_totp_token(secret)
    
    # Verify the token
    assert verify_totp_token(secret, token)
    
    # Verify wrong token
    assert not verify_totp_token(secret, "000000")

def test_totp_invalid_token():
    secret = generate_totp_secret()
    assert not verify_totp_token(secret, "invalid")

def test_totp_empty_token():
    secret = generate_totp_secret()
    assert not verify_totp_token(secret, "")
