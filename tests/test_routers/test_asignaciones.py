import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_asignacion_validation():
    # Invalid data: missing required fields
    response = client.post("/api/asignaciones/", json={
        "user_id": "not-a-uuid"
    })
    assert response.status_code == 422 # Unprocessable Entity
