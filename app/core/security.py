import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def encrypt(data: str, key: str) -> str:
    # Use the first 32 bytes of the key for AES-256
    key_bytes = key.encode('utf-8')
    if len(key_bytes) < 32:
        # Pad or hash? Prompt says: "Create an encryption helper".
        # Let's pad for simplicity or raise error.
        # Actually, let's just use the key. It's a helper.
        key_bytes = key_bytes.ljust(32, b'\0')
    else:
        key_bytes = key_bytes[:32]
        
    aesgcm = AESGCM(key_bytes)
    nonce = os.urandom(12) # GCM recommended nonce length
    ciphertext = aesgcm.encrypt(nonce, data.encode('utf-8'), None)
    return base64.b64encode(nonce + ciphertext).decode('utf-8')

def decrypt(token: str, key: str) -> str:
    key_bytes = key.encode('utf-8')
    if len(key_bytes) < 32:
        key_bytes = key_bytes.ljust(32, b'\0')
    else:
        key_bytes = key_bytes[:32]
        
    aesgcm = AESGCM(key_bytes)
    token_bytes = base64.b64decode(token)
    nonce = token_bytes[:12]
    ciphertext = token_bytes[12:]
    return aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
