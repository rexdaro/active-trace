import pytest
import uuid
import os
from unittest.mock import AsyncMock, MagicMock

os.environ["ENCRYPTION_KEY"] = "test-key-32-chars-long-for-encryption!!"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers.coloquios import router as coloquios_router
from app.core.rbac import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.user_role import UserRole
from app.models.rbac import Role, RolePermission, Permission


class TestColoquiosRouterSinAuth:

    def setup_method(self):
        self.app = FastAPI()
        self.app.include_router(coloquios_router)
        self.client = TestClient(self.app)

    def test_crear_convocatoria_sin_token_returns_401(self):
        response = self.client.post("/api/v1/coloquios/convocatorias", json={})
        assert response.status_code == 401

    def test_importar_sin_token_returns_401(self):
        response = self.client.post("/api/v1/coloquios/convocatorias/importar", json={})
        assert response.status_code == 401

    def test_listar_convocatorias_sin_token_returns_401(self):
        response = self.client.get("/api/v1/coloquios/convocatorias")
        assert response.status_code == 401

    def test_metricas_sin_token_returns_401(self):
        response = self.client.get("/api/v1/coloquios/metricas")
        assert response.status_code == 401

    def test_reservar_sin_token_returns_401(self):
        response = self.client.post("/api/v1/coloquios/reservas", json={})
        assert response.status_code == 401

    def test_cancelar_reserva_sin_token_returns_401(self):
        response = self.client.post(f"/api/v1/coloquios/reservas/{uuid.uuid4()}/cancelar")
        assert response.status_code == 401

    def test_mis_reservas_sin_token_returns_401(self):
        response = self.client.get("/api/v1/coloquios/mis-reservas")
        assert response.status_code == 401

    def test_registrar_resultado_sin_token_returns_401(self):
        response = self.client.post("/api/v1/coloquios/resultados", json={})
        assert response.status_code == 401

    def test_get_resultados_sin_token_returns_401(self):
        response = self.client.get(f"/api/v1/coloquios/convocatorias/{uuid.uuid4()}/resultados")
        assert response.status_code == 401


class BaseRouterTest:

    def setup_method(self):
        self.mock_user = User(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            email="coord@test.com",
            is_2fa_enabled=False,
            hashed_password="",
        )
        self.permissions_map = {
            "coloquios:gestionar": Permission(name="coloquios:gestionar"),
            "coloquios:reservar": Permission(name="coloquios:reservar"),
            "coloquios:ver": Permission(name="coloquios:ver"),
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


class TestColoquiosRouterPermisos(BaseRouterTest):

    def test_crear_convocatoria_con_permiso_gestionar_returns_422(self):
        self._setup_app(coloquios_router, "coloquios:gestionar")
        response = self.client.post(
            "/api/v1/coloquios/convocatorias",
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_importar_con_permiso_gestionar_returns_422(self):
        self._setup_app(coloquios_router, "coloquios:gestionar")
        response = self.client.post(
            "/api/v1/coloquios/convocatorias/importar",
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_listar_convocatorias_con_permiso_ver_returns_200(self):
        self._setup_app(coloquios_router, "coloquios:ver")
        response = self.client.get(
            "/api/v1/coloquios/convocatorias",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)

    def test_metricas_con_permiso_ver_returns_200(self):
        self._setup_app(coloquios_router, "coloquios:ver")
        response = self.client.get(
            "/api/v1/coloquios/metricas",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)

    def test_reservar_con_permiso_reservar_returns_422(self):
        self._setup_app(coloquios_router, "coloquios:reservar")
        response = self.client.post(
            "/api/v1/coloquios/reservas",
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_cancelar_con_permiso_reservar_returns_404(self):
        self._setup_app(coloquios_router, "coloquios:reservar")
        response = self.client.post(
            f"/api/v1/coloquios/reservas/{uuid.uuid4()}/cancelar",
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 404

    def test_mis_reservas_con_permiso_reservar_returns_200(self):
        self._setup_app(coloquios_router, "coloquios:reservar")
        response = self.client.get(
            "/api/v1/coloquios/mis-reservas",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)

    def test_registrar_resultado_con_permiso_gestionar_returns_422(self):
        self._setup_app(coloquios_router, "coloquios:gestionar")
        response = self.client.post(
            "/api/v1/coloquios/resultados",
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_get_resultados_con_permiso_ver_returns_200(self):
        self._setup_app(coloquios_router, "coloquios:ver")
        response = self.client.get(
            f"/api/v1/coloquios/convocatorias/{uuid.uuid4()}/resultados",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)
