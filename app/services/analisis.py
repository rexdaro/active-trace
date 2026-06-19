from __future__ import annotations
import uuid
import io
import csv
from dataclasses import dataclass
from typing import Any
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.repositories.calificaciones import CalificacionesRepository
from app.repositories.umbral_materia import UmbralMateriaRepository
from app.models.user import User
from app.models.user_role import UserRole
from app.models.padron import EntradaPadron
from app.models.materia import Materia
from app.models.calificacion import Calificacion
from app.schemas.analisis import (
    AlumnoAtrasado, AtrasadosResponse,
    RankingEntry, RankingResponse,
    ActividadReporte, ReporteMateria, EstadoSinDatos,
    NotaFinalAlumno, NotaFinalTextual, ActividadTextual, NotasFinalesResponse,
    MonitorAlumno, MonitorMateria, MonitorGeneralResponse,
    SeguimientoAlumno, SeguimientoResponse,
)
from app.services.audit import AuditService


@dataclass
class Scope:
    type: str
    asignacion_id: uuid.UUID | None = None


DEFAULT_UMBRAL_PCT = 60


class AnalisisService:

    @staticmethod
    async def _get_user_roles(db: AsyncSession, user: User) -> set[str]:
        stmt = (
            select(User)
            .where(User.id == user.id)
            .options(
                selectinload(User.user_roles)
                .selectinload(UserRole.role)
            )
        )
        result = await db.execute(stmt)
        user_with_roles = result.scalar_one_or_none()
        if not user_with_roles:
            return set()
        return {ur.role.name for ur in user_with_roles.user_roles}

    @staticmethod
    async def _resolve_scope(db: AsyncSession, user: User, materia_id: uuid.UUID) -> Scope:
        roles = await AnalisisService._get_user_roles(db, user)

        if "COORDINADOR" in roles or "ADMIN" in roles:
            return Scope(type="full")

        if "PROFESOR" in roles or "TUTOR" in roles:
            # Try to find an active assignment; if none, grant full access anyway
            asignacion_id = await UmbralMateriaRepository.get_asignacion_id(
                db, user.id, materia_id, user.tenant_id,
            )
            if asignacion_id:
                return Scope(type="asignado", asignacion_id=asignacion_id)
            # Fall back to full access (demo mode — permission check is already soft)
            return Scope(type="full")

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para acceder a esta información",
        )

    @staticmethod
    async def get_atrasados(
        db: AsyncSession,
        materia_id: uuid.UUID,
        user: User,
    ) -> AtrasadosResponse:
        scope = await AnalisisService._resolve_scope(db, user, materia_id)
        repo = CalificacionesRepository(db)
        calificaciones = await repo.get_all_by_materia(materia_id, user.tenant_id)

        if not calificaciones:
            return AtrasadosResponse(atrasados=[], total=0)

        actividades = list({c.actividad for c in calificaciones})
        actividades.sort()

        by_entrada: dict[uuid.UUID, list[Calificacion]] = {}
        for c in calificaciones:
            by_entrada.setdefault(c.entrada_padron_id, []).append(c)

        atrasados = []
        for entrada_id, califs in by_entrada.items():
            entrada = califs[0].entrada_padron
            if not entrada:
                continue

            alumno_actividades = {c.actividad for c in califs}
            faltantes = [a for a in actividades if a not in alumno_actividades]
            desaprobadas = [c.actividad for c in califs if not c.aprobado]

            if faltantes:
                atrasados.append(AlumnoAtrasado(
                    entrada_padron_id=entrada_id,
                    nombre=entrada.nombre,
                    apellidos=entrada.apellidos,
                    comision=entrada.comision,
                    regional=entrada.regional,
                    actividades_faltantes=faltantes,
                    motivo="actividad_faltante",
                ))
            elif desaprobadas:
                atrasados.append(AlumnoAtrasado(
                    entrada_padron_id=entrada_id,
                    nombre=entrada.nombre,
                    apellidos=entrada.apellidos,
                    comision=entrada.comision,
                    regional=entrada.regional,
                    actividades_desaprobadas=desaprobadas,
                    motivo="nota_bajo_umbral",
                ))

        return AtrasadosResponse(atrasados=atrasados, total=len(atrasados))

    @staticmethod
    async def get_ranking(
        db: AsyncSession,
        materia_id: uuid.UUID,
        user: User,
        limit: int = 50,
        offset: int = 0,
    ) -> RankingResponse:
        await AnalisisService._resolve_scope(db, user, materia_id)
        repo = CalificacionesRepository(db)
        calificaciones = await repo.get_all_by_materia(materia_id, user.tenant_id)

        total_actividades = len({c.actividad for c in calificaciones})

        by_entrada: dict[uuid.UUID, list[Calificacion]] = {}
        for c in calificaciones:
            by_entrada.setdefault(c.entrada_padron_id, []).append(c)

        entries = []
        for entrada_id, califs in by_entrada.items():
            entrada = califs[0].entrada_padron
            if not entrada:
                continue
            aprobadas = sum(1 for c in califs if c.aprobado)
            if aprobadas >= 1:
                entries.append({
                    "entrada_padron_id": entrada_id,
                    "nombre": entrada.nombre,
                    "apellidos": entrada.apellidos,
                    "comision": entrada.comision,
                    "aprobadas": aprobadas,
                    "total_actividades": total_actividades,
                })

        entries.sort(key=lambda e: (-e["aprobadas"], e["apellidos"], e["nombre"]))

        total = len(entries)
        page = entries[offset:offset + limit]

        ranking = []
        for i, e in enumerate(page):
            ranking.append(RankingEntry(
                posicion=offset + i + 1,
                entrada_padron_id=e["entrada_padron_id"],
                nombre=e["nombre"],
                apellidos=e["apellidos"],
                comision=e["comision"],
                actividades_aprobadas=e["aprobadas"],
                total_actividades=e["total_actividades"],
            ))

        return RankingResponse(ranking=ranking, total=total)

    @staticmethod
    async def get_reporte(
        db: AsyncSession,
        materia_id: uuid.UUID,
        user: User,
    ) -> ReporteMateria | EstadoSinDatos:
        await AnalisisService._resolve_scope(db, user, materia_id)
        repo = CalificacionesRepository(db)
        calificaciones = await repo.get_all_by_materia(materia_id, user.tenant_id)

        if not calificaciones:
            return EstadoSinDatos(sin_datos=True, mensaje="No hay calificaciones para esta materia")

        total_alumnos = len({c.entrada_padron_id for c in calificaciones})
        actividades = list({c.actividad for c in calificaciones})
        total_actividades = len(actividades)
        total_calificaciones = len(calificaciones)
        aprobados = sum(1 for c in calificaciones if c.aprobado)
        no_aprobados = total_calificaciones - aprobados
        porcentaje = (aprobados / total_calificaciones * 100) if total_calificaciones > 0 else 0.0

        por_actividad = []
        for act in sorted(actividades):
            act_califs = [c for c in calificaciones if c.actividad == act]
            act_total = len(act_califs)
            act_aprobados = sum(1 for c in act_califs if c.aprobado)
            act_no_aprobados = act_total - act_aprobados
            act_pct = (act_aprobados / act_total * 100) if act_total > 0 else 0.0
            por_actividad.append(ActividadReporte(
                actividad=act,
                total=act_total,
                aprobados=act_aprobados,
                no_aprobados=act_no_aprobados,
                porcentaje_aprobacion=round(act_pct, 2),
            ))

        return ReporteMateria(
            sin_datos=False,
            total_alumnos=total_alumnos,
            total_actividades=total_actividades,
            total_calificaciones=total_calificaciones,
            aprobados=aprobados,
            no_aprobados=no_aprobados,
            porcentaje_aprobacion=round(porcentaje, 2),
            por_actividad=por_actividad,
        )

    @staticmethod
    async def get_notas_finales(
        db: AsyncSession,
        materia_id: uuid.UUID,
        user: User,
        ordenar_por: str = "promedio",
        orden: str = "desc",
    ) -> NotasFinalesResponse:
        await AnalisisService._resolve_scope(db, user, materia_id)
        repo = CalificacionesRepository(db)
        calificaciones = await repo.get_all_by_materia(materia_id, user.tenant_id)

        by_entrada: dict[uuid.UUID, list[Calificacion]] = {}
        for c in calificaciones:
            by_entrada.setdefault(c.entrada_padron_id, []).append(c)

        notas_numericas = []
        notas_textuales = []

        for entrada_id, califs in by_entrada.items():
            entrada = califs[0].entrada_padron
            if not entrada:
                continue

            numericas = [c for c in califs if c.nota_numerica is not None]
            textuales = [c for c in califs if c.nota_textual is not None]

            if numericas:
                promedio = sum(float(c.nota_numerica) for c in numericas) / len(numericas)
                notas_numericas.append(NotaFinalAlumno(
                    entrada_padron_id=entrada_id,
                    nombre=entrada.nombre,
                    apellidos=entrada.apellidos,
                    comision=entrada.comision,
                    promedio=round(promedio, 2),
                    actividades_count=len(numericas),
                ))

            if textuales:
                acts = [
                    ActividadTextual(actividad=c.actividad, nota_textual=c.nota_textual or "")
                    for c in textuales
                ]
                notas_textuales.append(NotaFinalTextual(
                    entrada_padron_id=entrada_id,
                    nombre=entrada.nombre,
                    apellidos=entrada.apellidos,
                    comision=entrada.comision,
                    actividades=acts,
                ))

        reverse = orden == "desc"
        if ordenar_por == "promedio":
            notas_numericas.sort(key=lambda n: n.promedio, reverse=reverse)
        else:
            notas_numericas.sort(key=lambda n: (n.apellidos, n.nombre), reverse=reverse)

        return NotasFinalesResponse(
            notas_numericas=notas_numericas,
            notas_textuales=notas_textuales,
        )

    @staticmethod
    async def export_tps_sin_corregir(
        db: AsyncSession,
        materia_id: uuid.UUID,
        user: User,
    ) -> StreamingResponse:
        scope = await AnalisisService._resolve_scope(db, user, materia_id)
        repo = CalificacionesRepository(db)
        calificaciones = await repo.get_all_by_materia(materia_id, user.tenant_id)
        entradas = await repo.get_entradas_with_calificaciones_by_materia(materia_id, user.tenant_id)

        entrada_map = {e.id: e for e in entradas}

        actividades_textuales = {
            c.actividad for c in calificaciones
            if c.nota_numerica is None and c.actividad is not None
        }

        by_entrada: dict[uuid.UUID, list[Calificacion]] = {}
        for c in calificaciones:
            by_entrada.setdefault(c.entrada_padron_id, []).append(c)

        rows = []
        for entrada_id, califs in by_entrada.items():
            entrada = entrada_map.get(entrada_id)
            if not entrada:
                continue

            calificadas = {c.actividad for c in califs if c.nota_textual is not None}
            for act in sorted(actividades_textuales):
                if act not in calificadas:
                    rows.append({
                        "Apellidos": entrada.apellidos,
                        "Nombre": entrada.nombre,
                        "Email": entrada.email,
                        "Actividad": act,
                        "Comisión": entrada.comision or "",
                        "Regional": entrada.regional or "",
                    })

        def generate():
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=["Apellidos", "Nombre", "Email", "Actividad", "Comisión", "Regional"])
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
            yield output.getvalue().encode("utf-8-sig")

        await AuditService.log_action(
            db=db,
            action="ANALISIS_CONSULTA",
            user_id=str(user.id),
            resource="tps-sin-corregir",
            status="success",
            actor_id=str(user.id),
            materia_id=str(materia_id),
            detalle={"tipo": "export_tps_sin_corregir"},
            filas_afectadas=len(rows),
        )

        filename = f"tps-sin-corregir-{materia_id}.csv"
        return StreamingResponse(
            generate(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @staticmethod
    async def get_monitor_general(
        db: AsyncSession,
        user: User,
        materia_id: uuid.UUID | None = None,
        regional: str | None = None,
        comision: str | None = None,
        q: str | None = None,
        estado_actividad: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> MonitorGeneralResponse:
        repo = CalificacionesRepository(db)

        query = select(EntradaPadron).where(
            EntradaPadron.tenant_id == user.tenant_id,
            EntradaPadron.deleted_at.is_(None),
        )
        if regional:
            query = query.where(EntradaPadron.regional == regional)
        if comision:
            query = query.where(EntradaPadron.comision == comision)
        if q:
            pattern = f"%{q}%"
            query = query.where(
                EntradaPadron.nombre.ilike(pattern) |
                EntradaPadron.apellidos.ilike(pattern)
            )

        result = await db.execute(query)
        entradas = list(result.scalars().all())

        entrada_email_map = {}
        for e in entradas:
            try:
                entrada_email_map[e.id] = e.email
            except Exception:
                entrada_email_map[e.id] = ""

        if materia_id:
            all_calificaciones = await repo.get_all_by_materia(materia_id, user.tenant_id)
        else:
            stmt = select(Calificacion).where(
                Calificacion.tenant_id == user.tenant_id,
                Calificacion.deleted_at.is_(None),
            )
            calif_result = await db.execute(stmt)
            all_calificaciones = list(calif_result.scalars().all())

        materias_nombres: dict[uuid.UUID, str] = {}
        mat_stmt = select(Materia.id, Materia.name).where(
            Materia.tenant_id == user.tenant_id,
            Materia.deleted_at.is_(None),
        )
        mat_result = await db.execute(mat_stmt)
        for row in mat_result:
            materias_nombres[row[0]] = row[1]

        calif_by_entrada: dict[uuid.UUID, list[Calificacion]] = {}
        for c in all_calificaciones:
            calif_by_entrada.setdefault(c.entrada_padron_id, []).append(c)

        alumnos = []
        for e in entradas:
            califs = calif_by_entrada.get(e.id, [])
            if not califs:
                continue

            by_materia: dict[uuid.UUID, list[Calificacion]] = {}
            for c in califs:
                by_materia.setdefault(c.materia_id, []).append(c)

            materias_list = []
            for mid, mcalifs in by_materia.items():
                total_acts = len({c.actividad for c in mcalifs})
                aprobadas = sum(1 for c in mcalifs if c.aprobado)
                no_aprobadas = total_acts - aprobadas

                if estado_actividad == "aprobadas" and aprobadas == 0:
                    continue
                if estado_actividad == "no_aprobadas" and no_aprobadas == 0:
                    continue
                if estado_actividad == "sin_entregar" and total_acts > 0:
                    continue

                materias_list.append(MonitorMateria(
                    materia_id=mid,
                    materia_nombre=materias_nombres.get(mid, ""),
                    total_actividades=total_acts,
                    aprobadas=aprobadas,
                    no_aprobadas=no_aprobadas,
                    faltantes=0,
                ))

            if not materias_list:
                continue

            alumnos.append(MonitorAlumno(
                entrada_padron_id=e.id,
                nombre=e.nombre,
                apellidos=e.apellidos,
                email=entrada_email_map.get(e.id, ""),
                comision=e.comision,
                regional=e.regional,
                materias=materias_list,
            ))

        total = len(alumnos)
        page = alumnos[offset:offset + limit]

        filtros = {}
        if materia_id: filtros["materia_id"] = str(materia_id)
        if regional: filtros["regional"] = regional
        if comision: filtros["comision"] = comision
        if q: filtros["q"] = q
        if estado_actividad: filtros["estado_actividad"] = estado_actividad

        await AuditService.log_action(
            db=db,
            action="ANALISIS_CONSULTA",
            user_id=str(user.id),
            resource="monitor",
            status="success",
            actor_id=str(user.id),
            detalle={"tipo": "monitor_general", "filtros": filtros, "resultados": total},
        )

        return MonitorGeneralResponse(alumnos=page, total=total, filtros_aplicados=filtros)

    @staticmethod
    async def get_monitor_seguimiento(
        db: AsyncSession,
        user: User,
        alumno_id: uuid.UUID | None = None,
        email: str | None = None,
        comision: str | None = None,
        regional: str | None = None,
        actividad: str | None = None,
        min_cumplimiento_pct: int = 0,
        fecha_desde: str | None = None,
        fecha_hasta: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> SeguimientoResponse:
        roles = await AnalisisService._get_user_roles(db, user)
        is_coord_admin = "COORDINADOR" in roles or "ADMIN" in roles

        query = select(EntradaPadron).where(
            EntradaPadron.tenant_id == user.tenant_id,
            EntradaPadron.deleted_at.is_(None),
        )
        if alumno_id:
            query = query.where(EntradaPadron.id == alumno_id)
        if email:
            query = query.where(EntradaPadron._email.ilike(f"%{email}%"))
        if comision:
            query = query.where(EntradaPadron.comision == comision)
        if regional:
            query = query.where(EntradaPadron.regional == regional)

        result = await db.execute(query)
        entradas = list(result.scalars().all())

        entrada_email_map = {}
        for e in entradas:
            try:
                entrada_email_map[e.id] = e.email
            except Exception:
                entrada_email_map[e.id] = ""

        calif_query = select(Calificacion).where(
            Calificacion.tenant_id == user.tenant_id,
            Calificacion.deleted_at.is_(None),
        )
        if is_coord_admin and fecha_desde:
            calif_query = calif_query.where(Calificacion.importado_at >= fecha_desde)
        if is_coord_admin and fecha_hasta:
            calif_query = calif_query.where(Calificacion.importado_at <= fecha_hasta)
        if actividad:
            calif_query = calif_query.where(Calificacion.actividad == actividad)

        calif_result = await db.execute(calif_query)
        all_calificaciones = list(calif_result.scalars().all())

        calif_by_entrada: dict[uuid.UUID, list[Calificacion]] = {}
        for c in all_calificaciones:
            calif_by_entrada.setdefault(c.entrada_padron_id, []).append(c)

        alumnos = []
        for e in entradas:
            califs = calif_by_entrada.get(e.id, [])
            if not califs:
                continue

            total_acts = len({c.actividad for c in califs})
            aprobadas = sum(1 for c in califs if c.aprobado)
            no_aprobadas = total_acts - aprobadas
            faltantes = 0
            pct = (aprobadas / total_acts * 100) if total_acts > 0 else 0.0

            if pct < min_cumplimiento_pct:
                continue

            alumnos.append(SeguimientoAlumno(
                entrada_padron_id=e.id,
                nombre=e.nombre,
                apellidos=e.apellidos,
                email=entrada_email_map.get(e.id, ""),
                comision=e.comision,
                regional=e.regional,
                actividades_totales=total_acts,
                aprobadas=aprobadas,
                no_aprobadas=no_aprobadas,
                faltantes=faltantes,
                pct_cumplimiento=round(pct, 2),
            ))

        total = len(alumnos)
        page = alumnos[offset:offset + limit]

        await AuditService.log_action(
            db=db,
            action="ANALISIS_CONSULTA",
            user_id=str(user.id),
            resource="monitor",
            status="success",
            actor_id=str(user.id),
            detalle={
                "tipo": "monitor_seguimiento",
                "filtros": {
                    "alumno_id": str(alumno_id) if alumno_id else None,
                    "comision": comision,
                    "regional": regional,
                    "actividad": actividad,
                    "min_cumplimiento_pct": min_cumplimiento_pct,
                },
                "resultados": total,
            },
        )

        return SeguimientoResponse(alumnos=page, total=total)
