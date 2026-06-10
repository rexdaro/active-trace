import pytest
import uuid
import os
from app.models.user import Usuario

@pytest.mark.asyncio
async def test_usuario_encryption_roundtrip():
    # Set a temporary key
    os.environ["ENCRYPTION_KEY"] = "super-secret-key-that-is-at-least-32-chars-long"
    
    usuario = Usuario(
        tenant_id=uuid.uuid4(),
        email="test@example.com",
        dni="12345678",
        cuil="20123456789",
        cbu="0000000000000000000000"
    )
    
    # Check if internal fields are encrypted
    assert usuario._email != "test@example.com"
    
    # Check decryption
    assert usuario.email == "test@example.com"
    assert usuario.dni == "12345678"
    assert usuario.cuil == "20123456789"
    assert usuario.cbu == "0000000000000000000000"
