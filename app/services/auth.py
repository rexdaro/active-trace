import pyotp

def generate_totp_secret() -> str:
    return pyotp.random_base32()

def generate_totp_token(secret: str) -> str:
    totp = pyotp.TOTP(secret)
    return totp.now()

def verify_totp_token(secret: str, token: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(token)
