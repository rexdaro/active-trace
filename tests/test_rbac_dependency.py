import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from app.core.rbac import check_permission

app = FastAPI()

@app.get("/protected")
async def protected_route(_ = Depends(check_permission("mod:read"))):
    return {"message": "success"}

client = TestClient(app)

def test_rbac_dependency_unauthorized():
    response = client.get("/protected")
    assert response.status_code == 401
