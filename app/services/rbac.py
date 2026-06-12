from sqlalchemy import select
import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.rbac import Role, Permission, RolePermission
from app.models.user_role import UserRole
from app.models.user import User
from fastapi import Depends, HTTPException, status
from app.core.database import get_db

async def check_permission(db: AsyncSession, user_id: str, tenant_id: int, permission_name: str) -> bool:
    # Query to check if the user has the permission restricted by tenant
    stmt = (
        select(Permission)
        .join(RolePermission, Permission.id == RolePermission.permission_id)
        .join(Role, RolePermission.role_id == Role.id)
        .join(UserRole, Role.id == UserRole.role_id)
        .join(User, UserRole.user_id == User.id)
        .where(User.id == user_id)
        .where(User.tenant_id == tenant_id)
        .where(Permission.name == permission_name)
    )
    result = await db.execute(stmt)
    return result.scalar() is not None

async def seed_rbac(db: AsyncSession, config_path: str):
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Seed roles
    for role_data in config["roles"]:
        role = Role(name=role_data["name"], description=role_data.get("description"))
        db.add(role)
    
    # Seed permissions
    for perm_data in config["permissions"]:
        permission = Permission(name=perm_data["name"])
        db.add(permission)
    
    await db.commit()
    
    # Seed role_permissions
    for rp_data in config["role_permissions"]:
        role = (await db.execute(select(Role).where(Role.name == rp_data["role_name"]))).scalar()
        permission = (await db.execute(select(Permission).where(Permission.name == rp_data["permission_name"]))).scalar()
        
        if role and permission:
            rp = RolePermission(role=role, permission=permission)
            db.add(rp)
    
    await db.commit()

