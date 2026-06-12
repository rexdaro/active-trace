import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.models.tenant import Tenant
from app.models.materia import Materia
from app.models.user import User
from app.integrations.moodle_ws import MoodleWSService

logger = logging.getLogger(__name__)


async def sync_nightly():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        stmt = select(Tenant).where(
            Tenant.moodle_ws_url.isnot(None),
            Tenant.moodle_token.isnot(None),
        )
        result = await db.execute(stmt)
        tenants = list(result.scalars().all())

        for tenant in tenants:
            mock_user = User(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                email="nightly-sync@system",
                hashed_password="",
                is_2fa_enabled=False,
            )
            try:
                result = await MoodleWSService.sync_from_moodle(db, mock_user, materia_id=None)
                if result["errores"]:
                    for err in result["errores"]:
                        logger.warning(f"Nightly sync tenant {tenant.id}: {err}")
                logger.info(f"Nightly sync tenant {tenant.id}: {result['materias_procesadas']} materias procesadas")
            except Exception as e:
                logger.error(f"Nightly sync tenant {tenant.id}: error {e}")

    await engine.dispose()


import uuid

if __name__ == "__main__":
    import asyncio
    asyncio.run(sync_nightly())
