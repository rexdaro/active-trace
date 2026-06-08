import pytest
from app.models.user import User

def test_user_has_new_fields():
    user = User(email="test@example.com")
    
    # These should fail if fields don't exist
    assert hasattr(user, "hashed_password")
    assert hasattr(user, "is_2fa_enabled")
    assert hasattr(user, "totp_secret")
    assert hasattr(user, "refresh_tokens")
