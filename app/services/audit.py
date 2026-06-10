from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog

class AuditService:
    @staticmethod
    async def log_action(
        db: AsyncSession,
        action: str,
        user_id: str,
        resource: str,
        status: str,
        actor_id: str,
        impersonator_id: str = None,
        materia_id: str = None,
        detalle: dict = {},
        filas_afectadas: int = 0,
        ip: str = None,
        user_agent: str = None
    ):
        audit = AuditLog(
            action=action,
            user_id=user_id,
            resource=resource,
            status=status,
            actor_id=actor_id,
            impersonator_id=impersonator_id,
            materia_id=materia_id,
            detalle=detalle,
            filas_afectadas=filas_afectadas,
            ip=ip,
            user_agent=user_agent
        )
        db.add(audit)
        await db.commit()
