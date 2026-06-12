import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_test_route():
    response = client.get("/api/carreras/test")
    assert response.status_code == 200
    assert response.json() == {"message": "test"}
