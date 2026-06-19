"""
Migration script: unify `users` and `usuarios` into a single `users` table.

Steps:
1. Add new columns to `users` (dni, cuil, cbu, nombre, datos_fiscales, datos_bancarios, regional, modalidad_cobro)
2. Copy data from `usuarios` to `users` matching by id
3. Drop `usuarios` table

Run: python -m app.db.migrate_users_usuarios
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import text
from app.core.database import engine


async def migrate():
    print("=== Starting migration: users + usuarios → users ===")

    async with engine.connect() as conn:
        # 1. Check if columns already exist
        result = await conn.execute(text("PRAGMA table_info('users')"))
        existing_cols = {row[1] for row in result.fetchall()}

        columns_to_add = {
            "dni": "VARCHAR",
            "cuil": "VARCHAR",
            "cbu": "VARCHAR",
            "nombre": "VARCHAR",
            "datos_fiscales": "VARCHAR",
            "datos_bancarios": "VARCHAR",
            "regional": "VARCHAR",
            "modalidad_cobro": "VARCHAR",
        }

        for col, coltype in columns_to_add.items():
            if col not in existing_cols:
                print(f"  Adding column {col} to users...")
                await conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {coltype} NULL"))
            else:
                print(f"  Column {col} already exists in users, skipping.")

        # 2. Check if usuarios table exists
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'"))
        if result.scalar_one_or_none():
            # Copy data from usuarios → users matching by id
            print("  Copying data from usuarios to users (matched by id)...")
            await conn.execute(text(
                """
                UPDATE users
                SET dni = (SELECT u._dni FROM usuarios u WHERE u.id = users.id),
                    cuil = (SELECT u._cuil FROM usuarios u WHERE u.id = users.id),
                    cbu = (SELECT u._cbu FROM usuarios u WHERE u.id = users.id),
                    nombre = (SELECT u.nombre FROM usuarios u WHERE u.id = users.id),
                    datos_fiscales = (SELECT u.datos_fiscales FROM usuarios u WHERE u.id = users.id),
                    datos_bancarios = (SELECT u.datos_bancarios FROM usuarios u WHERE u.id = users.id),
                    regional = (SELECT u.regional FROM usuarios u WHERE u.id = users.id),
                    modalidad_cobro = (SELECT u.modalidad_cobro FROM usuarios u WHERE u.id = users.id)
                WHERE EXISTS (SELECT 1 FROM usuarios u WHERE u.id = users.id)
                """
            ))

            # Also create users from usuarios that don't have a matching user entry
            await conn.execute(text(
                """
                INSERT OR IGNORE INTO users (id, tenant_id, email, hashed_password, dni, cuil, cbu, nombre,
                                            datos_fiscales, datos_bancarios, regional, modalidad_cobro,
                                            created_at, updated_at)
                SELECT u.id, u.tenant_id, u.email, '', u._dni, u._cuil, u._cbu, u.nombre,
                       u.datos_fiscales, u.datos_bancarios, u.regional, u.modalidad_cobro,
                       u.created_at, u.updated_at
                FROM usuarios u
                WHERE NOT EXISTS (SELECT 1 FROM users s WHERE s.id = u.id)
                """
            ))

            # 3. Drop usuarios table
            print("  Dropping usuarios table...")
            await conn.execute(text("DROP TABLE IF EXISTS usuarios"))
            print("  usuarios table dropped.")
        else:
            print("  usuarios table does not exist, skipping migration.")

        await conn.commit()

    print("=== Migration complete ===")


if __name__ == "__main__":
    asyncio.run(migrate())
