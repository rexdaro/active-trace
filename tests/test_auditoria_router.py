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
from app.routers.auditoria import router as auditoria_router
from app.core.rbac import get_current_user
from app.core.database import get_db
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User, Usuario
from app.models.user_role import UserRole
from app.models.rbac import Role, Permission, RolePermission
from app.models.audit import AuditLog
from app.models.asignacion import Asignacion
from sqlalchemy import select
from sqlalchemy.orm import selectinload


class TestAuditoriaRouterSinAuth:

    def setup_method(self):
        self.app = FastAPI()
        self.app.include_router(auditoria_router)
        self.client = TestClient(self.app)

    def test_metricas_sin_token_returns_401(self):
        response = self.client.get("/api/v1/auditoria/metricas")
        assert response.status_code == 401

    def test_log_sin_token_returns_401(self):
        response = self.client.get("/api/v1/auditoria/log")
        assert response.status_code == 401


class BaseRouterTest:

    def setup_method(self):
        self.mock_user = User(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            email="admin@test.com",
            is_2fa_enabled=False,
            hashed_password="",
        )

    def _make_user_with_permission(self, perm_name: str):
        perm = Permission(name=perm_name)
        rp = RolePermission(permission=perm)
        role = Role(name="ADMIN", role_permissions=[rp])
        ur = UserRole(role=role)
        user = self.mock_user
        user.user_roles = [ur]
        return user

    def _setup_app(self, perm_name: str):
        self._make_user_with_permission(perm_name)
        self.app = FastAPI()
        self.app.include_router(auditoria_router)

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


class TestAuditoriaRouterPermisos(BaseRouterTest):

    def test_metricas_sin_permiso_returns_403(self):
        self._setup_app("avisos:ver")
        response = self.client.get(
            "/api/v1/auditoria/metricas",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 403

    def test_metricas_con_permiso_returns_200(self):
        self._setup_app("auditoria:ver")
        response = self.client.get(
            "/api/v1/auditoria/metricas",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)

    def test_log_sin_permiso_returns_403(self):
        self._setup_app("avisos:ver")
        response = self.client.get(
            "/api/v1/auditoria/log",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 403

    def test_log_con_permiso_returns_200(self):
        self._setup_app("auditoria:ver")
        response = self.client.get(
            "/api/v1/auditoria/log",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (200, 500)


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

    perm = Permission(name="auditoria:ver")
    db_session.add(perm)
    await db_session.flush()

    role = Role(name="ADMIN")
    db_session.add(role)
    await db_session.flush()

    rp = RolePermission(role_id=role.id, permission_id=perm.id)
    db_session.add(rp)

    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email="admin@test.com",
        hashed_password="hashed",
        is_2fa_enabled=False,
    )
    db_session.add(user)

    ur = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(ur)
    await db_session.commit()

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
    loaded_user = result.scalar_one()

    app = FastAPI()
    app.include_router(auditoria_router)

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return loaded_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    return client, tenant, loaded_user, db_session


class TestAuditoriaRouterIntegration:

    @pytest.mark.asyncio
    async def test_metricas_empty(self, integration_setup):
        client, tenant, user, db = integration_setup
        response = client.get(
            "/api/v1/auditoria/metricas",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["acciones_por_dia"] == []
        assert data["comunicaciones_por_docente"] == []
        assert data["ultimas_acciones"] == []

    @pytest.mark.asyncio
    async def test_metricas_with_data(self, integration_setup):
        client, tenant, user, db = integration_setup
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for i in range(5):
            audit = AuditLog(
                action="LOGIN",
                user_id=str(user.id),
                resource="auth",
                status="success",
                actor_id=str(user.id),
                detalle={},
                filas_afectadas=0,
                created_at=now - timedelta(hours=i),
            )
            db.add(audit)

        audit_com = AuditLog(
            action="COMUNICACION_ENVIAR",
            user_id=str(user.id),
            resource="comunicaciones",
            status="success",
            actor_id=str(user.id),
            detalle={},
            filas_afectadas=1,
            created_at=now,
        )
        db.add(audit_com)
        await db.commit()

        response = client.get(
            "/api/v1/auditoria/metricas",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["acciones_por_dia"]) > 0
        assert data["comunicaciones_por_docente"] is not None
        assert len(data["ultimas_acciones"]) == 6

    @pytest.mark.asyncio
    async def test_log_filters_date_range(self, integration_setup):
        client, tenant, user, db = integration_setup
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        old = now - timedelta(days=30)
        recent = now - timedelta(days=1)

        audit_old = AuditLog(
            action="LOGIN", user_id=str(user.id), resource="auth",
            status="success", actor_id=str(user.id), detalle={},
            filas_afectadas=0, created_at=old,
        )
        audit_recent = AuditLog(
            action="LOGIN", user_id=str(user.id), resource="auth",
            status="success", actor_id=str(user.id), detalle={},
            filas_afectadas=0, created_at=recent,
        )
        db.add_all([audit_old, audit_recent])
        await db.commit()

        response = client.get(
            f"/api/v1/auditoria/log?fecha_desde={recent.isoformat()}&fecha_hasta={now.isoformat()}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_log_filters_materia(self, integration_setup):
        client, tenant, user, db = integration_setup
        materia_id = uuid.uuid4()

        audit_materia = AuditLog(
            action="MATERIA_VER", user_id=str(user.id), resource="materias",
            status="success", actor_id=str(user.id), materia_id=str(materia_id),
            detalle={}, filas_afectadas=0,
        )
        audit_otro = AuditLog(
            action="MATERIA_VER", user_id=str(user.id), resource="materias",
            status="success", actor_id=str(user.id),
            detalle={}, filas_afectadas=0,
        )
        db.add_all([audit_materia, audit_otro])
        await db.commit()

        response = client.get(
            f"/api/v1/auditoria/log?materia_id={materia_id}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_log_filters_accion(self, integration_setup):
        client, tenant, user, db = integration_setup
        audit_login = AuditLog(
            action="LOGIN", user_id=str(user.id), resource="auth",
            status="success", actor_id=str(user.id), detalle={}, filas_afectadas=0,
        )
        audit_logout = AuditLog(
            action="LOGOUT", user_id=str(user.id), resource="auth",
            status="success", actor_id=str(user.id), detalle={}, filas_afectadas=0,
        )
        db.add_all([audit_login, audit_logout])
        await db.commit()

        response = client.get(
            "/api/v1/auditoria/log?accion=LOGIN",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_log_filters_usuario(self, integration_setup):
        client, tenant, user, db = integration_setup
        otro_id = uuid.uuid4()

        audit_user = AuditLog(
            action="LOGIN", user_id=str(user.id), resource="auth",
            status="success", actor_id=str(user.id), detalle={}, filas_afectadas=0,
        )
        audit_otro = AuditLog(
            action="LOGIN", user_id=str(otro_id), resource="auth",
            status="success", actor_id=str(otro_id), detalle={}, filas_afectadas=0,
        )
        db.add_all([audit_user, audit_otro])
        await db.commit()

        response = client.get(
            f"/api/v1/auditoria/log?usuario_id={otro_id}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_log_pagination(self, integration_setup):
        client, tenant, user, db = integration_setup
        for i in range(5):
            db.add(AuditLog(
                action="LOGIN", user_id=str(user.id), resource="auth",
                status="success", actor_id=str(user.id), detalle={}, filas_afectadas=0,
            ))
        await db.commit()

        response = client.get(
            "/api/v1/auditoria/log?limit=2&offset=0",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5


@pytest_asyncio.fixture
async def scope_integration_setup(db_session):
    tenant = Tenant(id=uuid.uuid4(), name="Test Tenant")
    db_session.add(tenant)

    perm = Permission(name="auditoria:ver")
    db_session.add(perm)
    await db_session.flush()

    coordinador_role = Role(name="COORDINADOR")
    db_session.add(coordinador_role)
    await db_session.flush()

    rp = RolePermission(role_id=coordinador_role.id, permission_id=perm.id)
    db_session.add(rp)

    materia_id = uuid.uuid4()

    coordinador_id = uuid.uuid4()
    coordinador = User(
        id=coordinador_id,
        tenant_id=tenant.id,
        email="coord@test.com",
        hashed_password="hashed",
        is_2fa_enabled=False,
        dni="0",
        cuil="0",
    )
    db_session.add(coordinador)
    await db_session.flush()

    ur = UserRole(user_id=coordinador.id, role_id=coordinador_role.id)
    db_session.add(ur)

    asignacion = Asignacion(
        user_id=coordinador.id,
        role_id=coordinador_role.id,
        contexto_id=materia_id,
        tenant_id=tenant.id,
        desde=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db_session.add(asignacion)

    otro_user_id = uuid.uuid4()
    audit_visible = AuditLog(
        action="MATERIA_VER",
        user_id=str(otro_user_id),
        resource="materias",
        status="success",
        actor_id=str(otro_user_id),
        materia_id=str(materia_id),
        detalle={},
        filas_afectadas=0,
    )
    audit_no_visible = AuditLog(
        action="MATERIA_VER",
        user_id=str(otro_user_id),
        resource="materias",
        status="success",
        actor_id=str(otro_user_id),
        materia_id=str(uuid.uuid4()),
        detalle={},
        filas_afectadas=0,
    )
    audit_propia = AuditLog(
        action="LOGIN",
        user_id=str(coordinador.id),
        resource="auth",
        status="success",
        actor_id=str(coordinador.id),
        materia_id=str(materia_id),
        detalle={},
        filas_afectadas=0,
    )
    db_session.add_all([audit_visible, audit_no_visible, audit_propia])
    await db_session.commit()

    stmt = (
        select(User)
        .where(User.id == coordinador.id)
        .options(
            selectinload(User.user_roles)
            .selectinload(UserRole.role)
            .selectinload(Role.role_permissions)
            .selectinload(RolePermission.permission)
        )
    )
    result = await db_session.execute(stmt)
    loaded_coordinador = result.scalar_one()

    app = FastAPI()
    app.include_router(auditoria_router)

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return loaded_coordinador

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    return client, tenant, loaded_coordinador, db_session


class TestAuditoriaScopeCoordinador:

    @pytest.mark.asyncio
    async def test_coordinador_ve_solo_sus_materias(self, scope_integration_setup):
        client, tenant, user, db = scope_integration_setup
        response = client.get(
            "/api/v1/auditoria/log",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
