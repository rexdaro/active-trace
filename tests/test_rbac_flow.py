import pytest
import uuid
from app.models.rbac import Role, Permission, RolePermission
from app.models.user import User
from app.models.tenant import Tenant
from app.models.user_role import UserRole
from app.core.database import AsyncSessionLocal
from app.services.rbac import check_permission

@pytest.mark.asyncio
async def test_rbac_resolution_logic():
    async with AsyncSessionLocal() as db:
        # Setup
        tenant = Tenant(name="Test Tenant")
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
        
        role = Role(name="PROFESOR")
        permission = Permission(name="calificaciones:importar")
        db.add(role)
        db.add(permission)
        await db.commit()
        await db.refresh(role)
        await db.refresh(permission)
        
        rp = RolePermission(role_id=role.id, permission_id=permission.id)
        db.add(rp)
        
        user = User(email="test@example.com", hashed_password="pw", tenant_id=tenant.id)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        user_role = UserRole(user_id=user.id, role_id=role.id)
        db.add(user_role)
        await db.commit()
        
        # Check permissions
        assert await check_permission(db, user.id, tenant.id, "calificaciones:importar") == True
        assert await check_permission(db, user.id, tenant.id, "auditoria:ver") == False
