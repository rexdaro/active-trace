import asyncio
import logging
import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage

from app.core.database import AsyncSessionLocal
from app.models.tenant import Tenant
from app.models.comunicacion import ComunicacionEstado
from app.repositories.comunicaciones import ComunicacionesRepository

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BACKOFF_BASE = 2
BATCH_SIZE = 50
POLL_INTERVAL = 10

SMTP_CONFIG = {
    "host": os.environ.get("SMTP_HOST", "localhost"),
    "port": int(os.environ.get("SMTP_PORT", "25")),
    "from": os.environ.get("SMTP_FROM", "noreply@activia-trace.com"),
    "user": os.environ.get("SMTP_USER", ""),
    "password": os.environ.get("SMTP_PASSWORD", ""),
    "use_tls": os.environ.get("SMTP_USE_TLS", "false").lower() == "true",
    "timeout": int(os.environ.get("SMTP_TIMEOUT", "30")),
}


async def send_email(
    destinatario: str,
    asunto: str,
    cuerpo: str,
    smtp_config: dict | None = None,
) -> bool:
    try:
        cfg = smtp_config or SMTP_CONFIG
        loop = asyncio.get_running_loop()

        def _sync_send():
            msg = EmailMessage()
            msg["Subject"] = asunto
            msg["From"] = cfg["from"]
            msg["To"] = destinatario
            msg.set_content(cuerpo)

            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=cfg.get("timeout", 30)) as server:
                if cfg.get("use_tls"):
                    server.starttls()
                if cfg.get("user"):
                    server.login(cfg["user"], cfg.get("password", ""))
                server.send_message(msg)

        await loop.run_in_executor(None, _sync_send)
        return True
    except Exception as e:
        logger.warning("send_email failed: %s", e)
        return False


async def process_pending_messages(
    db,
    tenant_id,
    send_func=None,
    max_retries: int | None = None,
    backoff_base: int | None = None,
) -> tuple[int, int]:
    if send_func is None:
        send_func = send_email

    retries = max_retries if max_retries is not None else MAX_RETRIES
    backoff = backoff_base if backoff_base is not None else BACKOFF_BASE

    repo = ComunicacionesRepository(db)
    pendientes = await repo.get_pendientes_elegibles(tenant_id, BATCH_SIZE)

    sent = 0
    failed = 0

    for msg in pendientes:
        comunicacion = await repo.transition_state(
            msg.id,
            ComunicacionEstado.PENDIENTE.value,
            ComunicacionEstado.ENVIANDO.value,
            tenant_id,
        )
        if comunicacion is None:
            continue

        success = False
        for attempt in range(retries):
            if await send_func(comunicacion.destinatario, comunicacion.asunto, comunicacion.cuerpo):
                success = True
                break
            if attempt < retries - 1:
                await asyncio.sleep(backoff ** attempt)

        if success:
            c2 = await repo.transition_state(
                msg.id,
                ComunicacionEstado.ENVIANDO.value,
                ComunicacionEstado.ENVIADO.value,
                tenant_id,
            )
            if c2:
                c2.enviado_at = datetime.now(timezone.utc)
                await db.flush()
            sent += 1
        else:
            await repo.transition_state(
                msg.id,
                ComunicacionEstado.ENVIANDO.value,
                ComunicacionEstado.ERROR.value,
                tenant_id,
            )
            failed += 1

    return sent, failed


async def worker_loop(app):
    while True:
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                result = await db.execute(select(Tenant))
                tenants = list(result.scalars().all())

                for tenant in tenants:
                    try:
                        sent, failed = await process_pending_messages(db, tenant.id)
                        if sent or failed:
                            logger.info("Tenant %s: %d sent, %d failed", tenant.id, sent, failed)
                    except Exception as e:
                        logger.error("Tenant %s error: %s", tenant.id, e)
        except Exception as e:
            logger.error("Worker loop error: %s", e)

        await asyncio.sleep(POLL_INTERVAL)


def start_worker(app):
    task = asyncio.create_task(worker_loop(app))
    return task
