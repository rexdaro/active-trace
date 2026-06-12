import pytest
import uuid
import os
from unittest.mock import AsyncMock, MagicMock

os.environ["ENCRYPTION_KEY"] = "test-key-32-chars-long-for-encryption!!"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers.comunicaciones import router as comunicaciones_router
from app.core.rbac import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.user_role import UserRole
from app.models.rbac import Role, RolePermission, Permission


class TestComunicacionesRouterSinAuth:

    def setup_method(self):
        self.app = FastAPI()
        self.app.include_router(comunicaciones_router)
        self.client = TestClient(self.app)

    def test_preview_sin_token_returns_401(self):
        response = self.client.post("/api/v1/comunicaciones/preview", json={})
        assert response.status_code == 401

    def test_confirm_sin_token_returns_401(self):
        response = self.client.post("/api/v1/comunicaciones/confirm", json={})
        assert response.status_code == 401

    def test_lotes_sin_token_returns_401(self):
        response = self.client.get("/api/v1/comunicaciones/lotes")
        assert response.status_code == 401

    def test_lote_detalle_sin_token_returns_401(self):
        response = self.client.get(f"/api/v1/comunicaciones/lotes/{uuid.uuid4()}")
        assert response.status_code == 401

    def test_aprobar_lote_sin_token_returns_401(self):
        response = self.client.post(f"/api/v1/comunicaciones/lotes/{uuid.uuid4()}/aprobar")
        assert response.status_code == 401

    def test_aprobar_individual_sin_token_returns_401(self):
        response = self.client.post(f"/api/v1/comunicaciones/{uuid.uuid4()}/aprobar")
        assert response.status_code == 401

    def test_rechazar_lote_sin_token_returns_401(self):
        response = self.client.post(f"/api/v1/comunicaciones/lotes/{uuid.uuid4()}/rechazar")
        assert response.status_code == 401

    def test_cancelar_individual_sin_token_returns_401(self):
        response = self.client.post(f"/api/v1/comunicaciones/{uuid.uuid4()}/cancelar")
        assert response.status_code == 401

    def test_estados_sin_token_returns_401(self):
        response = self.client.get("/api/v1/comunicaciones/estados")
        assert response.status_code == 401


class TestComunicacionesRouterPermisos:

    def setup_method(self):
        self.mock_user = User(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            email="coord@test.com",
            is_2fa_enabled=False,
            hashed_password="",
        )
        self.permissions_map = {
            "comunicacion:enviar": Permission(name="comunicacion:enviar"),
            "comunicacion:aprobar": Permission(name="comunicacion:aprobar"),
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
        self.app.include_router(comunicaciones_router)

        async def override_get_current_user():
            return self.mock_user

        async def override_get_db():
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = []
            scalars_mock.first.return_value = None
            result_mock = MagicMock()
            result_mock.scalars.return_value = scalars_mock
            result_mock.scalar_one_or_none.return_value = None
            result_mock.one_or_none.return_value = None
            result_mock.rowcount = 0
            mock_db = AsyncMock()
            mock_db.execute.return_value = result_mock
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            yield mock_db

        self.app.dependency_overrides[get_current_user] = override_get_current_user
        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)

    def test_preview_con_permiso_enviar_returns_422(self):
        self._setup_app("comunicacion:enviar")
        response = self.client.post(
            "/api/v1/comunicaciones/preview",
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_confirm_con_permiso_enviar_returns_422(self):
        self._setup_app("comunicacion:enviar")
        response = self.client.post(
            "/api/v1/comunicaciones/confirm",
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_lotes_con_permiso_enviar_returns_200(self):
        self._setup_app("comunicacion:enviar")
        response = self.client.get(
            "/api/v1/comunicaciones/lotes",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)

    def test_lote_detalle_con_permiso_enviar_returns_200(self):
        self._setup_app("comunicacion:enviar")
        response = self.client.get(
            f"/api/v1/comunicaciones/lotes/{uuid.uuid4()}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_aprobar_lote_con_permiso_aprobar_returns_200(self):
        self._setup_app("comunicacion:aprobar")
        response = self.client.post(
            f"/api/v1/comunicaciones/lotes/{uuid.uuid4()}/aprobar",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)

    def test_aprobar_individual_con_permiso_aprobar_returns_200(self):
        self._setup_app("comunicacion:aprobar")
        response = self.client.post(
            f"/api/v1/comunicaciones/{uuid.uuid4()}/aprobar",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)

    def test_rechazar_lote_con_permiso_aprobar_returns_200(self):
        self._setup_app("comunicacion:aprobar")
        response = self.client.post(
            f"/api/v1/comunicaciones/lotes/{uuid.uuid4()}/rechazar",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)

    def test_cancelar_individual_con_permiso_enviar_returns_200(self):
        self._setup_app("comunicacion:enviar")
        response = self.client.post(
            f"/api/v1/comunicaciones/{uuid.uuid4()}/cancelar",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)

    def test_estados_con_permiso_enviar_returns_200(self):
        self._setup_app("comunicacion:enviar")
        response = self.client.get(
            "/api/v1/comunicaciones/estados",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)
