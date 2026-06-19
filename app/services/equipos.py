import uuid
import csv
import io
from datetime import datetime, timezone
from sqlalchemy import select, update, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models.asignacion import Asignacion
from app.models.rbac import Role
from app.models.user import User
from app.schemas.equipos import (
    AsignacionMasivaRequest, AsignacionMasivaResponse,
    ClonarRequest, ClonarResponse,
    ModificarVigenciaRequest, ModificarVigenciaResponse,
    AsignacionReadWithAttributes,
)
from app.services.audit import AuditService


class EquiposService:

    @staticmethod
    async def mis_equipos(db: AsyncSession, user: User) -> list[Asignacion]:
        stmt = (
            select(Asignacion)
            .where(
                Asignacion.user_id == user.id,
                Asignacion.tenant_id == user.tenant_id,
            )
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def listar(
        db: AsyncSession,
        user: User,
        materia_id: uuid.UUID | None = None,
        carrera_id: uuid.UUID | None = None,
        cohorte_id: uuid.UUID | None = None,
        role_id: int | None = None,
        user_id: uuid.UUID | None = None,
        vigente: bool | None = None,
    ) -> list[Asignacion]:
        stmt = select(Asignacion).where(Asignacion.tenant_id == user.tenant_id)

        filters = []
        if materia_id is not None:
            filters.append(Asignacion.contexto_id == materia_id)
        if carrera_id is not None:
            filters.append(Asignacion.contexto_id == carrera_id)
        if cohorte_id is not None:
            filters.append(Asignacion.contexto_id == cohorte_id)
        if role_id is not None:
            filters.append(Asignacion.role_id == role_id)
        if user_id is not None:
            filters.append(Asignacion.user_id == user_id)
        if vigente is True:
            now = datetime.now(timezone.utc)
            filters.append(
                and_(
                    Asignacion.desde <= now,
                    or_(Asignacion.hasta.is_(None), Asignacion.hasta >= now),
                )
            )
        elif vigente is False:
            now = datetime.now(timezone.utc)
            filters.append(
                or_(
                    Asignacion.desde > now,
                    and_(Asignacion.hasta.isnot(None), Asignacion.hasta < now),
                )
            )

        if filters:
            stmt = stmt.where(and_(*filters))

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def asignar_masiva(
        db: AsyncSession, user: User, request: AsignacionMasivaRequest
    ) -> AsignacionMasivaResponse:
        asignaciones = []
        for a in request.asignaciones:
            nueva = Asignacion(
                tenant_id=user.tenant_id,
                user_id=a.user_id,
                role_id=a.role_id,
                contexto_id=a.contexto_id,
                responsable_id=a.responsable_id,
                desde=a.desde,
                hasta=a.hasta,
            )
            db.add(nueva)
            asignaciones.append(nueva)

        await db.commit()
        for a in asignaciones:
            await db.refresh(a)

        await AuditService.log_action(
            db=db,
            action="ASIGNACION_MODIFICAR",
            user_id=str(user.id),
            resource="asignaciones",
            status="success",
            actor_id=str(user.id),
            filas_afectadas=len(asignaciones),
        )

        return AsignacionMasivaResponse(
            creadas=len(asignaciones),
            asignaciones=[AsignacionReadWithAttributes.model_validate(a) for a in asignaciones],
        )

    @staticmethod
    async def clonar(
        db: AsyncSession, user: User, request: ClonarRequest
    ) -> ClonarResponse:
        now = datetime.now(timezone.utc)
        stmt = (
            select(Asignacion)
            .where(
                Asignacion.tenant_id == user.tenant_id,
                Asignacion.contexto_id == request.origen_contexto_id,
            )
            .where(
                or_(
                    Asignacion.hasta.is_(None),
                    Asignacion.hasta > now,
                )
            )
        )
        result = await db.execute(stmt)
        activas = list(result.scalars().all())

        nuevas = []
        for a in activas:
            clon = Asignacion(
                tenant_id=user.tenant_id,
                user_id=a.user_id,
                role_id=a.role_id,
                contexto_id=request.destino_contexto_id,
                responsable_id=a.responsable_id,
                desde=request.nuevo_desde,
                hasta=request.nuevo_hasta,
            )
            db.add(clon)
            nuevas.append(clon)

        await db.commit()
        for c in nuevas:
            await db.refresh(c)

        await AuditService.log_action(
            db=db,
            action="ASIGNACION_MODIFICAR",
            user_id=str(user.id),
            resource="asignaciones",
            status="success",
            actor_id=str(user.id),
            filas_afectadas=len(nuevas),
        )

        return ClonarResponse(
            clonadas=len(nuevas),
            asignaciones=[AsignacionReadWithAttributes.model_validate(c) for c in nuevas],
        )

    @staticmethod
    async def modificar_vigencia(
        db: AsyncSession, user: User, request: ModificarVigenciaRequest
    ) -> ModificarVigenciaResponse:
        stmt = (
            update(Asignacion)
            .where(
                Asignacion.tenant_id == user.tenant_id,
                Asignacion.contexto_id == request.contexto_id,
            )
            .values(
                desde=request.nuevo_desde,
                hasta=request.nuevo_hasta,
            )
        )
        result = await db.execute(stmt)
        await db.commit()

        filas = result.rowcount

        await AuditService.log_action(
            db=db,
            action="ASIGNACION_MODIFICAR",
            user_id=str(user.id),
            resource="asignaciones",
            status="success",
            actor_id=str(user.id),
            filas_afectadas=filas,
        )

        return ModificarVigenciaResponse(modificadas=filas)

    @staticmethod
    async def exportar(
        db: AsyncSession, user: User, contexto_id: uuid.UUID
    ) -> str:
        stmt = (
            select(Asignacion)
            .where(
                Asignacion.tenant_id == user.tenant_id,
                Asignacion.contexto_id == contexto_id,
            )
        )
        result = await db.execute(stmt)
        asignaciones = list(result.scalars().all())

        output = io.StringIO()
        output.write("\ufeff")
        writer = csv.writer(output)
        writer.writerow([
            "user_id", "email", "dni", "nombre", "rol",
            "contexto_id", "responsable_id", "desde", "hasta", "estado_vigencia",
        ])

        for a in asignaciones:
            usuario = await db.get(User, a.user_id)
            role = await db.get(Role, a.role_id)
            now = datetime.now(timezone.utc)
            if a.hasta is None:
                vigente = a.desde <= now
            else:
                vigente = a.desde <= now <= a.hasta

            writer.writerow([
                str(a.user_id),
                usuario.email if usuario else "",
                usuario.dni if usuario else "",
                "",
                role.name if role else "",
                str(a.contexto_id),
                str(a.responsable_id) if a.responsable_id else "",
                a.desde.isoformat(),
                a.hasta.isoformat() if a.hasta else "",
                "vigente" if vigente else "vencida",
            ])

        return output.getvalue()
