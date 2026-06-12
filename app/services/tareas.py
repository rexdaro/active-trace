import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.tareas import TareaRepository
from app.models.tarea import Tarea, ComentarioTarea, EstadoTarea
from app.models.materia import Materia
from app.models.user import Usuario, User
from app.models.rbac import Role, Permission, RolePermission
from app.models.user_role import UserRole
from app.services.audit import AuditService
from app.schemas.tarea import (
    TareaCreate,
    TareaUpdate,
    TareaEstadoUpdate,
    TareaListParams,
    ComentarioTareaCreate,
)


class TareaService:

    @staticmethod
    async def create(
        db: AsyncSession,
        obj_in: TareaCreate,
        usuario_actual: User,
    ) -> Tarea:
        if obj_in.materia_id is not None:
            materia = await db.get(Materia, obj_in.materia_id)
            if not materia:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Materia no encontrada")

        usuario_asignado = await db.get(Usuario, obj_in.asignado_a)
        if not usuario_asignado:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Usuario asignado no encontrado")

        repo = TareaRepository(db)
        data = obj_in.model_dump()
        data["asignado_por"] = usuario_actual.id
        data["estado"] = EstadoTarea.PENDIENTE.value

        tarea = await repo.create(data, usuario_actual.tenant_id)
        await db.commit()

        await AuditService.log_action(
            db=db,
            action="TAREA_CREAR",
            user_id=str(usuario_actual.id),
            resource="tareas",
            status="success",
            actor_id=str(usuario_actual.id),
            detalle={
                "tarea_id": str(tarea.id),
                "asignado_a": str(obj_in.asignado_a),
                "materia_id": str(obj_in.materia_id) if obj_in.materia_id else None,
                "descripcion": obj_in.descripcion,
            },
        )

        return tarea

    @staticmethod
    async def update(
        db: AsyncSession,
        id: uuid.UUID,
        obj_in: TareaUpdate | TareaEstadoUpdate,
        usuario_actual: User,
    ) -> Tarea:
        repo = TareaRepository(db)
        tarea = await repo.get(id, usuario_actual.tenant_id)
        if not tarea:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")

        data = obj_in.model_dump(exclude_unset=True)

        # Check if this is an estado change
        estado_anterior = tarea.estado
        if "estado" in data and data["estado"] is not None:
            nuevo_estado = data["estado"].value if hasattr(data["estado"], "value") else data["estado"]
            data["estado"] = nuevo_estado

            # Permission check for estado transitions
            if nuevo_estado == EstadoTarea.CANCELADA.value:
                # Only tareas:gestionar can cancel
                has_gestionar = await TareaService._user_has_permission(db, usuario_actual, "tareas:gestionar")
                if not has_gestionar:
                    raise HTTPException(status.HTTP_403_FORBIDDEN, detail="No tienes permiso para cancelar tareas")

            # Check if asignado_a is being changed (delegation)
            if "asignado_a" in data and data["asignado_a"] is not None:
                nuevo_asignado = data["asignado_a"]
                usuario_val = await db.get(Usuario, nuevo_asignado)
                if not usuario_val:
                    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Usuario asignado no encontrado")

            updated = await repo.update(tarea, data)
            await db.commit()
            await db.refresh(updated)

            # Determine audit action
            if estado_anterior != updated.estado:
                await AuditService.log_action(
                    db=db,
                    action="TAREA_ACTUALIZAR_ESTADO",
                    user_id=str(usuario_actual.id),
                    resource="tareas",
                    status="success",
                    actor_id=str(usuario_actual.id),
                    detalle={
                        "tarea_id": str(id),
                        "estado_anterior": estado_anterior,
                        "estado_nuevo": updated.estado,
                    },
                )

            asignado_anterior = tarea.asignado_a
            if "asignado_a" in data and data["asignado_a"] is not None and data["asignado_a"] != asignado_anterior:
                await AuditService.log_action(
                    db=db,
                    action="TAREA_DELEGAR",
                    user_id=str(usuario_actual.id),
                    resource="tareas",
                    status="success",
                    actor_id=str(usuario_actual.id),
                    detalle={
                        "tarea_id": str(id),
                        "asignado_anterior": str(asignado_anterior),
                        "asignado_nuevo": str(data["asignado_a"]),
                    },
                )

            return updated

        # Handle asignado_a change for delegation (no estado change)
        if "asignado_a" in data and data["asignado_a"] is not None:
            nuevo_asignado = data["asignado_a"]
            usuario_val = await db.get(Usuario, nuevo_asignado)
            if not usuario_val:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Usuario asignado no encontrado")

            asignado_anterior = tarea.asignado_a
            updated = await repo.update(tarea, data)
            await db.commit()
            await db.refresh(updated)

            if updated.asignado_a != asignado_anterior:
                await AuditService.log_action(
                    db=db,
                    action="TAREA_DELEGAR",
                    user_id=str(usuario_actual.id),
                    resource="tareas",
                    status="success",
                    actor_id=str(usuario_actual.id),
                    detalle={
                        "tarea_id": str(id),
                        "asignado_anterior": str(asignado_anterior),
                        "asignado_nuevo": str(updated.asignado_a),
                    },
                )

            return updated

        # Regular update (no estado, no asignado_a change)
        updated = await repo.update(tarea, data)
        await db.commit()
        await db.refresh(updated)
        return updated

    @staticmethod
    async def delete(
        db: AsyncSession,
        id: uuid.UUID,
        usuario_actual: User,
    ) -> None:
        repo = TareaRepository(db)
        tarea = await repo.get(id, usuario_actual.tenant_id)
        if not tarea:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")

        await repo.delete(id, usuario_actual.tenant_id)
        await db.commit()

        await AuditService.log_action(
            db=db,
            action="TAREA_ELIMINAR",
            user_id=str(usuario_actual.id),
            resource="tareas",
            status="success",
            actor_id=str(usuario_actual.id),
            detalle={"tarea_id": str(id)},
        )

    @staticmethod
    async def get(
        db: AsyncSession,
        id: uuid.UUID,
        usuario_actual: User,
    ) -> Tarea:
        repo = TareaRepository(db)
        tarea = await repo.get(id, usuario_actual.tenant_id)
        if not tarea:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
        return tarea

    @staticmethod
    async def list_mis_tareas(
        db: AsyncSession,
        usuario_actual: User,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Tarea], int]:
        repo = TareaRepository(db)
        return await repo.list_by_asignado(usuario_actual.id, usuario_actual.tenant_id, offset, limit)

    @staticmethod
    async def list_all_tareas(
        db: AsyncSession,
        usuario_actual: User,
        params: TareaListParams | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Tarea], int]:
        repo = TareaRepository(db)
        params = params or TareaListParams()
        return await repo.list_all(usuario_actual.tenant_id, params, offset, limit)

    @staticmethod
    async def add_comentario(
        db: AsyncSession,
        tarea_id: uuid.UUID,
        obj_in: ComentarioTareaCreate,
        usuario_actual: User,
    ) -> ComentarioTarea:
        repo = TareaRepository(db)
        tarea = await repo.get(tarea_id, usuario_actual.tenant_id)
        if not tarea:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")

        comentario = await repo.create_comentario({
            "tarea_id": tarea_id,
            "autor_id": usuario_actual.id,
            "texto": obj_in.texto,
        }, usuario_actual.tenant_id)
        await db.commit()

        await AuditService.log_action(
            db=db,
            action="TAREA_COMENTAR",
            user_id=str(usuario_actual.id),
            resource="tareas",
            status="success",
            actor_id=str(usuario_actual.id),
            detalle={"tarea_id": str(tarea_id), "comentario_id": str(comentario.id)},
        )

        return comentario

    @staticmethod
    async def list_comentarios(
        db: AsyncSession,
        tarea_id: uuid.UUID,
        usuario_actual: User,
    ) -> list[ComentarioTarea]:
        repo = TareaRepository(db)
        tarea = await repo.get(tarea_id, usuario_actual.tenant_id)
        if not tarea:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
        return await repo.list_comentarios(tarea_id, usuario_actual.tenant_id)

    @staticmethod
    async def delete_comentario(
        db: AsyncSession,
        tarea_id: uuid.UUID,
        comentario_id: uuid.UUID,
        usuario_actual: User,
    ) -> None:
        repo = TareaRepository(db)
        tarea = await repo.get(tarea_id, usuario_actual.tenant_id)
        if not tarea:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")

        comentario = await repo.get_comentario(comentario_id, usuario_actual.tenant_id)
        if not comentario:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Comentario no encontrado")

        await repo.delete_comentario(comentario_id, usuario_actual.tenant_id)
        await db.commit()

    @staticmethod
    async def _user_has_permission(db: AsyncSession, user: User, permission_name: str) -> bool:
        stmt = (
            select(Permission.name)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user.id, Permission.name == permission_name)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None
