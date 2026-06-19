import pytest
import pytest_asyncio
import uuid
from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.core.rbac import get_current_user
from app.models.user import User
from app.models.user_role import UserRole
from app.models.rbac import Role, Permission, RolePermission
from app.models.base import Base
from app.core.database import get_db
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


@pytest_asyncio.fixture
async def _app_with_auth():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    perm = Permission(name="estructura:gestionar")
    rp = RolePermission(permission=perm)
    role = Role(name="ADMIN", role_permissions=[rp])
    mock_user = User(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        email="admin@test.com",
        is_2fa_enabled=False,
        hashed_password="",
        user_roles=[UserRole(role=role)],
    )

    async def override_get_current_user():
        return mock_user

    from app.main import app
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.mark.asyncio
async def test_create_carrera_validation(_app_with_auth):
    client = _app_with_auth
    response = client.post("/api/carreras", json={
        "name": "Ingeniería",
        "code": "ING",
    })
    assert response.status_code == 200
