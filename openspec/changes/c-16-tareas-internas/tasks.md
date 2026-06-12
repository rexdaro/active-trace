## 1. Migration & Seed

- [x] 1.1 Create migration `1e2f3c4d5e6f_add_tareas_y_comentarios.py` with tables `tareas` and `comentarios_tarea`, including FK constraints, UUID PKs, tenant isolation, soft-delete columns, and unique constraints
- [x] 1.2 Add permissions `tareas:crear`, `tareas:ver`, `tareas:gestionar` to `app/db/seed.py` with their role assignments:
  - `tareas:crear` → PROFESOR, COORDINADOR
  - `tareas:ver` → TUTOR, PROFESOR, COORDINADOR
  - `tareas:gestionar` → COORDINADOR, ADMIN

## 2. Model Layer

- [x] 2.1 Create `app/models/tarea.py` with `EstadoTarea` enum (Pendiente, En progreso, Resuelta, Cancelada) and `Tarea` model inheriting `Base, TimestampMixin, TenantMixin`, with fields: id, materia_id (nullable FK), asignado_a (FK usuario), asignado_por (FK usuario), estado (default Pendiente), descripcion, contexto_id (nullable UUID)
- [x] 2.2 Create `ComentarioTarea` model in `app/models/tarea.py` with fields: id, tenant_id, tarea_id (FK CASCADE), autor_id (FK usuario), texto, creado_at
- [x] 2.3 Register `Tarea` and `ComentarioTarea` in `app/models/__init__.py`

## 3. Schema Layer

- [x] 3.1 Create `app/schemas/tarea.py` with:
  - `TareaCreate` (materia_id, asignado_a, descripcion, contexto_id)
  - `TareaUpdate` (all Optional: materia_id, asignado_a, descripcion, estado, contexto_id)
  - `TareaEstadoUpdate` (estado only — for status transitions)
  - `TareaResponse` (all fields + created_at, updated_at, with `ConfigDict(from_attributes=True)`)
  - `TareaListParams` (estado, asignado_a, materia_id, search query params)
  - `ComentarioTareaCreate` (texto)
  - `ComentarioTareaResponse` (id, tarea_id, autor_id, texto, creado_at)

## 4. Repository Layer

- [x] 4.1 Create `app/repositories/tareas.py` with `TareaRepository` class:
  - `create(data, tenant_id) → Tarea`
  - `get(id, tenant_id) → Tarea | None`
  - `update(db_obj, data) → Tarea`
  - `delete(id, tenant_id)` (soft-delete via deleted_at)
  - `list_by_asignado(asignado_a, tenant_id, offset, limit) → tuple[list[Tarea], int]`
  - `list_all(tenant_id, params: TareaListParams, offset, limit) → tuple[list[Tarea], int]`
  - `count_by_asignado(asignado_a, tenant_id) → int`

- [x] 4.2 Add `ComentarioTareaRepository` methods (or same class):
  - `create_comentario(data, tenant_id) → ComentarioTarea`
  - `list_comentarios(tarea_id, tenant_id) → list[ComentarioTarea]`
  - `get_comentario(id, tenant_id) → ComentarioTarea | None`
  - `delete_comentario(id, tenant_id)` (soft-delete)

## 5. Service Layer

- [x] 5.1 Create `app/services/tareas.py` with `TareaService` class (all @staticmethod):
  - `create(db, obj_in, usuario_actual) → Tarea` — validates materia exists if provided, validates asignado_a user exists, sets asignado_por from session, audits TAREA_CREAR
  - `update(db, id, obj_in, usuario_actual) → Tarea` — validates permissions for estado changes, audits TAREA_ACTUALIZAR_ESTADO or TAREA_DELEGAR
  - `delete(db, id, usuario_actual) → None` — soft-delete, audits TAREA_ELIMINAR
  - `get(db, id, usuario_actual) → Tarea` — 404 if not found
  - `list_mis_tareas(db, usuario_actual, offset, limit) → tuple[list[Tarea], int]`
  - `list_all_tareas(db, usuario_actual, params, offset, limit) → tuple[list[Tarea], int]`
  - `add_comentario(db, tarea_id, obj_in, usuario_actual) → ComentarioTarea` — validates tarea exists, audits TAREA_COMENTAR
  - `list_comentarios(db, tarea_id, usuario_actual) → list[ComentarioTarea]`
  - `delete_comentario(db, tarea_id, comentario_id, usuario_actual) → None`

## 6. Router Layer

- [x] 6.1 Create `app/routers/tareas.py` with `APIRouter(prefix="/api/v1/tareas", tags=["Tareas"])`:
  - `POST /` — crear tarea (permiso `tareas:crear`) → 201
  - `PUT /{tarea_id}` — actualizar tarea (permiso `tareas:crear`)
  - `PUT /{tarea_id}/estado` — cambiar estado (permiso `tareas:ver`)
  - `DELETE /{tarea_id}` — eliminar tarea (permiso `tareas:gestionar`) → 204
  - `GET /{tarea_id}` — obtener tarea (permiso `tareas:ver`)
  - `GET /mis-tareas` — mis tareas (permiso `tareas:ver`)
  - `GET /admin` — lista global (permiso `tareas:gestionar`)
  - `POST /{tarea_id}/comentarios` — agregar comentario (permiso `tareas:ver`)
  - `GET /{tarea_id}/comentarios` — listar comentarios (permiso `tareas:ver`)
  - `DELETE /{tarea_id}/comentarios/{comentario_id}` — eliminar comentario (permiso `tareas:gestionar`) → 204

- [x] 6.2 Register the tareas router in the main FastAPI app (app/main.py)

## 7. Tests — Model

- [x] 7.1 Create `tests/test_tarea_model.py` with:
  - `TestEstadoTarea` — enum values
  - `TestTareaModel` — create with defaults, create with all fields, nullable materia_id, FK to usuario for asignado_a and users for asignado_por, soft-delete via TimestampMixin, tenant isolation
  - `TestComentarioTareaModel` — create with all fields, FK cascade from tarea delete, soft-delete

## 8. Tests — Repository

- [x] 8.1 Create `tests/test_tarea_repo.py` with:
  - `TestTareaRepo` — create, get, update, delete (soft), list_by_asignado, list_all with filters (estado, asignado_a, materia_id), pagination, tenant isolation
  - `TestComentarioTareaRepo` — create_comentario, list_comentarios, get_comentario, delete_comentario

## 9. Tests — Service

- [x] 9.1 Create `tests/test_tarea_service.py` with:
  - Create tarea as COORDINADOR — success
  - Create tarea with materia — success
  - Create tarea with invalid materia — 404
  - Create tarea with invalid asignado_a user — 404
  - Audit log on create
  - Update tarea estado as docente (Pendiente → En progreso) — success
  - Update tarea estado as docente (En progreso → Resuelta) — success
  - Update tarea estado as docente to Cancelada — 403
  - Update tarea estado as COORDINADOR to Cancelada — success
  - Delegar tarea (update asignado_a) — success
  - Update tarea not found — 404
  - Audit log on estado change
  - Audit log on delegación
  - Soft-delete tarea — hidden from list
  - Delete audit log
  - Delete not found — 404
  - Get tarea — success
  - Get tarea not found — 404
  - List mis tareas empty
  - Add comentario — success
  - Add comentario to non-existent tarea — 404
  - List comentarios — ordered by created_at asc
  - Delete comentario

## 10. Tests — Router

- [x] 10.1 Create `tests/test_tareas_router.py` with:
  - `TestTareasRouterSinAuth` — all 10 endpoints return 401
  - `TestTareasRouterPermisos` (BaseRouterTest subclass) — permission checks for each endpoint
  - `TestTareasRouterIntegration` — full integration flow: create → list → add comentario → change estado → delete
