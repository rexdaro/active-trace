import pytest
import pytest_asyncio
import uuid
import os

os.environ["ENCRYPTION_KEY"] = "test-key-32-chars-long-for-encryption!!"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.core.database import get_db
from app.core.rbac import get_current_user, check_permission
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User
from app.models.rbac import Role
from app.models.user_role import UserRole
from app.routers.usuarios import router as usuarios_router
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def app_with_db(db_session):
    tenant = Tenant(id=uuid.uuid4(), name="Test Tenant")
    db_session.add(tenant)
    admin_user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email="admin@test.com",
        hashed_password="hashed",
    )
    db_session.add(admin_user)
    await db_session.commit()

    app = FastAPI()
    app.include_router(usuarios_router)

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return admin_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db
    return app, db_session, tenant, admin_user


class TestCrearUsuarioAdmin:

    @pytest.mark.asyncio
    async def test_admin_creates_user_with_role(self, app_with_db):
        app, db, tenant, admin = app_with_db
        role = Role(id=1, name="PROFESOR")
        db.add(role)
        await db.commit()

        client = TestClient(app)
        response = client.post(
            "/api/v1/usuarios",
            json={
                "email": "nuevo@test.com",
                "password": "Pass123!",
                "role_id": 1,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "nuevo@test.com"

        result = await db.execute(
            select(UserRole).where(UserRole.user_id == uuid.UUID(data["id"]))
        )
        user_role = result.scalar_one_or_none()
        assert user_role is not None
        assert user_role.role_id == 1

    @pytest.mark.asyncio
    async def test_admin_creates_user_without_role_defaults_alumno(self, app_with_db):
        app, db, tenant, admin = app_with_db
        alumno = Role(id=2, name="ALUMNO")
        db.add(alumno)
        await db.commit()

        client = TestClient(app)
        response = client.post(
            "/api/v1/usuarios",
            json={
                "email": "alumno@test.com",
                "password": "Pass123!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "alumno@test.com"

        result = await db.execute(
            select(UserRole).where(UserRole.user_id == uuid.UUID(data["id"]))
        )
        user_role = result.scalar_one_or_none()
        assert user_role is not None
        assert user_role.role_id == 2

    @pytest.mark.asyncio
    async def test_duplicate_email_returns_409(self, app_with_db):
        app, db, tenant, admin = app_with_db
        existing = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email="dup@test.com",
            hashed_password="x",
        )
        db.add(existing)
        await db.commit()

        client = TestClient(app)
        response = client.post(
            "/api/v1/usuarios",
            json={
                "email": "dup@test.com",
                "password": "Pass123!",
            },
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_invalid_role_returns_404(self, app_with_db):
        app, db, tenant, admin = app_with_db
        client = TestClient(app)
        response = client.post(
            "/api/v1/usuarios",
            json={
                "email": "badrole@test.com",
                "password": "Pass123!",
                "role_id": 999,
            },
        )
        assert response.status_code == 404


class TestRoleManagement:

    @pytest.mark.asyncio
    async def test_assign_role(self, app_with_db):
        app, db, tenant, admin = app_with_db
        role = Role(id=1, name="TUTOR")
        db.add(role)
        target = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email="target@test.com",
            hashed_password="x",
        )
        db.add(target)
        await db.commit()

        client = TestClient(app)
        response = client.post(
            f"/api/v1/usuarios/{target.id}/roles",
            json={"rol": "TUTOR"},
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True

    @pytest.mark.asyncio
    async def test_assign_duplicate_role(self, app_with_db):
        app, db, tenant, admin = app_with_db
        role = Role(id=1, name="TUTOR")
        db.add(role)
        target = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email="target@test.com",
            hashed_password="x",
        )
        db.add(target)
        user_role = UserRole(user_id=target.id, role_id=role.id)
        db.add(user_role)
        await db.commit()

        client = TestClient(app)
        response = client.post(
            f"/api/v1/usuarios/{target.id}/roles",
            json={"rol": "TUTOR"},
        )
        assert response.status_code == 200
        assert "ya tiene" in response.json()["mensaje"]

    @pytest.mark.asyncio
    async def test_assign_nonexistent_role(self, app_with_db):
        app, db, tenant, admin = app_with_db
        target = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email="target@test.com",
            hashed_password="x",
        )
        db.add(target)
        await db.commit()

        client = TestClient(app)
        response = client.post(
            f"/api/v1/usuarios/{target.id}/roles",
            json={"rol": "FAKEROLE"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_remove_role(self, app_with_db):
        app, db, tenant, admin = app_with_db
        role = Role(id=1, name="TUTOR")
        db.add(role)
        target = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email="target@test.com",
            hashed_password="x",
        )
        db.add(target)
        user_role = UserRole(user_id=target.id, role_id=role.id)
        db.add(user_role)
        await db.commit()

        client = TestClient(app)
        response = client.delete(
            f"/api/v1/usuarios/{target.id}/roles/{role.id}",
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True

        result = await db.execute(
            select(UserRole).where(
                UserRole.user_id == target.id,
                UserRole.role_id == role.id,
            )
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_remove_nonexistent_role_returns_404(self, app_with_db):
        app, db, tenant, admin = app_with_db
        target = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email="target@test.com",
            hashed_password="x",
        )
        db.add(target)
        await db.commit()

        client = TestClient(app)
        response = client.delete(
            f"/api/v1/usuarios/{target.id}/roles/999",
        )
        assert response.status_code == 404
