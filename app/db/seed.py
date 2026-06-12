import asyncio
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.rbac import Role, Permission, RolePermission

ROLES = ["ALUMNO", "TUTOR", "PROFESOR", "COORDINADOR", "NEXO", "ADMIN", "FINANZAS"]

PERMISSIONS = {
    "atrasados:ver": ["PROFESOR", "TUTOR", "COORDINADOR", "ADMIN"],
    "atrasados:export": ["PROFESOR", "COORDINADOR", "ADMIN"],
    "comunicacion:enviar": ["PROFESOR", "COORDINADOR", "ADMIN"],
    "comunicacion:aprobar": ["COORDINADOR", "ADMIN"],
    "encuentros:gestionar": ["PROFESOR", "COORDINADOR", "ADMIN"],
    "encuentros:ver": ["COORDINADOR", "ADMIN"],
    "guardias:registrar": ["TUTOR", "COORDINADOR", "ADMIN"],
    "guardias:ver": ["COORDINADOR", "ADMIN"],
    "coloquios:gestionar": ["COORDINADOR", "ADMIN"],
    "coloquios:reservar": ["ALUMNO"],
    "coloquios:ver": ["COORDINADOR", "ADMIN", "PROFESOR"],
}


async def _ensure_permissions(session: AsyncSession):
    for perm_name, roles in PERMISSIONS.items():
        result = await session.execute(select(Permission).filter(Permission.name == perm_name))
        perm = result.scalar_one_or_none()
        if not perm:
            print(f"Adding permission: {perm_name}")
            perm = Permission(name=perm_name)
            session.add(perm)
            await session.flush()
        else:
            print(f"Permission {perm_name} already exists.")
            continue

        for role_name in roles:
            role_result = await session.execute(select(Role).filter(Role.name == role_name))
            role = role_result.scalar_one_or_none()
            if role:
                rp_result = await session.execute(
                    select(RolePermission).filter(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == perm.id,
                    )
                )
                if not rp_result.scalar_one_or_none():
                    print(f"  Assigning {perm_name} to {role_name}")
                    session.add(RolePermission(role_id=role.id, permission_id=perm.id))


async def seed():
    async with AsyncSessionLocal() as session:
        for role_name in ROLES:
            result = await session.execute(select(Role).filter(Role.name == role_name))
            role = result.scalar_one_or_none()
            if not role:
                print(f"Adding role: {role_name}")
                session.add(Role(name=role_name))
            else:
                print(f"Role {role_name} already exists.")
        await session.commit()
        await _ensure_permissions(session)
        await session.commit()

if __name__ == "__main__":
    asyncio.run(seed())
