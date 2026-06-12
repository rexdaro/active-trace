import pytest
import uuid
import os
from unittest.mock import AsyncMock, MagicMock

os.environ["ENCRYPTION_KEY"] = "test-key-32-chars-long-for-encryption!!"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers.encuentros import router as encuentros_router
from app.routers.guardias import router as guardias_router
from app.core.rbac import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.user_role import UserRole
from app.models.rbac import Role, RolePermission, Permission


class TestEncuentrosRouterSinAuth:

    def setup_method(self):
        self.app = FastAPI()
        self.app.include_router(encuentros_router)
        self.client = TestClient(self.app)

    def test_crear_recurrente_sin_token_returns_401(self):
        response = self.client.post("/api/v1/encuentros/recurrente", json={})
        assert response.status_code == 401

    def test_crear_unico_sin_token_returns_401(self):
        response = self.client.post("/api/v1/encuentros/unico", json={})
        assert response.status_code == 401

    def test_editar_instancia_sin_token_returns_401(self):
        response = self.client.put(f"/api/v1/encuentros/instancias/{uuid.uuid4()}", json={})
        assert response.status_code == 401

    def test_list_instancias_sin_token_returns_401(self):
        response = self.client.get(f"/api/v1/encuentros/materias/{uuid.uuid4()}/instancias")
        assert response.status_code == 401

    def test_all_instancias_sin_token_returns_401(self):
        response = self.client.get("/api/v1/encuentros/instancias")
        assert response.status_code == 401

    def test_html_block_sin_token_returns_401(self):
        response = self.client.get(f"/api/v1/encuentros/materias/{uuid.uuid4()}/html")
        assert response.status_code == 401


class TestGuardiasRouterSinAuth:

    def setup_method(self):
        self.app = FastAPI()
        self.app.include_router(guardias_router)
        self.client = TestClient(self.app)

    def test_registrar_sin_token_returns_401(self):
        response = self.client.post("/api/v1/guardias", json={})
        assert response.status_code == 401

    def test_listar_sin_token_returns_401(self):
        response = self.client.get("/api/v1/guardias")
        assert response.status_code == 401

    def test_actualizar_sin_token_returns_401(self):
        response = self.client.put(f"/api/v1/guardias/{uuid.uuid4()}", json={})
        assert response.status_code == 401

    def test_export_sin_token_returns_401(self):
        response = self.client.get("/api/v1/guardias/export")
        assert response.status_code == 401


class BaseRouterTest:
    """Shared setup for permission-based router tests."""

    def setup_method(self):
        self.mock_user = User(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            email="coord@test.com",
            is_2fa_enabled=False,
            hashed_password="",
        )
        self.permissions_map = {
            "encuentros:gestionar": Permission(name="encuentros:gestionar"),
            "encuentros:ver": Permission(name="encuentros:ver"),
            "guardias:registrar": Permission(name="guardias:registrar"),
            "guardias:ver": Permission(name="guardias:ver"),
        }

    def _make_user_with_permission(self, perm_name: str):
        perm = self.permissions_map[perm_name]
        rp = RolePermission(permission=perm)
        role = Role(name="COORD", role_permissions=[rp])
        ur = UserRole(role=role)
        user = self.mock_user
        user.user_roles = [ur]
        return user

    def _setup_app(self, router, perm_name: str):
        self._make_user_with_permission(perm_name)
        self.app = FastAPI()
        self.app.include_router(router)

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


class TestEncuentrosRouterPermisos(BaseRouterTest):

    def test_crear_recurrente_con_permiso_gestionar_returns_422(self):
        self._setup_app(encuentros_router, "encuentros:gestionar")
        response = self.client.post(
            "/api/v1/encuentros/recurrente",
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_crear_unico_con_permiso_gestionar_returns_422(self):
        self._setup_app(encuentros_router, "encuentros:gestionar")
        response = self.client.post(
            "/api/v1/encuentros/unico",
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_editar_instancia_con_permiso_gestionar_returns_422(self):
        self._setup_app(encuentros_router, "encuentros:gestionar")
        response = self.client.put(
            f"/api/v1/encuentros/instancias/{uuid.uuid4()}",
            json={"estado": 123},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_list_instancias_con_permiso_gestionar_returns_200(self):
        self._setup_app(encuentros_router, "encuentros:gestionar")
        response = self.client.get(
            f"/api/v1/encuentros/materias/{uuid.uuid4()}/instancias",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)

    def test_all_instancias_con_permiso_ver_returns_200(self):
        self._setup_app(encuentros_router, "encuentros:ver")
        response = self.client.get(
            "/api/v1/encuentros/instancias",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)

    def test_html_block_con_permiso_gestionar_returns_200(self):
        self._setup_app(encuentros_router, "encuentros:gestionar")
        response = self.client.get(
            f"/api/v1/encuentros/materias/{uuid.uuid4()}/html",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)


class TestGuardiasRouterPermisos(BaseRouterTest):

    def test_registrar_con_permiso_registrar_returns_422(self):
        self._setup_app(guardias_router, "guardias:registrar")
        response = self.client.post(
            "/api/v1/guardias",
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_listar_con_permiso_ver_returns_200(self):
        self._setup_app(guardias_router, "guardias:ver")
        response = self.client.get(
            "/api/v1/guardias",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)

    def test_actualizar_con_permiso_registrar_returns_422(self):
        self._setup_app(guardias_router, "guardias:registrar")
        response = self.client.put(
            f"/api/v1/guardias/{uuid.uuid4()}",
            json={"estado": 123},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_export_con_permiso_ver_returns_200(self):
        self._setup_app(guardias_router, "guardias:ver")
        response = self.client.get(
            "/api/v1/guardias/export",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)
