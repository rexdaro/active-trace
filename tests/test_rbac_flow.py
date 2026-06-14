import pytest
import pytest_asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.base import Base
from app.models.rbac import Role, Permission, RolePermission
from app.models.user import User
from app.models.tenant import Tenant
from app.models.user_role import UserRole
from app.services.rbac import check_permission


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.mark.asyncio
async def test_rbac_resolution_logic(db_session):
    tenant = Tenant(name=f"RBAC Flow {uuid.uuid4().hex[:8]}")
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    
    role = Role(name="PROFESOR")
    permission = Permission(name="calificaciones:importar")
    db_session.add(role)
    db_session.add(permission)
    await db_session.commit()
    await db_session.refresh(role)
    await db_session.refresh(permission)
    
    rp = RolePermission(role_id=role.id, permission_id=permission.id)
    db_session.add(rp)
    
    user = User(email="test@example.com", hashed_password="pw", tenant_id=tenant.id)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    user_role = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(user_role)
    await db_session.commit()
    
    assert await check_permission(db_session, user.id, tenant.id, "calificaciones:importar") == True
    assert await check_permission(db_session, user.id, tenant.id, "auditoria:ver") == False
