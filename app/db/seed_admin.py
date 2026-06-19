"""
Seed: crea un tenant de prueba y un usuario admin con contraseña.
Correr con: python -m app.db.seed_admin
"""
import asyncio
import uuid
from datetime import datetime
from sqlalchemy import select
import bcrypt

from app.core.database import AsyncSessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.models.rbac import Role
from app.models.user_role import UserRole


async def seed_admin():
    async with AsyncSessionLocal() as session:
        # 1. Crear tenant si no existe
        result = await session.execute(
            select(Tenant).filter(Tenant.name == "Tenant Demo")
        )
        tenant = result.scalar_one_or_none()
        if not tenant:
            tenant = Tenant(
                id=uuid.uuid4(),
                name="Tenant Demo",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(tenant)
            await session.flush()
            print(f"✓ Tenant creado: {tenant.name} (id={tenant.id})")
        else:
            print(f"→ Tenant ya existe: {tenant.name}")

        # 2. Crear usuario admin
        result = await session.execute(
            select(User).filter(User.email == "admin@activia-trace.com")
        )
        user = result.scalar_one_or_none()
        if not user:
            password = "admin123"
            hashed = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

            user = User(
                id=uuid.uuid4(),
                email="admin@activia-trace.com",
                tenant_id=tenant.id,
                hashed_password=hashed,
                is_2fa_enabled=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(user)
            await session.flush()
            print(f"✓ Usuario creado: {user.email} / pass: {password}")
        else:
            print(f"→ Usuario ya existe: {user.email}")

        # 3. Asignar rol ADMIN
        result = await session.execute(select(Role).filter(Role.name == "ADMIN"))
        admin_role = result.scalar_one_or_none()

        if admin_role:
            result = await session.execute(
                select(UserRole).filter(
                    UserRole.user_id == user.id,
                    UserRole.role_id == admin_role.id,
                )
            )
            existing = result.scalar_one_or_none()
            if not existing:
                ur = UserRole(
                    user_id=user.id,
                    role_id=admin_role.id,
                )
                session.add(ur)
                print(f"✓ Rol ADMIN asignado a {user.email}")
            else:
                print(f"→ Rol ADMIN ya asignado")
        else:
            print("⚠️  Rol ADMIN no encontrado — ejecutá primero app.db.seed")

        # 4. Asignar también rol COORDINADOR
        result = await session.execute(select(Role).filter(Role.name == "COORDINADOR"))
        coord_role = result.scalar_one_or_none()
        if coord_role:
            result = await session.execute(
                select(UserRole).filter(
                    UserRole.user_id == user.id,
                    UserRole.role_id == coord_role.id,
                )
            )
            existing = result.scalar_one_or_none()
            if not existing:
                ur = UserRole(
                    user_id=user.id,
                    role_id=coord_role.id,
                )
                session.add(ur)
                print(f"✓ Rol COORDINADOR asignado a {user.email}")

        await session.commit()
        print("\n✅ Seed de admin completo!")
        print(f"   Email:    admin@activia-trace.com")
        print(f"   Password: admin123")


if __name__ == "__main__":
    asyncio.run(seed_admin())
