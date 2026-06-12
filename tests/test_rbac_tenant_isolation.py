import pytest
from sqlalchemy import select, event
from sqlalchemy.engine import Engine
from app.models.rbac import Role, Permission, RolePermission
from app.models.user import User
from app.models.tenant import Tenant
from app.models.user_role import UserRole
from app.core.database import AsyncSessionLocal, engine
from app.services.rbac import check_permission

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Add a function to handle 'now()' for sqlite
@event.listens_for(Engine, "connect")
def add_sqlite_now_function(dbapi_connection, connection_record):
    import sqlite3
    from datetime import datetime
    dbapi_connection.create_function("now", 0, lambda: datetime.now())


@pytest.mark.asyncio
async def test_rbac_tenant_isolation():
    async with AsyncSessionLocal() as db:
        # Setup two tenants
        tenant1 = Tenant(name="Tenant 1")
        tenant2 = Tenant(name="Tenant 2")
        db.add(tenant1)
        db.add(tenant2)
        await db.commit()
        await db.refresh(tenant1)
        await db.refresh(tenant2)
        
        # Setup role and permission in tenant 1
        role1 = Role(name="PROFESOR_T1")
        permission1 = Permission(name="calificaciones:importar")
        db.add(role1)
        db.add(permission1)
        await db.commit()
        
        rp1 = RolePermission(role_id=role1.id, permission_id=permission1.id)
        db.add(rp1)
        
        # Setup user in tenant 1
        user1 = User(email="t1@example.com", hashed_password="pw", tenant_id=tenant1.id)
        db.add(user1)
        await db.commit()
        
        user_role1 = UserRole(user_id=user1.id, role_id=role1.id)
        db.add(user_role1)
        await db.commit()
        
        # This should be true
        assert await check_permission(db, user1.id, tenant1.id, "calificaciones:importar") == True
        
        # This should be false (user belongs to tenant 1, cannot access tenant 2)
        # Note: The requirement is that permissions are restricted by tenant.
        # If I pass tenant2.id to check_permission, it should return False
        assert await check_permission(db, user1.id, tenant2.id, "calificaciones:importar") == False
