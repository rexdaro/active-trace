import pytest
import pytest_asyncio
import uuid
import os

os.environ["ENCRYPTION_KEY"] = "test-key-32-chars-long-for-encryption!!"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.core.database import get_db
from app.core.rbac import get_current_user
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User as UserModel
from app.models.rbac import Role
from app.models.user_role import UserRole
from app.routers.auth import router as auth_router
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


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
    await db_session.commit()

    app = FastAPI()
    app.include_router(auth_router, prefix="/api/auth")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return app, db_session, tenant


class TestRegisterEndpoint:

    @pytest.mark.asyncio
    async def test_register_success_assigns_alumno_role(self, app_with_db):
        app, db, tenant = app_with_db
        role = Role(id=1, name="ALUMNO")
        db.add(role)
        await db.commit()

        client = TestClient(app)
        response = client.post("/api/auth/register", json={
            "email": "nuevo@test.com",
            "password": "SecurePass123!",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "nuevo@test.com"
        assert data["mensaje"] == "Usuario registrado exitosamente"

        from sqlalchemy import select
        result = await db.execute(
            select(UserRole).join(UserModel, UserRole.user_id == UserModel.id)
            .where(UserModel.email == "nuevo@test.com")
        )
        user_role = result.scalar_one_or_none()
        assert user_role is not None
        assert user_role.role_id == role.id

    @pytest.mark.asyncio
    async def test_register_duplicate_email_returns_409(self, app_with_db):
        app, db, tenant = app_with_db
        from app.models.user import User
        user = User(id=uuid.uuid4(), tenant_id=tenant.id, email="existente@test.com", hashed_password="x")
        db.add(user)
        await db.commit()

        client = TestClient(app)
        response = client.post("/api/auth/register", json={
            "email": "existente@test.com",
            "password": "SecurePass123!",
        })
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_register_without_role_still_works(self, app_with_db):
        app, db, tenant = app_with_db
        client = TestClient(app)
        response = client.post("/api/auth/register", json={
            "email": "sinrol@test.com",
            "password": "SecurePass123!",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "sinrol@test.com"
