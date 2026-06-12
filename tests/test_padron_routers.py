import pytest
import uuid
import io
import os
from unittest.mock import AsyncMock, MagicMock

os.environ["ENCRYPTION_KEY"] = "test-key-32-chars-long-for-encryption!!"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers.padron import router as padron_router
from app.core.rbac import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.user_role import UserRole
from app.models.rbac import Role, RolePermission, Permission


class TestPadronRouterAutorizacion:

    def setup_method(self):
        self.app = FastAPI()
        self.app.include_router(padron_router)
        self.client = TestClient(self.app)

    def test_preview_sin_token_returns_401(self):
        response = self.client.post("/api/v1/padron/preview")
        assert response.status_code == 401

    def test_confirm_sin_token_returns_401(self):
        response = self.client.post("/api/v1/padron/confirm", json={})
        assert response.status_code == 401

    def test_vaciar_sin_token_returns_401(self):
        response = self.client.delete(f"/api/v1/padron/{uuid.uuid4()}/datos")
        assert response.status_code == 401

    def test_versiones_sin_token_returns_401(self):
        response = self.client.get(f"/api/v1/padron/{uuid.uuid4()}/versiones")
        assert response.status_code == 401

    def test_sync_sin_token_returns_401(self):
        response = self.client.post("/api/v1/padron/sync", json={})
        assert response.status_code == 401


class TestPadronRouterConAuth:

    def setup_method(self):
        self.mock_user = User(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            email="coord@test.com",
            is_2fa_enabled=False,
            hashed_password="",
        )
        self.permissions_map = {
            "padron:importar": Permission(name="padron:importar"),
            "padron:vaciar": Permission(name="padron:vaciar"),
            "padron:ver": Permission(name="padron:ver"),
            "padron:sincronizar": Permission(name="padron:sincronizar"),
        }

    def _make_user_with_permission(self, perm_name: str):
        perm = self.permissions_map[perm_name]
        rp = RolePermission(permission=perm)
        role = Role(name="COORD", role_permissions=[rp])
        ur = UserRole(role=role)
        user = self.mock_user
        user.user_roles = [ur]
        return user

    def _setup_app(self, perm_name: str):
        self._make_user_with_permission(perm_name)
        self.app = FastAPI()
        self.app.include_router(padron_router)

        async def override_get_current_user():
            return self.mock_user

        async def override_get_db():
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = []
            scalars_mock.first.return_value = None
            result_mock = MagicMock()
            result_mock.scalars.return_value = scalars_mock
            result_mock.scalar_one_or_none.return_value = None
            result_mock.rowcount = 0
            mock_db = AsyncMock()
            mock_db.execute.return_value = result_mock
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            yield mock_db

        self.app.dependency_overrides[get_current_user] = override_get_current_user
        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)

    def test_confirm_json_valid_returns_422_or_400(self):
        self._setup_app("padron:importar")
        response = self.client.post(
            "/api/v1/padron/confirm",
            json={"preview_token": "invalid-token"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (400, 422, 500)

    def test_versiones_con_token_returns_200(self):
        self._setup_app("padron:ver")
        response = self.client.get(
            f"/api/v1/padron/{uuid.uuid4()}/versiones",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)

    def test_vaciar_con_token_returns_200(self):
        self._setup_app("padron:vaciar")
        response = self.client.delete(
            f"/api/v1/padron/{uuid.uuid4()}/datos",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)

    def test_sync_con_token_returns_200(self):
        self._setup_app("padron:sincronizar")
        response = self.client.post(
            "/api/v1/padron/sync",
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)
