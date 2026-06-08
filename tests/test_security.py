import pytest
from app.core.security import encrypt, decrypt

def test_encryption_decryption():
    original_data = "sensitive-pii-data"
    key = "secret-key-that-is-32-bytes-long" # 32 bytes for AES-256
    
    encrypted = encrypt(original_data, key)
    decrypted = decrypt(encrypted, key)
    
    assert decrypted == original_data
    assert encrypted != original_data

def test_encryption_decryption_long_string():
    original_data = "a" * 1000
    key = "secret-key"
    
    encrypted = encrypt(original_data, key)
    decrypted = decrypt(encrypted, key)
    
    assert decrypted == original_data

def test_encryption_decryption_special_chars():
    original_data = "!@#$%^&*()_+{}|:<>?1234567890-=[]\\;',./"
    key = "secret-key"
    
    encrypted = encrypt(original_data, key)
    decrypted = decrypt(encrypted, key)
    
    assert decrypted == original_data
