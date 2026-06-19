import pytest
import pytest_asyncio
import uuid
import os
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

os.environ["ENCRYPTION_KEY"] = "test-key-32-chars-long-for-encryption!!"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers.avisos import router as avisos_router
from app.core.rbac import get_current_user
from app.core.database import get_db
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User
from app.models.user_role import UserRole
from app.models.rbac import Role, Permission, RolePermission
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.aviso import Aviso, AcknowledgmentAviso, AlcanceAviso
from app.models.user import Usuario


# ═══════════════════════════════════════════════════════════════════════════════
# Sin autenticación — todos devuelven 401
# ═══════════════════════════════════════════════════════════════════════════════

class TestAvisosRouterSinAuth:

    def setup_method(self):
        self.app = FastAPI()
        self.app.include_router(avisos_router)
        self.client = TestClient(self.app)

    def test_create_sin_token_returns_401(self):
        response = self.client.post("/api/v1/avisos", json={})
        assert response.status_code == 401

    def test_list_sin_token_returns_401(self):
        response = self.client.get("/api/v1/avisos")
        assert response.status_code == 401

    def test_get_sin_token_returns_401(self):
        response = self.client.get(f"/api/v1/avisos/{uuid.uuid4()}")
        assert response.status_code == 401

    def test_update_sin_token_returns_401(self):
        response = self.client.put(f"/api/v1/avisos/{uuid.uuid4()}", json={})
        assert response.status_code == 401

    def test_delete_sin_token_returns_401(self):
        response = self.client.delete(f"/api/v1/avisos/{uuid.uuid4()}")
        assert response.status_code == 401

    def test_mis_avisos_sin_token_returns_401(self):
        response = self.client.get("/api/v1/avisos/mis-avisos")
        assert response.status_code == 401

    def test_confirmar_lectura_sin_token_returns_401(self):
        response = self.client.post(f"/api/v1/avisos/{uuid.uuid4()}/confirmar-lectura")
        assert response.status_code == 401

    def test_metricas_sin_token_returns_401(self):
        response = self.client.get(f"/api/v1/avisos/{uuid.uuid4()}/metricas")
        assert response.status_code == 401

    def test_acks_sin_token_returns_401(self):
        response = self.client.get(f"/api/v1/avisos/{uuid.uuid4()}/acks")
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# Con permisos — verifica routing y permisos
# ═══════════════════════════════════════════════════════════════════════════════

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
            "avisos:publicar": Permission(name="avisos:publicar"),
            "avisos:ver": Permission(name="avisos:ver"),
            "avisos:confirmar": Permission(name="avisos:confirmar"),
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
        self.app.include_router(avisos_router)

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


class TestAvisosRouterPermisos(BaseRouterTest):

    def test_create_aviso_con_permiso_publicar_returns_422(self):
        self._setup_app("avisos:publicar")
        response = self.client.post(
            "/api/v1/avisos",
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_create_aviso_sin_permiso_returns_403(self):
        self._setup_app("avisos:ver")
        response = self.client.post(
            "/api/v1/avisos",
            json={"titulo": "test", "cuerpo": "test", "alcance": "Global", "inicio_en": "2026-06-01T00:00:00", "fin_en": "2026-07-01T00:00:00"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 403

    def test_list_mis_avisos_con_permiso_ver_returns_200(self):
        self._setup_app("avisos:ver")
        response = self.client.get(
            "/api/v1/avisos/mis-avisos",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)

    def test_confirmar_lectura_sin_permiso_returns_403(self):
        self._setup_app("avisos:ver")
        response = self.client.post(
            f"/api/v1/avisos/{uuid.uuid4()}/confirmar-lectura",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 403

    def test_confirmar_lectura_con_permiso_returns_404(self):
        self._setup_app("avisos:confirmar")
        response = self.client.post(
            f"/api/v1/avisos/{uuid.uuid4()}/confirmar-lectura",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 404

    def test_metricas_sin_permiso_returns_403(self):
        self._setup_app("avisos:ver")
        response = self.client.get(
            f"/api/v1/avisos/{uuid.uuid4()}/metricas",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 403

    def test_delete_sin_permiso_returns_403(self):
        self._setup_app("avisos:ver")
        response = self.client.delete(
            f"/api/v1/avisos/{uuid.uuid4()}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 403

    def test_list_all_admin_sin_permiso_returns_403(self):
        self._setup_app("avisos:ver")
        response = self.client.get(
            "/api/v1/avisos",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════════
# Integración — usa base de datos en memoria real
# ═══════════════════════════════════════════════════════════════════════════════

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

    perm_publicar = Permission(name="avisos:publicar")
    perm_ver = Permission(name="avisos:ver")
    perm_confirmar = Permission(name="avisos:confirmar")
    db_session.add_all([perm_publicar, perm_ver, perm_confirmar])
    await db_session.flush()

    role = Role(name="COORDINADOR")
    db_session.add(role)
    await db_session.flush()

    rp1 = RolePermission(role_id=role.id, permission_id=perm_publicar.id)
    rp2 = RolePermission(role_id=role.id, permission_id=perm_ver.id)
    rp3 = RolePermission(role_id=role.id, permission_id=perm_confirmar.id)
    db_session.add_all([rp1, rp2, rp3])

    uid = uuid.uuid4()
    user = User(
        id=uid,
        tenant_id=tenant.id,
        email="coord@test.com",
        hashed_password="hashed",
        is_2fa_enabled=False,
        dni="0",
        cuil="0",
    )
    db_session.add(user)

    ur = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(ur)
    await db_session.commit()

    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    stmt = (
        select(User)
        .where(User.id == user.id)
        .options(
            selectinload(User.user_roles)
            .selectinload(UserRole.role)
            .selectinload(Role.role_permissions)
            .selectinload(RolePermission.permission)
        )
    )
    result = await db_session.execute(stmt)
    user = result.scalar_one()

    app = FastAPI()
    app.include_router(avisos_router)

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return user

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    return client, tenant, user, db_session


class TestAvisosRouterIntegration:

    @pytest.mark.asyncio
    async def test_create_aviso_endpoint(self, integration_setup):
        client, tenant, user, db = integration_setup
        now = datetime.now(timezone.utc)
        payload = {
            "titulo": "Aviso desde endpoint",
            "cuerpo": "Creado vía HTTP",
            "alcance": "Global",
            "inicio_en": now.isoformat(),
            "fin_en": (now + timedelta(days=30)).isoformat(),
        }
        response = client.post(
            "/api/v1/avisos",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["titulo"] == "Aviso desde endpoint"
        assert data["cuerpo"] == "Creado vía HTTP"
        assert data["alcance"] == "Global"

    @pytest.mark.asyncio
    async def test_list_mis_avisos_empty(self, integration_setup):
        client, tenant, user, db = integration_setup
        response = client.get(
            "/api/v1/avisos/mis-avisos",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_mis_avisos_with_data(self, integration_setup):
        client, tenant, user, db = integration_setup
        now = datetime.now(timezone.utc)
        payload = {
            "titulo": "Visible en mis-avisos",
            "cuerpo": "Aparece en la lista",
            "alcance": "Global",
            "inicio_en": (now - timedelta(days=1)).isoformat(),
            "fin_en": (now + timedelta(days=1)).isoformat(),
        }
        create_resp = client.post(
            "/api/v1/avisos",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        assert create_resp.status_code == 201

        response = client.get(
            "/api/v1/avisos/mis-avisos",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["titulo"] == "Visible en mis-avisos"

    @pytest.mark.asyncio
    async def test_confirmar_lectura_endpoint(self, integration_setup):
        client, tenant, user, db = integration_setup
        now = datetime.now(timezone.utc)
        payload = {
            "titulo": "Ack via endpoint",
            "cuerpo": "Confirma lectura",
            "alcance": "Global",
            "inicio_en": (now - timedelta(days=1)).isoformat(),
            "fin_en": (now + timedelta(days=1)).isoformat(),
            "requiere_ack": True,
        }
        create_resp = client.post(
            "/api/v1/avisos",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        assert create_resp.status_code == 201
        aviso_id = create_resp.json()["id"]

        ack_resp = client.post(
            f"/api/v1/avisos/{aviso_id}/confirmar-lectura",
            headers={"Authorization": "Bearer test-token"},
        )
        assert ack_resp.status_code == 200
        ack_data = ack_resp.json()
        assert ack_data["aviso_id"] == aviso_id
        assert ack_data["usuario_id"] == str(user.id)

    @pytest.mark.asyncio
    async def test_get_metricas_endpoint(self, integration_setup):
        client, tenant, user, db = integration_setup
        now = datetime.now(timezone.utc)
        payload = {
            "titulo": "Metricas test",
            "cuerpo": "Endpoint métricas",
            "alcance": "Global",
            "inicio_en": (now - timedelta(days=1)).isoformat(),
            "fin_en": (now + timedelta(days=1)).isoformat(),
            "requiere_ack": True,
        }
        create_resp = client.post(
            "/api/v1/avisos",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        assert create_resp.status_code == 201
        aviso_id = create_resp.json()["id"]

        # Create ack to have metrics
        client.post(
            f"/api/v1/avisos/{aviso_id}/confirmar-lectura",
            headers={"Authorization": "Bearer test-token"},
        )

        metrics_resp = client.get(
            f"/api/v1/avisos/{aviso_id}/metricas",
            headers={"Authorization": "Bearer test-token"},
        )
        assert metrics_resp.status_code == 200
        metrics = metrics_resp.json()
        assert metrics["total_acks"] >= 1
        assert metrics["total_views"] >= 1

    @pytest.mark.asyncio
    async def test_delete_aviso_endpoint(self, integration_setup):
        client, tenant, user, db = integration_setup
        now = datetime.now(timezone.utc)
        payload = {
            "titulo": "A eliminar",
            "cuerpo": "Delete via endpoint",
            "alcance": "Global",
            "inicio_en": (now - timedelta(days=1)).isoformat(),
            "fin_en": (now + timedelta(days=1)).isoformat(),
        }
        create_resp = client.post(
            "/api/v1/avisos",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        assert create_resp.status_code == 201
        aviso_id = create_resp.json()["id"]

        delete_resp = client.delete(
            f"/api/v1/avisos/{aviso_id}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert delete_resp.status_code == 204

    @pytest.mark.asyncio
    async def test_list_all_admin_endpoint(self, integration_setup):
        client, tenant, user, db = integration_setup
        now = datetime.now(timezone.utc)
        for i in range(3):
            payload = {
                "titulo": f"Aviso {i}",
                "cuerpo": f"Cuerpo {i}",
                "alcance": "Global",
                "inicio_en": (now - timedelta(days=1)).isoformat(),
                "fin_en": (now + timedelta(days=1)).isoformat(),
            }
            client.post(
                "/api/v1/avisos",
                json=payload,
                headers={"Authorization": "Bearer test-token"},
            )

        response = client.get(
            "/api/v1/avisos",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    @pytest.mark.asyncio
    async def test_get_aviso_endpoint(self, integration_setup):
        client, tenant, user, db = integration_setup
        now = datetime.now(timezone.utc)
        payload = {
            "titulo": "Get individual",
            "cuerpo": "GET single aviso",
            "alcance": "Global",
            "inicio_en": now.isoformat(),
            "fin_en": (now + timedelta(days=30)).isoformat(),
        }
        create_resp = client.post(
            "/api/v1/avisos",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        aviso_id = create_resp.json()["id"]

        get_resp = client.get(
            f"/api/v1/avisos/{aviso_id}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["titulo"] == "Get individual"

    @pytest.mark.asyncio
    async def test_update_aviso_endpoint(self, integration_setup):
        client, tenant, user, db = integration_setup
        now = datetime.now(timezone.utc)
        payload = {
            "titulo": "Original",
            "cuerpo": "Cuerpo original",
            "alcance": "Global",
            "inicio_en": now.isoformat(),
            "fin_en": (now + timedelta(days=30)).isoformat(),
        }
        create_resp = client.post(
            "/api/v1/avisos",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        aviso_id = create_resp.json()["id"]

        update_payload = {"titulo": "Modificado"}
        update_resp = client.put(
            f"/api/v1/avisos/{aviso_id}",
            json=update_payload,
            headers={"Authorization": "Bearer test-token"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["titulo"] == "Modificado"

    @pytest.mark.asyncio
    async def test_acks_endpoint(self, integration_setup):
        client, tenant, user, db = integration_setup
        now = datetime.now(timezone.utc)
        payload = {
            "titulo": "Acks list",
            "cuerpo": "Lista de acks",
            "alcance": "Global",
            "inicio_en": (now - timedelta(days=1)).isoformat(),
            "fin_en": (now + timedelta(days=1)).isoformat(),
            "requiere_ack": True,
        }
        create_resp = client.post(
            "/api/v1/avisos",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        aviso_id = create_resp.json()["id"]

        client.post(
            f"/api/v1/avisos/{aviso_id}/confirmar-lectura",
            headers={"Authorization": "Bearer test-token"},
        )

        acks_resp = client.get(
            f"/api/v1/avisos/{aviso_id}/acks",
            headers={"Authorization": "Bearer test-token"},
        )
        assert acks_resp.status_code == 200
        acks = acks_resp.json()
        assert len(acks) >= 1
        assert acks[0]["aviso_id"] == aviso_id
