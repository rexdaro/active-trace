## 1. Migration

- [x] 1.1 Create migration `2a3b4c5d6e7f_add_programa_materia_y_fecha_academica.py` with tables `programa_materia` and `fecha_academica` including FK constraints (materias, carreras, cohortes), UUID PKs, tenant isolation, soft-delete columns, and `tipo_fecha` enum type

## 2. Model Layer

- [x] 2.1 Create `app/models/programa_materia.py` with `ProgramaMateria` model inheriting `Base, TimestampMixin, TenantMixin`, with fields: id (UUID PK), materia_id (FK materias), carrera_id (FK carreras), cohorte_id (FK cohortes), titulo (String), referencia_archivo (String, nullable), cargado_at (DateTime, server_default now)
- [x] 2.2 Create `app/models/fecha_academica.py` with `TipoFecha` enum (Parcial, TP, Coloquio, Recuperatorio) and `FechaAcademica` model inheriting `Base, TimestampMixin, TenantMixin`, with fields: id (UUID PK), materia_id (FK materias), cohorte_id (FK cohortes), tipo (String), numero (Integer), periodo (String), fecha (Date), titulo (String)
- [x] 2.3 Register `ProgramaMateria`, `FechaAcademica` and `TipoFecha` in `app/models/__init__.py`

## 3. Schema Layer

- [x] 3.1 Create `app/schemas/programa_materia.py` with:
  - `ProgramaMateriaCreate` (materia_id, carrera_id, cohorte_id, titulo, referencia_archivo opcional)
  - `ProgramaMateriaUpdate` (all Optional: titulo, referencia_archivo)
  - `ProgramaMateriaRead` (all fields + timestamps, with `ConfigDict(from_attributes=True)`)
  - `ProgramaMateriaListParams` (materia_id, carrera_id, cohorte_id query params)

- [x] 3.2 Create `app/schemas/fecha_academica.py` with:
  - `FechaAcademicaCreate` (materia_id, cohorte_id, tipo from TipoFecha, numero, periodo, fecha, titulo)
  - `FechaAcademicaUpdate` (all Optional: tipo, numero, periodo, fecha, titulo)
  - `FechaAcademicaRead` (all fields + timestamps, with `ConfigDict(from_attributes=True)`)
  - `FechaAcademicaListParams` (materia_id, cohorte_id, tipo, periodo query params)

## 4. Repository Layer

- [x] 4.1 Create `app/repositories/programas_materia.py` with `ProgramaMateriaRepository` class:
  - `create(data, tenant_id) → ProgramaMateria`
  - `get(id, tenant_id) → ProgramaMateria | None`
  - `update(db_obj, data) → ProgramaMateria`
  - `delete(id, tenant_id)` (soft-delete)
  - `list(tenant_id, params: ProgramaMateriaListParams, offset, limit) → tuple[list[ProgramaMateria], int]`
  - `count(tenant_id) → int`

- [x] 4.2 Create `app/repositories/fechas_academicas.py` with `FechaAcademicaRepository` class:
  - `create(data, tenant_id) → FechaAcademica`
  - `get(id, tenant_id) → FechaAcademica | None`
  - `update(db_obj, data) → FechaAcademica`
  - `delete(id, tenant_id)` (soft-delete)
  - `list(tenant_id, params: FechaAcademicaListParams, offset, limit) → tuple[list[FechaAcademica], int]`
  - `list_html(tenant_id, materia_id, cohorte_id) → list[FechaAcademica]`

## 5. Service Layer

- [x] 5.1 Create `app/services/programas_materia.py` with `ProgramaMateriaService` class:
  - `create(db, obj_in, usuario_actual) → ProgramaMateria` — validates materia/carrera/cohorte exist in tenant
  - `get(db, id, usuario_actual) → ProgramaMateria` — 404 if not found or wrong tenant
  - `update(db, id, obj_in, usuario_actual) → ProgramaMateria`
  - `delete(db, id, usuario_actual) → None` — soft-delete
  - `list(db, usuario_actual, params, offset, limit) → tuple[list[ProgramaMateria], int]`

- [x] 5.2 Create `app/services/fechas_academicas.py` with `FechaAcademicaService` class:
  - `create(db, obj_in, usuario_actual) → FechaAcademica` — validates materia/cohorte exist in tenant
  - `get(db, id, usuario_actual) → FechaAcademica`
  - `update(db, id, obj_in, usuario_actual) → FechaAcademica`
  - `delete(db, id, usuario_actual) → None`
  - `list(db, usuario_actual, params, offset, limit) → tuple[list[FechaAcademica], int]`
  - `generate_html(db, id, usuario_actual) → str` — renders HTML fragment for LMS embedding

## 6. Router Layer

- [x] 6.1 Create `app/routers/programas.py` with `APIRouter(prefix="/api/v1/programas", tags=["Programas"])`:
  - `POST /` — crear programa (permiso `estructura:gestionar`) → 201
  - `GET /` — listar programas con filtros (permiso `estructura:gestionar`)
  - `GET /{programa_id}` — obtener programa (permiso `estructura:gestionar`)
  - `PUT /{programa_id}` — actualizar programa (permiso `estructura:gestionar`)
  - `DELETE /{programa_id}` — eliminar programa (permiso `estructura:gestionar`) → 204

- [x] 6.2 Create `app/routers/fechas_academicas.py` with `APIRouter(prefix="/api/v1/fechas-academicas", tags=["Fechas Académicas"])`:
  - `POST /` — crear fecha (permiso `estructura:gestionar`) → 201
  - `GET /` — listar fechas con filtros (permiso `estructura:gestionar`)
  - `GET /{fecha_id}` — obtener fecha (permiso `estructura:gestionar`)
  - `PUT /{fecha_id}` — actualizar fecha (permiso `estructura:gestionar`)
  - `DELETE /{fecha_id}` — eliminar fecha (permiso `estructura:gestionar`) → 204
  - `GET /{fecha_id}/html` — fragmento HTML embebible (permiso `estructura:gestionar`)

- [x] 6.3 Register both routers in `app/main.py`:
  - `from app.routers.programas import router as programas_router`
  - `from app.routers.fechas_academicas import router as fechas_academicas_router`
  - `app.include_router(programas_router)`
  - `app.include_router(fechas_academicas_router)`

## 7. Tests — Models

- [x] 7.1 Create `tests/test_programa_materia_model.py` with:
  - `TestProgramaMateriaModel` — create with defaults, create with all fields, FK to materia/carrera/cohorte, soft-delete, tenant isolation

- [x] 7.2 Create `tests/test_fecha_academica_model.py` with:
  - `TestTipoFechaEnum` — enum values
  - `TestFechaAcademicaModel` — create with defaults, create with all fields, FK to materia/cohorte, soft-delete, tenant isolation

## 8. Tests — Repositories

- [x] 8.1 Create `tests/test_programa_materia_repo.py` with:
  - `TestProgramaMateriaRepo` — create, get, get not found, update, delete (soft), list with filters (materia_id, carrera_id, cohorte_id), pagination, tenant isolation, soft-deleted hidden from list

- [x] 8.2 Create `tests/test_fecha_academica_repo.py` with:
  - `TestFechaAcademicaRepo` — create, get, get not found, update, delete (soft), list with filters (materia_id, cohorte_id, tipo, periodo), pagination, tenant isolation, soft-deleted hidden from list, list_html returns ordered by fecha asc

## 9. Tests — Services

- [x] 9.1 Create `tests/test_programa_materia_service.py` with:
  - Create programa — success
  - Create with invalid materia — 404
  - Create with invalid carrera — 404
  - Create with invalid cohorte — 404
  - Get programa — success
  - Get programa not found — 404
  - Update programa — success
  - Delete programa — soft-delete
  - Delete not found — 404
  - List with filters — success

- [x] 9.2 Create `tests/test_fecha_academica_service.py` with:
  - Create fecha — success
  - Create with invalid materia — 404
  - Create with invalid cohorte — 404
  - Get fecha — success
  - Get fecha not found — 404
  - Update fecha — success
  - Delete fecha — soft-delete
  - Delete not found — 404
  - List with filters — success
  - Generate HTML — returns string with table, ordered by fecha asc
  - Generate HTML for non-existent fecha — 404

## 10. Tests — Routers

- [x] 10.1 Create `tests/test_programas_router.py` with:
  - `TestProgramasRouterSinAuth` — all 5 endpoints return 401
  - `TestProgramasRouterPermisos` — permission checks (requires `estructura:gestionar`)
  - `TestProgramasRouterIntegration` — full integration flow: create → list → get → update → delete

- [x] 10.2 Create `tests/test_fechas_academicas_router.py` with:
  - `TestFechasRouterSinAuth` — all 6 endpoints return 401
  - `TestFechasRouterPermisos` — permission checks
  - `TestFechasRouterIntegration` — full integration flow: create → list → get → update → get HTML → delete
