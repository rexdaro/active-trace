import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.avisos import AvisoRepository
from app.models.aviso import Aviso, AcknowledgmentAviso, AlcanceAviso
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.models.rbac import Role
from app.models.user_role import UserRole
from app.models.user import User
from app.services.audit import AuditService
from app.schemas.aviso import (
    AvisoCreate,
    AvisoUpdate,
    AvisoResponse,
    AvisoConAckResponse,
    AvisoListParams,
)


class AvisoService:

    @staticmethod
    async def create(
        db: AsyncSession,
        obj_in: AvisoCreate,
        usuario_actual: User,
    ) -> Aviso:
        if obj_in.alcance == AlcanceAviso.POR_MATERIA:
            if obj_in.materia_id is None:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="materia_id requerido para alcance PorMateria")
            materia = await db.get(Materia, obj_in.materia_id)
            if not materia:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Materia no encontrada")

        if obj_in.alcance == AlcanceAviso.POR_COHORTE:
            if obj_in.cohorte_id is None:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="cohorte_id requerido para alcance PorCohorte")
            cohorte = await db.get(Cohorte, obj_in.cohorte_id)
            if not cohorte:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Cohorte no encontrada")

        if obj_in.alcance == AlcanceAviso.POR_ROL:
            if not obj_in.rol_destino:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="rol_destino requerido para alcance PorRol")
            stmt = select(Role).where(Role.name == obj_in.rol_destino)
            result = await db.execute(stmt)
            role = result.scalar_one_or_none()
            if not role:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Rol '{obj_in.rol_destino}' no válido")

        repo = AvisoRepository(db)
        data = obj_in.model_dump()
        if obj_in.alcance:
            data["alcance"] = obj_in.alcance.value
        if obj_in.severidad:
            data["severidad"] = obj_in.severidad.value

        aviso = await repo.create(data, usuario_actual.tenant_id)
        await db.commit()

        await AuditService.log_action(
            db=db,
            action="AVISO_CREAR",
            user_id=str(usuario_actual.id),
            resource="avisos",
            status="success",
            actor_id=str(usuario_actual.id),
            detalle={"titulo": obj_in.titulo},
        )

        return aviso

    @staticmethod
    async def update(
        db: AsyncSession,
        id: uuid.UUID,
        obj_in: AvisoUpdate,
        usuario_actual: User,
    ) -> Aviso:
        repo = AvisoRepository(db)
        aviso = await repo.get(id, usuario_actual.tenant_id)
        if not aviso:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Aviso no encontrado")

        data = obj_in.model_dump(exclude_unset=True)
        if "alcance" in data and data["alcance"] is not None:
            data["alcance"] = data["alcance"].value if hasattr(data["alcance"], "value") else data["alcance"]
        if "severidad" in data and data["severidad"] is not None:
            data["severidad"] = data["severidad"].value if hasattr(data["severidad"], "value") else data["severidad"]

        updated = await repo.update(aviso, data)
        await db.commit()
        await db.refresh(updated)

        await AuditService.log_action(
            db=db,
            action="AVISO_ACTUALIZAR",
            user_id=str(usuario_actual.id),
            resource="avisos",
            status="success",
            actor_id=str(usuario_actual.id),
            detalle={"aviso_id": str(id), "titulo": obj_in.titulo},
        )

        return updated

    @staticmethod
    async def delete(
        db: AsyncSession,
        id: uuid.UUID,
        usuario_actual: User,
    ) -> None:
        repo = AvisoRepository(db)
        aviso = await repo.get(id, usuario_actual.tenant_id)
        if not aviso:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Aviso no encontrado")

        await repo.delete(id, usuario_actual.tenant_id)
        await db.commit()

        await AuditService.log_action(
            db=db,
            action="AVISO_ELIMINAR",
            user_id=str(usuario_actual.id),
            resource="avisos",
            status="success",
            actor_id=str(usuario_actual.id),
            detalle={"aviso_id": str(id), "titulo": aviso.titulo},
        )

    @staticmethod
    async def get(
        db: AsyncSession,
        id: uuid.UUID,
        usuario_actual: User,
    ) -> Aviso:
        repo = AvisoRepository(db)
        aviso = await repo.get(id, usuario_actual.tenant_id)
        if not aviso:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Aviso no encontrado")
        return aviso

    @staticmethod
    async def list_para_usuario(
        db: AsyncSession,
        usuario_actual: User,
    ) -> list[AvisoConAckResponse]:
        usuario_rol = None
        stmt = (
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == usuario_actual.id)
        )
        result = await db.execute(stmt)
        roles = result.scalars().all()
        if roles:
            usuario_rol = roles[0]

        repo = AvisoRepository(db)
        avisos = await repo.list_visibles(
            tenant_id=usuario_actual.tenant_id,
            usuario_rol=usuario_rol,
            usuario_id=usuario_actual.id,
            materia_ids=None,
            cohorte_ids=None,
        )

        result = []
        for aviso in avisos:
            acknowledged = None
            if aviso.requiere_ack:
                ack = await repo.get_ack(aviso.id, usuario_actual.id, usuario_actual.tenant_id)
                acknowledged = ack is not None
            aviso_resp = AvisoResponse.model_validate(aviso)
            result.append(AvisoConAckResponse(
                **aviso_resp.model_dump(),
                acknowledged=acknowledged,
            ))

        return result

    @staticmethod
    async def confirmar_lectura(
        db: AsyncSession,
        aviso_id: uuid.UUID,
        usuario_actual: User,
    ) -> AcknowledgmentAviso:
        repo = AvisoRepository(db)

        aviso = await repo.get(aviso_id, usuario_actual.tenant_id)
        if not aviso:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Aviso no encontrado")

        existing = await repo.get_ack(aviso_id, usuario_actual.id, usuario_actual.tenant_id)
        if existing:
            return existing

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        fin_en = aviso.fin_en.replace(tzinfo=None) if aviso.fin_en.tzinfo else aviso.fin_en
        if now > fin_en:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Aviso fuera de vigencia")

        ack = await repo.create_ack(aviso_id, usuario_actual.id, usuario_actual.tenant_id)
        await db.commit()

        await AuditService.log_action(
            db=db,
            action="AVISO_CONFIRMAR",
            user_id=str(usuario_actual.id),
            resource="avisos",
            status="success",
            actor_id=str(usuario_actual.id),
            detalle={"aviso_id": str(aviso_id), "titulo": aviso.titulo},
        )

        return ack

    @staticmethod
    async def get_metricas(
        db: AsyncSession,
        aviso_id: uuid.UUID,
        usuario_actual: User,
    ) -> dict:
        repo = AvisoRepository(db)

        aviso = await repo.get(aviso_id, usuario_actual.tenant_id)
        if not aviso:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Aviso no encontrado")

        total_acks = await repo.get_ack_count(aviso_id, usuario_actual.tenant_id)
        total_views = await repo.get_visto_count(aviso_id, usuario_actual.tenant_id)

        return {
            "aviso_id": str(aviso_id),
            "titulo": aviso.titulo,
            "total_acks": total_acks,
            "total_views": total_views,
        }

    @staticmethod
    async def list_all(
        db: AsyncSession,
        usuario_actual: User,
        params: AvisoListParams | None = None,
    ) -> list[Aviso]:
        repo = AvisoRepository(db)
        params = params or AvisoListParams()
        items, _total = await repo.list_all(
            tenant_id=usuario_actual.tenant_id,
            params=params,
        )
        return items

    @staticmethod
    async def list_acks(
        db: AsyncSession,
        aviso_id: uuid.UUID,
        usuario_actual: User,
    ) -> list[AcknowledgmentAviso]:
        repo = AvisoRepository(db)

        aviso = await repo.get(aviso_id, usuario_actual.tenant_id)
        if not aviso:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Aviso no encontrado")

        items, _total = await repo.list_acks_for_aviso(
            aviso_id=aviso_id,
            tenant_id=usuario_actual.tenant_id,
        )
        return items
