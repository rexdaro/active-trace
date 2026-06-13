import pytest
import pytest_asyncio
import uuid
import os
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

os.environ["ENCRYPTION_KEY"] = "test-key-32-chars-long-for-encryption!!"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers.programas import router as programas_router
from app.core.rbac import get_current_user
from app.core.database import get_db
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User
from app.models.user_role import UserRole
from app.models.rbac import Role, Permission, RolePermission
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.programa_materia import ProgramaMateria
from sqlalchemy import select
from sqlalchemy.orm import selectinload


class TestProgramasRouterSinAuth:

    def setup_method(self):
        self.app = FastAPI()
        self.app.include_router(programas_router)
        self.client = TestClient(self.app)

    def test_create_sin_token_returns_401(self):
        response = self.client.post("/api/v1/programas", json={})
        assert response.status_code == 401

    def test_list_sin_token_returns_401(self):
        response = self.client.get("/api/v1/programas")
        assert response.status_code == 401

    def test_get_sin_token_returns_401(self):
        response = self.client.get(f"/api/v1/programas/{uuid.uuid4()}")
        assert response.status_code == 401

    def test_update_sin_token_returns_401(self):
        response = self.client.put(f"/api/v1/programas/{uuid.uuid4()}", json={})
        assert response.status_code == 401

    def test_delete_sin_token_returns_401(self):
        response = self.client.delete(f"/api/v1/programas/{uuid.uuid4()}")
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
            "estructura:gestionar": Permission(name="estructura:gestionar"),
        }

    def _make_user_with_permission(self, perm_name: str):
        if perm_name not in self.permissions_map:
            perm = Permission(name="otro:permiso")
        else:
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
        self.app.include_router(programas_router)

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


class TestProgramasRouterPermisos(BaseRouterTest):

    def test_create_con_permiso_returns_422(self):
        self._setup_app("estructura:gestionar")
        response = self.client.post(
            "/api/v1/programas",
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_create_sin_permiso_returns_403(self):
        self._setup_app("otro:permiso")
        response = self.client.post(
            "/api/v1/programas",
            json={"materia_id": str(uuid.uuid4()), "carrera_id": str(uuid.uuid4()), "cohorte_id": str(uuid.uuid4()), "titulo": "test"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 403

    def test_list_sin_permiso_returns_403(self):
        self._setup_app("otro:permiso")
        response = self.client.get(
            "/api/v1/programas",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 403

    def test_get_sin_permiso_returns_403(self):
        self._setup_app("otro:permiso")
        response = self.client.get(
            f"/api/v1/programas/{uuid.uuid4()}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 403

    def test_update_sin_permiso_returns_403(self):
        self._setup_app("otro:permiso")
        response = self.client.put(
            f"/api/v1/programas/{uuid.uuid4()}",
            json={"titulo": "test"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 403

    def test_delete_sin_permiso_returns_403(self):
        self._setup_app("otro:permiso")
        response = self.client.delete(
            f"/api/v1/programas/{uuid.uuid4()}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 403


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

    perm = Permission(name="estructura:gestionar")
    db_session.add(perm)
    await db_session.flush()

    role = Role(name="COORDINADOR")
    db_session.add(role)
    await db_session.flush()

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

    materia = Materia(id=uuid.uuid4(), tenant_id=tenant.id, name="Matemática", code="MAT101")
    db_session.add(materia)
    carrera = Carrera(id=uuid.uuid4(), tenant_id=tenant.id, name="Ing. Sistemas", code="IS")
    db_session.add(carrera)
    cohorte = Cohorte(id=uuid.uuid4(), tenant_id=tenant.id, carrera_id=carrera.id, name="2026")
    db_session.add(cohorte)
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
    user = result.scalar_one()

    app = FastAPI()
    app.include_router(programas_router)

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return user

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    return client, tenant, user, db_session, materia, carrera, cohorte


class TestProgramasRouterIntegration:

    @pytest.mark.asyncio
    async def test_create_programa_endpoint(self, integration_setup):
        client, tenant, user, db, materia, carrera, cohorte = integration_setup
        payload = {
            "materia_id": str(materia.id),
            "carrera_id": str(carrera.id),
            "cohorte_id": str(cohorte.id),
            "titulo": "Programa 2026",
        }
        response = client.post(
            "/api/v1/programas",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["titulo"] == "Programa 2026"
        assert data["materia_id"] == str(materia.id)
        assert data["carrera_id"] == str(carrera.id)
        assert data["cohorte_id"] == str(cohorte.id)

    @pytest.mark.asyncio
    async def test_list_programas_endpoint(self, integration_setup):
        client, tenant, user, db, materia, carrera, cohorte = integration_setup

        response = client.get(
            "/api/v1/programas",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_programa_endpoint(self, integration_setup):
        client, tenant, user, db, materia, carrera, cohorte = integration_setup
        payload = {
            "materia_id": str(materia.id),
            "carrera_id": str(carrera.id),
            "cohorte_id": str(cohorte.id),
            "titulo": "Get test",
        }
        create_resp = client.post(
            "/api/v1/programas",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        programa_id = create_resp.json()["id"]

        get_resp = client.get(
            f"/api/v1/programas/{programa_id}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["titulo"] == "Get test"

    @pytest.mark.asyncio
    async def test_update_programa_endpoint(self, integration_setup):
        client, tenant, user, db, materia, carrera, cohorte = integration_setup
        payload = {
            "materia_id": str(materia.id),
            "carrera_id": str(carrera.id),
            "cohorte_id": str(cohorte.id),
            "titulo": "Original",
        }
        create_resp = client.post(
            "/api/v1/programas",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        programa_id = create_resp.json()["id"]

        update_payload = {"titulo": "Modificado"}
        update_resp = client.put(
            f"/api/v1/programas/{programa_id}",
            json=update_payload,
            headers={"Authorization": "Bearer test-token"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["titulo"] == "Modificado"

    @pytest.mark.asyncio
    async def test_delete_programa_endpoint(self, integration_setup):
        client, tenant, user, db, materia, carrera, cohorte = integration_setup
        payload = {
            "materia_id": str(materia.id),
            "carrera_id": str(carrera.id),
            "cohorte_id": str(cohorte.id),
            "titulo": "A eliminar",
        }
        create_resp = client.post(
            "/api/v1/programas",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        programa_id = create_resp.json()["id"]

        delete_resp = client.delete(
            f"/api/v1/programas/{programa_id}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert delete_resp.status_code == 204
