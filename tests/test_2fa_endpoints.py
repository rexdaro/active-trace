import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.auth import generate_totp_secret, generate_totp_token

@pytest.mark.asyncio
async def test_enrol_2fa():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/auth/2fa/enrol")
        assert response.status_code == 200
        data = response.json()
        assert "secret" in data
        assert "qr_code_uri" in data

@pytest.mark.asyncio
async def test_verify_2fa():
    secret = generate_totp_secret()
    token = generate_totp_token(secret)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Verify valid token
        response = await ac.post("/api/auth/2fa/verify", json={"secret": secret, "token": token})
        assert response.status_code == 200
        assert response.json() == {"message": "Verified"}
        
        # Verify invalid token
        response = await ac.post("/api/auth/2fa/verify", json={"secret": secret, "token": "000000"})
        assert response.status_code == 400
