import asyncio
from sqlalchemy.future import select
from app.core.database import AsyncSessionLocal
from app.models.rbac import Role

ROLES = ["ALUMNO", "TUTOR", "PROFESOR", "COORDINADOR", "NEXO", "ADMIN", "FINANZAS"]

async def seed():
    async with AsyncSessionLocal() as session:
        for role_name in ROLES:
            # Check if role exists
            result = await session.execute(select(Role).filter(Role.name == role_name))
            role = result.scalar_one_or_none()
            if not role:
                print(f"Adding role: {role_name}")
                session.add(Role(name=role_name))
            else:
                print(f"Role {role_name} already exists.")
        await session.commit()

if __name__ == "__main__":
    asyncio.run(seed())
