import pytest
import pytest_asyncio
import uuid
import os
from datetime import datetime, timezone

os.environ["ENCRYPTION_KEY"] = "test-key-32-chars-long-for-encryption!!"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers.perfil import router as perfil_router
from app.core.rbac import get_current_user
from app.core.database import get_db
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User, Usuario
from app.models.user_role import UserRole
from app.models.rbac import Role, Permission, RolePermission
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from sqlalchemy.orm import selectinload


class TestPerfilRouterSinAuth:

    def setup_method(self):
        self.app = FastAPI()
        self.app.include_router(perfil_router)
        self.client = TestClient(self.app)

    def test_get_sin_token_returns_401(self):
        response = self.client.get("/api/v1/perfil")
        assert response.status_code == 401

    def test_put_sin_token_returns_401(self):
        response = self.client.put("/api/v1/perfil", json={})
        assert response.status_code == 401


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def integration_setup(db_session):
    tenant = Tenant(id=uuid.uuid4(), name="Test Tenant")
    db_session.add(tenant)

    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email="user@test.com",
        hashed_password="hashed",
        is_2fa_enabled=False,
    )
    db_session.add(user)

    import app.core.security as sec
    key = os.environ.get("ENCRYPTION_KEY", "dev-key")
    usuario = Usuario(
        id=user.id,
        tenant_id=tenant.id,
        nombre="Original Nombre",
    )
    usuario._email = sec.encrypt("user@test.com", key)
    usuario._dni = sec.encrypt("12345678", key)
    usuario._cuil = sec.encrypt("20-12345678-9", key)
    usuario._cbu = sec.encrypt("0000003100000000000001", key)
    db_session.add(usuario)
    await db_session.commit()

    app = FastAPI()
    app.include_router(perfil_router)

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return user

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    return client, tenant, user, usuario, db_session


class TestPerfilRouterIntegration:

    @pytest.mark.asyncio
    async def test_get_perfil(self, integration_setup):
        client, tenant, user, usuario, db = integration_setup
        response = client.get("/api/v1/perfil", headers={"Authorization": "Bearer test-token"})
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "user@test.com"
        assert data["dni"] == "12345678"
        assert data["cuil"] == "20-12345678-9"
        assert data["nombre"] == "Original Nombre"
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_update_perfil_ok(self, integration_setup):
        client, tenant, user, usuario, db = integration_setup
        payload = {
            "nombre": "Nuevo Nombre",
            "datos_fiscales": "Monotributista",
            "regional": "CABA",
            "modalidad_cobro": "Transferencia",
        }
        response = client.put(
            "/api/v1/perfil",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Nuevo Nombre"
        assert data["datos_fiscales"] == "Monotributista"
        assert data["regional"] == "CABA"
        assert data["modalidad_cobro"] == "Transferencia"
        assert data["cuil"] == "20-12345678-9"

    @pytest.mark.asyncio
    async def test_update_perfil_cuil_rechazado(self, integration_setup):
        client, tenant, user, usuario, db = integration_setup
        payload = {"cuil": "99-99999999-9"}
        response = client.put(
            "/api/v1/perfil",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 400
        assert "CUIL" in response.text

    @pytest.mark.asyncio
    async def test_update_perfil_extra_fields_forbidden(self, integration_setup):
        client, tenant, user, usuario, db = integration_setup
        payload = {"nombre": "Test", "extra_field": "should_fail"}
        response = client.put(
            "/api/v1/perfil",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422
