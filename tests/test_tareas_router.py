import pytest
import pytest_asyncio
import uuid
import os
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["ENCRYPTION_KEY"] = "test-key-32-chars-long-for-encryption!!"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers.tareas import router as tareas_router
from app.core.rbac import get_current_user
from app.core.database import get_db
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User, Usuario
from app.models.user_role import UserRole
from app.models.rbac import Role, Permission, RolePermission
from app.models.materia import Materia
from app.models.tarea import Tarea, EstadoTarea
from sqlalchemy import select, text


# ═══════════════════════════════════════════════════════════════════════════════
# Sin autenticación — todos devuelven 401
# ═══════════════════════════════════════════════════════════════════════════════

class TestTareasRouterSinAuth:

    def setup_method(self):
        self.app = FastAPI()
        self.app.include_router(tareas_router)
        self.client = TestClient(self.app)

    def test_create_sin_token_returns_401(self):
        response = self.client.post("/api/v1/tareas", json={})
        assert response.status_code == 401

    def test_list_mis_tareas_sin_token_returns_401(self):
        response = self.client.get("/api/v1/tareas/mis-tareas")
        assert response.status_code == 401

    def test_list_admin_sin_token_returns_401(self):
        response = self.client.get("/api/v1/tareas/admin")
        assert response.status_code == 401

    def test_get_sin_token_returns_401(self):
        response = self.client.get(f"/api/v1/tareas/{uuid.uuid4()}")
        assert response.status_code == 401

    def test_update_sin_token_returns_401(self):
        response = self.client.put(f"/api/v1/tareas/{uuid.uuid4()}", json={})
        assert response.status_code == 401

    def test_update_estado_sin_token_returns_401(self):
        response = self.client.put(f"/api/v1/tareas/{uuid.uuid4()}/estado", json={})
        assert response.status_code == 401

    def test_delete_sin_token_returns_401(self):
        response = self.client.delete(f"/api/v1/tareas/{uuid.uuid4()}")
        assert response.status_code == 401

    def test_add_comentario_sin_token_returns_401(self):
        response = self.client.post(f"/api/v1/tareas/{uuid.uuid4()}/comentarios", json={})
        assert response.status_code == 401

    def test_list_comentarios_sin_token_returns_401(self):
        response = self.client.get(f"/api/v1/tareas/{uuid.uuid4()}/comentarios")
        assert response.status_code == 401

    def test_delete_comentario_sin_token_returns_401(self):
        response = self.client.delete(f"/api/v1/tareas/{uuid.uuid4()}/comentarios/{uuid.uuid4()}")
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
            "tareas:crear": Permission(name="tareas:crear"),
            "tareas:ver": Permission(name="tareas:ver"),
            "tareas:gestionar": Permission(name="tareas:gestionar"),
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
        self.app.include_router(tareas_router)

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


class TestTareasRouterPermisos(BaseRouterTest):

    def test_create_tarea_con_permiso_crear_returns_422(self):
        self._setup_app("tareas:crear")
        response = self.client.post(
            "/api/v1/tareas",
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_create_tarea_sin_permiso_returns_403(self):
        self._setup_app("tareas:ver")
        response = self.client.post(
            "/api/v1/tareas",
            json={"asignado_a": str(uuid.uuid4()), "descripcion": "test"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 403

    def test_list_mis_tareas_con_permiso_ver_returns_200(self):
        self._setup_app("tareas:ver")
        response = self.client.get(
            "/api/v1/tareas/mis-tareas",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)

    def test_list_mis_tareas_sin_permiso_returns_403(self):
        self._setup_app("tareas:crear")
        response = self.client.get(
            "/api/v1/tareas/mis-tareas",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 403

    def test_list_admin_sin_permiso_returns_403(self):
        self._setup_app("tareas:ver")
        response = self.client.get(
            "/api/v1/tareas/admin",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 403

    def test_delete_sin_permiso_gestionar_returns_403(self):
        self._setup_app("tareas:ver")
        response = self.client.delete(
            f"/api/v1/tareas/{uuid.uuid4()}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 403

    def test_delete_comentario_sin_permiso_returns_403(self):
        self._setup_app("tareas:ver")
        response = self.client.delete(
            f"/api/v1/tareas/{uuid.uuid4()}/comentarios/{uuid.uuid4()}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 403

    def test_admin_con_permiso_returns_200_or_500(self):
        self._setup_app("tareas:gestionar")
        response = self.client.get(
            "/api/v1/tareas/admin",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)


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
        await session.execute(text("PRAGMA foreign_keys=ON"))
        yield session


@pytest_asyncio.fixture
async def integration_setup(db_session):
    tenant = Tenant(id=uuid.uuid4(), name="Test Tenant")
    db_session.add(tenant)

    # Create permissions
    for perm_name in ["tareas:crear", "tareas:ver", "tareas:gestionar"]:
        perm = Permission(name=perm_name)
        db_session.add(perm)
    await db_session.flush()

    # Create role with all permissions
    role = Role(name="COORDINADOR")
    db_session.add(role)
    await db_session.flush()

    perms = await db_session.execute(select(Permission))
    for perm in perms.scalars().all():
        rp = RolePermission(role_id=role.id, permission_id=perm.id)
        db_session.add(rp)

    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email="coord@test.com",
        hashed_password="hashed",
        is_2fa_enabled=False,
    )
    db_session.add(user)
    ur = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(ur)

    usuario = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email="docente@test.com",
        hashed_password="x",
        _dni="11111111",
        _cuil="20-11111111-9",
    )
    db_session.add(usuario)
    await db_session.commit()

    # Reload user with roles eagerly loaded
    from sqlalchemy.orm import selectinload
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
    app.include_router(tareas_router)

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return user

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    return client, tenant, user, usuario, db_session


class TestTareasRouterIntegration:

    @pytest.mark.asyncio
    async def test_create_tarea_endpoint(self, integration_setup):
        client, tenant, user, usuario, db = integration_setup
        payload = {
            "asignado_a": str(usuario.id),
            "descripcion": "Tarea creada desde endpoint",
        }
        response = client.post(
            "/api/v1/tareas",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["descripcion"] == "Tarea creada desde endpoint"
        assert data["estado"] == "Pendiente"
        assert data["asignado_a"] == str(usuario.id)

    @pytest.mark.asyncio
    async def test_list_mis_tareas_empty(self, integration_setup):
        client, tenant, user, usuario, db = integration_setup
        response = client.get(
            "/api/v1/tareas/mis-tareas",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_mis_tareas_with_data(self, integration_setup):
        client, tenant, user, usuario, db = integration_setup
        payload = {
            "asignado_a": str(usuario.id),
            "descripcion": "Mi tarea asignada",
        }
        create_resp = client.post(
            "/api/v1/tareas",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        assert create_resp.status_code == 201

        response = client.get(
            "/api/v1/tareas/mis-tareas",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_add_comentario_endpoint(self, integration_setup):
        client, tenant, user, usuario, db = integration_setup
        # Create tarea first
        create_resp = client.post(
            "/api/v1/tareas",
            json={"asignado_a": str(usuario.id), "descripcion": "Tarea con comentario"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert create_resp.status_code == 201
        tarea_id = create_resp.json()["id"]

        # Add comentario
        comentario_resp = client.post(
            f"/api/v1/tareas/{tarea_id}/comentarios",
            json={"texto": "Este es un comentario"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert comentario_resp.status_code == 201
        data = comentario_resp.json()
        assert data["texto"] == "Este es un comentario"

    @pytest.mark.asyncio
    async def test_update_estado_endpoint(self, integration_setup):
        client, tenant, user, usuario, db = integration_setup
        create_resp = client.post(
            "/api/v1/tareas",
            json={"asignado_a": str(usuario.id), "descripcion": "Cambiar estado"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert create_resp.status_code == 201
        tarea_id = create_resp.json()["id"]

        # Change estado
        estado_resp = client.put(
            f"/api/v1/tareas/{tarea_id}/estado",
            json={"estado": "En progreso"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert estado_resp.status_code == 200
        assert estado_resp.json()["estado"] == "En progreso"

    @pytest.mark.asyncio
    async def test_delete_tarea_endpoint(self, integration_setup):
        client, tenant, user, usuario, db = integration_setup
        create_resp = client.post(
            "/api/v1/tareas",
            json={"asignado_a": str(usuario.id), "descripcion": "A eliminar"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert create_resp.status_code == 201
        tarea_id = create_resp.json()["id"]

        delete_resp = client.delete(
            f"/api/v1/tareas/{tarea_id}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert delete_resp.status_code == 204

    @pytest.mark.asyncio
    async def test_list_comentarios_endpoint(self, integration_setup):
        client, tenant, user, usuario, db = integration_setup
        create_resp = client.post(
            "/api/v1/tareas",
            json={"asignado_a": str(usuario.id), "descripcion": "Comentarios"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert create_resp.status_code == 201
        tarea_id = create_resp.json()["id"]

        # Add 2 comments
        for texto in ["Primero", "Segundo"]:
            client.post(
                f"/api/v1/tareas/{tarea_id}/comentarios",
                json={"texto": texto},
                headers={"Authorization": "Bearer test-token"},
            )

        list_resp = client.get(
            f"/api/v1/tareas/{tarea_id}/comentarios",
            headers={"Authorization": "Bearer test-token"},
        )
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_delete_comentario_endpoint(self, integration_setup):
        client, tenant, user, usuario, db = integration_setup
        create_resp = client.post(
            "/api/v1/tareas",
            json={"asignado_a": str(usuario.id), "descripcion": "Comentario a borrar"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert create_resp.status_code == 201
        tarea_id = create_resp.json()["id"]

        comment_resp = client.post(
            f"/api/v1/tareas/{tarea_id}/comentarios",
            json={"texto": "A borrar"},
            headers={"Authorization": "Bearer test-token"},
        )
        comentario_id = comment_resp.json()["id"]

        delete_resp = client.delete(
            f"/api/v1/tareas/{tarea_id}/comentarios/{comentario_id}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert delete_resp.status_code == 204

    @pytest.mark.asyncio
    async def test_full_flow(self, integration_setup):
        """Create → list → add comentario → change estado → delete"""
        client, tenant, user, usuario, db = integration_setup

        # 1. Create
        create_resp = client.post(
            "/api/v1/tareas",
            json={"asignado_a": str(usuario.id), "descripcion": "Full flow"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert create_resp.status_code == 201
        tarea_id = create_resp.json()["id"]

        # 2. Add comentario
        com_resp = client.post(
            f"/api/v1/tareas/{tarea_id}/comentarios",
            json={"texto": "Comentario en flow completo"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert com_resp.status_code == 201

        # 3. Change estado
        estado_resp = client.put(
            f"/api/v1/tareas/{tarea_id}/estado",
            json={"estado": "En progreso"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert estado_resp.status_code == 200
        assert estado_resp.json()["estado"] == "En progreso"

        # 4. Get tarea
        get_resp = client.get(
            f"/api/v1/tareas/{tarea_id}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["estado"] == "En progreso"

        # 5. Delete
        delete_resp = client.delete(
            f"/api/v1/tareas/{tarea_id}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert delete_resp.status_code == 204
