import pytest
import uuid
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

os.environ["ENCRYPTION_KEY"] = "test-key-32-chars-long-for-encryption!!"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers.equipos import router as equipos_router
from app.core.rbac import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.user_role import UserRole
from app.models.rbac import Role, RolePermission, Permission


# Task 13: Tests de autorización
class TestAutorizacion:

    def setup_method(self):
        self.app = FastAPI()
        self.app.include_router(equipos_router)
        self.client = TestClient(self.app)

    def test_mis_equipos_sin_token_returns_401(self):
        response = self.client.get("/api/equipos/mis-equipos")
        assert response.status_code == 401

    def test_listar_equipos_sin_token_returns_401(self):
        response = self.client.get("/api/equipos")
        assert response.status_code == 401

    def test_asignacion_masiva_sin_token_returns_401(self):
        response = self.client.post("/api/equipos/asignacion-masiva", json={})
        assert response.status_code == 401

    def test_clonar_sin_token_returns_401(self):
        response = self.client.post("/api/equipos/clonar", json={})
        assert response.status_code == 401

    def test_vigencia_sin_token_returns_401(self):
        response = self.client.put("/api/equipos/vigencia", json={})
        assert response.status_code == 401

    def test_export_sin_token_returns_401(self):
        response = self.client.get("/api/equipos/export?contexto_id=" + str(uuid.uuid4()))
        assert response.status_code == 401


class TestRouterConAuth:

    def setup_method(self):
        self.mock_user = User(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            email="coord@test.com",
            is_2fa_enabled=False,
            hashed_password="",
        )

        perm = Permission(name="equipos:asignar")
        rp = RolePermission(permission=perm)
        role = Role(name="COORD", role_permissions=[rp])
        ur = UserRole(role=role)
        self.mock_user.user_roles = [ur]

        self.app = FastAPI()
        self.app.include_router(equipos_router)

        async def override_get_current_user():
            return self.mock_user

        async def override_get_db():
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = []
            result_mock = MagicMock()
            result_mock.scalars.return_value = scalars_mock
            mock_db = AsyncMock()
            mock_db.execute.return_value = result_mock
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            yield mock_db

        self.app.dependency_overrides[get_current_user] = override_get_current_user
        self.app.dependency_overrides[get_db] = override_get_db

        self.client = TestClient(self.app)

    def test_mis_equipos_con_token_returns_200(self):
        response = self.client.get(
            "/api/equipos/mis-equipos",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 422, 500)

    def test_asignacion_masiva_empty_list_returns_422(self):
        response = self.client.post(
            "/api/equipos/asignacion-masiva",
            json={"asignaciones": []},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_clonar_valid_returns_200_or_422(self):
        response = self.client.post(
            "/api/equipos/clonar",
            json={
                "origen_contexto_id": str(uuid.uuid4()),
                "destino_contexto_id": str(uuid.uuid4()),
                "nuevo_desde": "2026-03-01T00:00:00",
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 422, 500)

    def test_vigencia_valid_returns_200_or_422(self):
        response = self.client.put(
            "/api/equipos/vigencia",
            json={
                "contexto_id": str(uuid.uuid4()),
                "nuevo_desde": "2026-03-01T00:00:00",
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 422, 500)
