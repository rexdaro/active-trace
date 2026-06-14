import uuid
import pytest
import pytest_asyncio
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
async def test_rbac_tenant_isolation(db_session):
    tenant1 = Tenant(name=f"Tenant 1 {uuid.uuid4().hex[:8]}")
    tenant2 = Tenant(name=f"Tenant 2 {uuid.uuid4().hex[:8]}")
    db_session.add(tenant1)
    db_session.add(tenant2)
    await db_session.commit()
    await db_session.refresh(tenant1)
    await db_session.refresh(tenant2)
    
    role1 = Role(name="PROFESOR_T1")
    permission1 = Permission(name="calificaciones:importar")
    db_session.add(role1)
    db_session.add(permission1)
    await db_session.commit()
    
    rp1 = RolePermission(role_id=role1.id, permission_id=permission1.id)
    db_session.add(rp1)
    
    user1 = User(email="t1@example.com", hashed_password="pw", tenant_id=tenant1.id)
    db_session.add(user1)
    await db_session.commit()
    
    user_role1 = UserRole(user_id=user1.id, role_id=role1.id)
    db_session.add(user_role1)
    await db_session.commit()
    
    assert await check_permission(db_session, user1.id, tenant1.id, "calificaciones:importar") == True
    assert await check_permission(db_session, user1.id, tenant2.id, "calificaciones:importar") == False
