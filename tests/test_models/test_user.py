import pytest
import uuid
import os
from app.models.user import User

@pytest.mark.asyncio
async def test_usuario_encryption_roundtrip():
    os.environ["ENCRYPTION_KEY"] = "super-secret-key-that-is-at-least-32-chars-long"

    user = User(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="x",
        dni="12345678",
        cuil="20123456789",
        cbu="0000000000000000000000",
    )

    assert user._dni != "12345678"
    assert user._cuil != "20123456789"

    assert user.dni == "12345678"
    assert user.cuil == "20123456789"
    assert user.cbu == "0000000000000000000000"
    assert user.email == "test@example.com"
