import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.middleware.audit import AuditLogMiddleware
from unittest.mock import AsyncMock, patch

def test_audit_log_middleware_captures_impersonation():
    app = FastAPI()
    app.add_middleware(AuditLogMiddleware)
    
    @app.get("/")
    async def root():
        return {"message": "Hello World"}
    
    with patch("app.middleware.audit.AuditService.log_action", new_callable=AsyncMock) as mock_log:
        client = TestClient(app)
        response = client.get("/", headers={"X-User-ID": "test_user", "X-Impersonator-ID": "admin_user"})
        assert response.status_code == 200
        
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        assert kwargs["impersonator_id"] == "admin_user"
        assert kwargs["actor_id"] == "test_user"
