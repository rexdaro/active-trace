import uuid
import csv
import io
from datetime import date, datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.encuentros import SlotEncuentroRepository, InstanciaEncuentroRepository
from app.repositories.guardias import GuardiaRepository
from app.services.audit import AuditService
from app.schemas.encuentro import (
    RecurrenteRequest,
    RecurrenteResponse,
    InstanciaEncuentroCreate,
    InstanciaEncuentroUpdate,
    InstanciaEncuentroRead,
    SlotEncuentroRead,
    HTMLBlockResponse,
    InstanciasListResponse,
    GuardiaCreate,
    GuardiaRead,
    GuardiaListResponse,
    GuardiaUpdate,
)
from app.models.user import User
from app.models.asignacion import Asignacion


class EncuentrosService:

    @staticmethod
    def _parse_horario_start(horario: str) -> str:
        return horario.split("–")[0].strip()

    @staticmethod
    async def crear_recurrente(
        db: AsyncSession,
        request: RecurrenteRequest,
        user: User,
    ) -> RecurrenteResponse:
        slot_repo = SlotEncuentroRepository(db)
        inst_repo = InstanciaEncuentroRepository(db)

        slot = await slot_repo.create_slot(
            materia_id=request.materia_id,
            creado_por=user.id,
            dia_semana=request.dia_semana,
            horario=request.horario,
            titulo=request.titulo,
            meet_url=request.meet_url,
            fecha_inicio=request.fecha_inicio,
            cant_semanas=request.cant_semanas,
            tenant_id=user.tenant_id,
        )
        await db.flush()

        hora_start = EncuentrosService._parse_horario_start(request.horario)

        instances_data = []
        for week in range(request.cant_semanas):
            fecha = request.fecha_inicio + timedelta(weeks=week)
            instances_data.append({
                "slot_id": slot.id,
                "materia_id": request.materia_id,
                "fecha": fecha,
                "hora": hora_start,
                "titulo": request.titulo,
                "meet_url": request.meet_url,
                "tenant_id": user.tenant_id,
            })

        instancias = await inst_repo.bulk_create(instances_data)
        await db.commit()

        await AuditService.log_action(
            db=db,
            action="ENCUENTRO_CREAR",
            user_id=str(user.id),
            resource="encuentros",
            status="success",
            actor_id=str(user.id),
            materia_id=str(request.materia_id),
            detalle={
                "tipo": "recurrente",
                "slot_id": str(slot.id),
                "instancias": len(instancias),
            },
            filas_afectadas=len(instancias),
        )

        return RecurrenteResponse(
            slot=SlotEncuentroRead.model_validate(slot),
            instancias_count=len(instancias),
        )

    @staticmethod
    async def crear_unico(
        db: AsyncSession,
        request: InstanciaEncuentroCreate,
        user: User,
    ) -> InstanciaEncuentroRead:
        inst_repo = InstanciaEncuentroRepository(db)

        instancia = await inst_repo.create(
            materia_id=request.materia_id,
            fecha=request.fecha,
            hora=request.hora,
            titulo=request.titulo,
            meet_url=request.meet_url,
            tenant_id=user.tenant_id,
            slot_id=None,
        )
        await db.commit()

        await AuditService.log_action(
            db=db,
            action="ENCUENTRO_CREAR",
            user_id=str(user.id),
            resource="encuentros",
            status="success",
            actor_id=str(user.id),
            materia_id=str(request.materia_id),
            detalle={
                "tipo": "unico",
                "instancia_id": str(instancia.id),
            },
            filas_afectadas=1,
        )

        return InstanciaEncuentroRead.model_validate(instancia)

    @staticmethod
    async def editar_instancia(
        db: AsyncSession,
        instancia_id: uuid.UUID,
        request: InstanciaEncuentroUpdate,
        user: User,
    ) -> InstanciaEncuentroRead:
        inst_repo = InstanciaEncuentroRepository(db)

        data = {}
        if request.estado is not None:
            data["estado"] = request.estado
        if request.meet_url is not None:
            data["meet_url"] = request.meet_url
        if request.video_url is not None:
            data["video_url"] = request.video_url
        if request.comentario is not None:
            data["comentario"] = request.comentario

        instancia = await inst_repo.update_instancia(
            id=instancia_id,
            data=data,
            tenant_id=user.tenant_id,
        )
        if instancia is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instancia no encontrada",
            )

        await db.commit()

        await AuditService.log_action(
            db=db,
            action="ENCUENTRO_EDITAR",
            user_id=str(user.id),
            resource="encuentros",
            status="success",
            actor_id=str(user.id),
            materia_id=str(instancia.materia_id),
            detalle={
                "instancia_id": str(instancia_id),
                "campos_actualizados": list(data.keys()),
            },
            filas_afectadas=1,
        )

        return InstanciaEncuentroRead.model_validate(instancia)

    @staticmethod
    async def get_instancias_by_materia(
        db: AsyncSession,
        materia_id: uuid.UUID,
        user: User,
        estado: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> InstanciasListResponse:
        inst_repo = InstanciaEncuentroRepository(db)

        instancias, total = await inst_repo.get_by_materia(
            materia_id=materia_id,
            tenant_id=user.tenant_id,
            estado=estado,
            offset=offset,
            limit=limit,
        )

        return InstanciasListResponse(
            items=[InstanciaEncuentroRead.model_validate(i) for i in instancias],
            total=total,
        )

    @staticmethod
    async def get_all_instancias(
        db: AsyncSession,
        user: User,
        materia_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> InstanciasListResponse:
        inst_repo = InstanciaEncuentroRepository(db)

        if materia_id is not None:
            instancias, total = await inst_repo.get_by_materia(
                materia_id=materia_id,
                tenant_id=user.tenant_id,
                offset=offset,
                limit=limit,
            )
        else:
            from app.repositories.base import BaseRepository
            from app.models.encuentro import InstanciaEncuentro
            from sqlalchemy import select, func

            query = select(InstanciaEncuentro).where(
                InstanciaEncuentro.tenant_id == user.tenant_id,
            )
            count_query = select(func.count()).select_from(InstanciaEncuentro).where(
                InstanciaEncuentro.tenant_id == user.tenant_id,
            )

            count_result = await db.execute(count_query)
            total = count_result.scalar() or 0

            query = query.offset(offset).limit(limit).order_by(InstanciaEncuentro.fecha)
            result = await db.execute(query)
            instancias = list(result.scalars().all())

        return InstanciasListResponse(
            items=[InstanciaEncuentroRead.model_validate(i) for i in instancias],
            total=total,
        )

    @staticmethod
    async def generate_html_block(
        db: AsyncSession,
        materia_id: uuid.UUID,
        user: User,
    ) -> HTMLBlockResponse:
        from app.models.encuentro import InstanciaEncuentro
        from sqlalchemy import select

        today = date.today()
        query = select(InstanciaEncuentro).where(
            InstanciaEncuentro.tenant_id == user.tenant_id,
            InstanciaEncuentro.materia_id == materia_id,
            InstanciaEncuentro.fecha >= today,
        ).order_by(InstanciaEncuentro.fecha)

        result = await db.execute(query)
        instancias = list(result.scalars().all())

        rows_html = ""
        for inst in instancias:
            meet_cell = f'<a href="{inst.meet_url}">Link</a>' if inst.meet_url else ""
            video_cell = f'<a href="{inst.video_url}">Video</a>' if inst.video_url else ""
            rows_html += (
                f"<tr>"
                f"<td>{inst.fecha.isoformat()}</td>"
                f"<td>{inst.hora}</td>"
                f"<td>{inst.titulo}</td>"
                f"<td>{meet_cell}</td>"
                f"<td>{video_cell}</td>"
                f"</tr>\n"
            )

        html = (
            "<table border='1' cellpadding='8' cellspacing='0' style='border-collapse:collapse;width:100%'>\n"
            "<thead>\n<tr>"
            "<th>Fecha</th><th>Hora</th><th>Título</th><th>Meet</th><th>Video</th>"
            "</tr>\n</thead>\n<tbody>\n"
            f"{rows_html}"
            "</tbody>\n</table>"
        )

        return HTMLBlockResponse(html=html)


class GuardiasService:

    @staticmethod
    async def _user_has_role(db: AsyncSession, user: User, role_name: str) -> bool:
        from app.models.user_role import UserRole
        from app.models.rbac import Role
        stmt = select(UserRole).join(Role).where(
            UserRole.user_id == user.id,
            Role.name == role_name,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def registrar(
        db: AsyncSession,
        request: GuardiaCreate,
        user: User,
    ) -> GuardiaRead:
        query = select(Asignacion).where(
            Asignacion.tenant_id == user.tenant_id,
            Asignacion.user_id == user.id,
            Asignacion.contexto_id == request.materia_id,
            Asignacion.hasta.is_(None),
        )
        result = await db.execute(query)
        asignacion = result.scalar_one_or_none()

        if not asignacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay asignación activa para esta materia",
            )

        repo = GuardiaRepository(db)
        guardia = await repo.create(
            materia_id=request.materia_id,
            carrera_id=request.carrera_id,
            cohorte_id=request.cohorte_id,
            dia=request.dia,
            horario=request.horario,
            tenant_id=user.tenant_id,
            asignacion_id=asignacion.id,
            comentarios=request.comentarios,
        )
        await db.commit()

        await AuditService.log_action(
            db=db,
            action="GUARDIA_REGISTRAR",
            user_id=str(user.id),
            resource="guardias",
            status="success",
            actor_id=str(user.id),
            materia_id=str(request.materia_id),
            detalle={
                "guardia_id": str(guardia.id),
                "dia": request.dia,
                "horario": request.horario,
            },
            filas_afectadas=1,
        )

        return GuardiaRead.model_validate(guardia)

    @staticmethod
    async def listar(
        db: AsyncSession,
        user: User,
        materia_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> GuardiaListResponse:
        repo = GuardiaRepository(db)

        is_tutor = await GuardiasService._user_has_role(db, user, "TUTOR")

        if is_tutor:
            guardias, total = await repo.get_by_user(
                user_id=user.id,
                tenant_id=user.tenant_id,
                materia_id=materia_id,
                offset=offset,
                limit=limit,
            )
        else:
            guardias, total = await repo.get_all(
                tenant_id=user.tenant_id,
                materia_id=materia_id,
                offset=offset,
                limit=limit,
            )

        return GuardiaListResponse(
            items=[GuardiaRead.model_validate(g) for g in guardias],
            total=total,
        )

    @staticmethod
    async def actualizar(
        db: AsyncSession,
        guardia_id: uuid.UUID,
        request: GuardiaUpdate,
        user: User,
    ) -> GuardiaRead:
        repo = GuardiaRepository(db)

        data = {}
        if request.estado is not None:
            data["estado"] = request.estado
        if request.comentarios is not None:
            data["comentarios"] = request.comentarios

        guardia = await repo.update_guardia(
            id=guardia_id,
            data=data,
            tenant_id=user.tenant_id,
        )
        if guardia is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guardia no encontrada",
            )

        await db.commit()

        await AuditService.log_action(
            db=db,
            action="GUARDIA_ACTUALIZAR",
            user_id=str(user.id),
            resource="guardias",
            status="success",
            actor_id=str(user.id),
            materia_id=str(guardia.materia_id),
            detalle={
                "guardia_id": str(guardia_id),
                "campos_actualizados": list(data.keys()),
            },
            filas_afectadas=1,
        )

        return GuardiaRead.model_validate(guardia)

    @staticmethod
    async def exportar_csv(
        db: AsyncSession,
        user: User,
        materia_id: uuid.UUID | None = None,
    ) -> str:
        repo = GuardiaRepository(db)
        guardias, _ = await repo.get_all(
            tenant_id=user.tenant_id,
            materia_id=materia_id,
            offset=0,
            limit=10000,
        )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "asignacion_id", "materia_id", "carrera_id", "cohorte_id",
            "dia", "horario", "estado", "comentarios", "created_at",
        ])
        for g in guardias:
            writer.writerow([
                str(g.id),
                str(g.asignacion_id),
                str(g.materia_id),
                str(g.carrera_id),
                str(g.cohorte_id),
                g.dia,
                g.horario,
                g.estado,
                g.comentarios or "",
                g.created_at.isoformat() if g.created_at else "",
            ])

        return output.getvalue()
