from __future__ import annotations
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.coloquios import ColoquiosRepository
from app.services.audit import AuditService
from app.schemas.coloquio import (
    EvaluacionCreate,
    EvaluacionRead,
    ReservaCreate,
    ReservaRead,
    ReservaCancelResponse,
    ResultadoCreate,
    ResultadoRead,
    ImportAlumnosRequest,
    ImportAlumnosResponse,
    ConvovatoriaListItem,
    ConvocatoriaListResponse,
    PanelMetricas,
)
from sqlalchemy import select
from app.models.user import User
from app.models.materia import Materia
from app.models.coloquio import EstadoReserva


class ColoquiosService:

    @staticmethod
    async def crear_convocatoria(db: AsyncSession, request: EvaluacionCreate, user: User) -> EvaluacionRead:
        repo = ColoquiosRepository(db)
        evaluacion = await repo.crear_evaluacion({
            **request.model_dump(),
            "tenant_id": user.tenant_id,
        })
        await db.commit()
        await AuditService.log_action(
            db=db,
            action="COLOQUIO_CREAR",
            user_id=str(user.id),
            resource="coloquios",
            status="success",
            actor_id=str(user.id),
            materia_id=str(request.materia_id),
            detalle={"tipo": request.tipo, "instancia": request.instancia},
        )
        return EvaluacionRead.model_validate(evaluacion)

    @staticmethod
    async def import_alumnos(
        db: AsyncSession,
        request: ImportAlumnosRequest,
        user: User,
    ) -> ImportAlumnosResponse:
        repo = ColoquiosRepository(db)
        evaluacion = await repo.get_evaluacion(request.evaluacion_id, user.tenant_id)
        if not evaluacion:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convocatoria no encontrada")

        await AuditService.log_action(
            db=db,
            action="COLOQUIO_IMPORTAR",
            user_id=str(user.id),
            resource="coloquios",
            status="success",
            actor_id=str(user.id),
            materia_id=str(evaluacion.materia_id),
            detalle={"evaluacion_id": str(request.evaluacion_id), "cantidad": len(request.alumno_ids)},
        )
        return ImportAlumnosResponse(evaluacion_id=request.evaluacion_id, cantidad=len(request.alumno_ids))

    @staticmethod
    async def reservar_turno(db: AsyncSession, request: ReservaCreate, user: User) -> ReservaRead:
        repo = ColoquiosRepository(db)
        evaluacion = await repo.get_evaluacion(request.evaluacion_id, user.tenant_id)
        if not evaluacion:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convocatoria no encontrada")

        count = await repo.count_reservas_activas_by_evaluacion_y_fecha(
            request.evaluacion_id, request.fecha_hora, user.tenant_id,
        )
        if count >= evaluacion.cupos_por_dia:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay cupos disponibles para esa fecha/hora",
            )

        existing = await repo.get_reservas_activas_by_alumno(user.id, request.evaluacion_id, user.tenant_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya tienes una reserva activa para esta convocatoria",
            )

        reserva = await repo.crear_reserva({
            "evaluacion_id": request.evaluacion_id,
            "alumno_id": user.id,
            "fecha_hora": request.fecha_hora,
            "estado": EstadoReserva.ACTIVA.value,
            "tenant_id": user.tenant_id,
        })
        await db.commit()
        await AuditService.log_action(
            db=db,
            action="COLOQUIO_RESERVAR",
            user_id=str(user.id),
            resource="coloquios",
            status="success",
            actor_id=str(user.id),
        )
        return ReservaRead.model_validate(reserva)

    @staticmethod
    async def cancelar_reserva(db: AsyncSession, reserva_id: uuid.UUID, user: User) -> ReservaCancelResponse:
        repo = ColoquiosRepository(db)
        reserva = await repo.get_reserva(reserva_id, user.tenant_id)
        if not reserva:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva no encontrada")
        if reserva.estado != EstadoReserva.ACTIVA.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden cancelar reservas activas",
            )

        cancelled = await repo.cancelar_reserva(reserva_id, user.tenant_id)
        await db.commit()
        await AuditService.log_action(
            db=db,
            action="COLOQUIO_CANCELAR",
            user_id=str(user.id),
            resource="coloquios",
            status="success",
            actor_id=str(user.id),
        )
        return ReservaCancelResponse(id=cancelled.id, estado=cancelled.estado)

    @staticmethod
    async def get_convocatorias(
        db: AsyncSession,
        user: User,
        materia_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> ConvocatoriaListResponse:
        repo = ColoquiosRepository(db)
        evaluaciones, total = await repo.get_evaluaciones(user.tenant_id, materia_id, offset, limit)
        # Pre-load materia names
        materia_ids = {ev.materia_id for ev in evaluaciones}
        materia_nombres: dict[uuid.UUID, str] = {}
        if materia_ids:
            stmt = select(Materia.id, Materia.name).where(Materia.id.in_(materia_ids))
            result = await db.execute(stmt)
            for row in result.all():
                materia_nombres[row.id] = row.name

        items = []
        for ev in evaluaciones:
            reservas = await repo.get_reservas_by_evaluacion(ev.id, user.tenant_id, estado=EstadoReserva.ACTIVA.value)
            items.append(ConvovatoriaListItem(
                id=ev.id,
                materia_id=ev.materia_id,
                materia_nombre=materia_nombres.get(ev.materia_id, ""),
                cohorte_id=ev.cohorte_id,
                tipo=ev.tipo,
                instancia=ev.instancia,
                cupos_por_dia=ev.cupos_por_dia,
                total_alumnos=0,
                reservas_activas=len(reservas),
                created_at=ev.created_at,
            ))
        return ConvocatoriaListResponse(items=items, total=total)

    @staticmethod
    async def get_panel_metricas(db: AsyncSession, user: User) -> PanelMetricas:
        repo = ColoquiosRepository(db)
        return await repo.get_panel_metricas(user.tenant_id)

    @staticmethod
    async def registrar_resultado(db: AsyncSession, request: ResultadoCreate, user: User) -> ResultadoRead:
        repo = ColoquiosRepository(db)
        evaluacion = await repo.get_evaluacion(request.evaluacion_id, user.tenant_id)
        if not evaluacion:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convocatoria no encontrada")

        resultado = await repo.crear_resultado({
            "evaluacion_id": request.evaluacion_id,
            "alumno_id": request.alumno_id,
            "nota_final": request.nota_final,
            "tenant_id": user.tenant_id,
        })
        await db.commit()
        await AuditService.log_action(
            db=db,
            action="COLOQUIO_RESULTADO",
            user_id=str(user.id),
            resource="coloquios",
            status="success",
            actor_id=str(user.id),
            materia_id=str(evaluacion.materia_id),
            detalle={"alumno_id": str(request.alumno_id), "nota": request.nota_final},
        )
        return ResultadoRead.model_validate(resultado)

    @staticmethod
    async def get_resultados(
        db: AsyncSession,
        evaluacion_id: uuid.UUID,
        user: User,
    ) -> list[ResultadoRead]:
        repo = ColoquiosRepository(db)
        resultados = await repo.get_resultados_by_evaluacion(evaluacion_id, user.tenant_id)
        return [ResultadoRead.model_validate(r) for r in resultados]

    @staticmethod
    async def get_mis_reservas(db: AsyncSession, user: User) -> list[ReservaRead]:
        repo = ColoquiosRepository(db)
        reservas = await repo.get_reservas_by_alumno(user.id, user.tenant_id)
        return [ReservaRead.model_validate(r) for r in reservas]
