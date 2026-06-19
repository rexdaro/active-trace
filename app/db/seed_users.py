import asyncio
import uuid
import bcrypt
from sqlalchemy.future import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.tenant import Tenant
from app.models.user_role import UserRole
from app.models.rbac import Role

async def seed_users():
    async with AsyncSessionLocal() as session:
        # Check if user exists
        result = await session.execute(select(User).where(User.email == "test@example.com"))
        existing_user = result.scalar_one_or_none()
        
        # Get or create default tenant
        tenant_result = await session.execute(select(Tenant).limit(1))
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            tenant = Tenant(id=uuid.uuid4(), name="Default")
            session.add(tenant)
            await session.flush()
            print("Created default tenant")

        if existing_user:
            hashed = bcrypt.hashpw(b"SuperSecret123!", bcrypt.gensalt()).decode()
            existing_user.hashed_password = hashed
            existing_user.tenant_id = tenant.id
            await session.commit()
            print("Updated test user password")
            return

        # Create new user
        hashed = bcrypt.hashpw(b"SuperSecret123!", bcrypt.gensalt()).decode()
        user = User(
            tenant_id=tenant.id,
            email="test@example.com",
            hashed_password=hashed,
        )
        session.add(user)
        await session.flush()
        print(f"Created test user with id={user.id}")

        # Assign roles: PROFESOR, COORDINADOR, ADMIN
        for role_name in ["PROFESOR", "COORDINADOR", "ADMIN"]:
            role_result = await session.execute(select(Role).where(Role.name == role_name))
            role = role_result.scalar_one_or_none()
            if role:
                session.add(UserRole(user_id=user.id, role_id=role.id))
                print(f"  Assigned role {role_name}")
            else:
                print(f"  Role {role_name} not found in DB (run seed.py first)")

        await session.commit()
        print("Test user seeded successfully")

if __name__ == "__main__":
    asyncio.run(seed_users())
