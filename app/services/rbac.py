from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.rbac import Role, Permission, RolePermission
from app.models.user_role import UserRole

async def check_permission(db: AsyncSession, user_id: str, tenant_id: int, permission_name: str) -> bool:
    # Query to check if the user has the permission
    stmt = (
        select(Permission)
        .join(RolePermission, Permission.id == RolePermission.permission_id)
        .join(Role, RolePermission.role_id == Role.id)
        .join(UserRole, Role.id == UserRole.role_id)
        .where(UserRole.user_id == user_id)
        .where(Permission.name == permission_name)
    )
    result = await db.execute(stmt)
    return result.scalar() is not None
