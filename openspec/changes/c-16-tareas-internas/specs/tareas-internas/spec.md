# tareas-internas — Specification

## ADDED Requirements

### Requirement: ABM Tareas with Assignment

WHEN a user with permission `tareas:crear` creates, edits, or deletes a tarea,
the system SHALL manage Tarea records with the specified assignment configuration.

#### Scenario: Create Tarea as Coordinador
GIVEN a user with role COORDINADOR and permission `tareas:crear`
WHEN the user creates a Tarea with:
  - `materia_id` = a valid materia UUID
  - `asignado_a` = a valid usuario UUID
  - `descripcion` = "Revisar planificaciones del módulo 3"
  - `contexto_id` = null
THEN the system SHALL create a Tarea record
AND the record SHALL have `estado` = "Pendiente"
AND the record SHALL have `tenant_id` matching the user's tenant
AND the record SHALL have `asignado_por` matching the authenticated user's ID
AND the record SHALL have the provided materia_id, asignado_a, descripcion

#### Scenario: Create Tarea without materia (institutional level)
GIVEN a user with permission `tareas:crear`
WHEN the user creates a Tarea with `materia_id` = null
THEN the system SHALL create the Tarea record
AND the record SHALL have `materia_id` = null

#### Scenario: Edit Tarea
GIVEN an existing Tarea record
WHEN a user with permission `tareas:crear` edits the tarea
THEN the system SHALL update the specified fields
AND the `updated_at` timestamp SHALL be refreshed

#### Scenario: Delete Tarea (Soft)
GIVEN an existing Tarea record
WHEN a user with permission `tareas:gestionar` deletes the tarea
THEN the system SHALL set `deleted_at` to the current timestamp
AND the tarea SHALL NOT appear in any queries

---

### Requirement: Delegación de Tarea

WHEN a user with permission `tareas:crear` reassigns a tarea to another user,
the system SHALL update the `asignado_a` field and record the change.

#### Scenario: Delegar Tarea a Otro Docente
GIVEN an existing Tarea assigned to usuario A
WHEN a user with permission `tareas:crear` updates `asignado_a` to usuario B
THEN the system SHALL update `asignado_a` to usuario B
AND the system SHALL keep `asignado_por` as the original assigner
AND the `updated_at` timestamp SHALL be refreshed

#### Scenario: Cannot Delegate Without Permission
GIVEN a user WITHOUT permission `tareas:crear`
WHEN the user attempts to update `asignado_a`
THEN the system SHALL return a 403 Forbidden response

---

### Requirement: Visualización de Mis Tareas (F8.1)

WHEN a user with permission `tareas:ver` views their assigned tareas,
the system SHALL return only tareas where `asignado_a` matches the authenticated user.

#### Scenario: Docente Ve Sus Tareas Asignadas
GIVEN tareas assigned to the authenticated user and tareas assigned to other users
WHEN the user accesses `mis-tareas`
THEN the system SHALL return only tareas where `asignado_a` = authenticated user's ID
AND each tarea SHALL include id, descripcion, estado, materia_id, asignado_por, asignado_a, created_at, updated_at

#### Scenario: Docente Sin Tareas Ve Lista Vacía
GIVEN no tareas assigned to the authenticated user
WHEN the user accesses `mis-tareas`
THEN the system SHALL return an empty list

#### Scenario: Cannot View Without Permission
GIVEN a user WITHOUT permission `tareas:ver`
WHEN the user accesses `mis-tareas`
THEN the system SHALL return a 403 Forbidden response

---

### Requirement: Administración Global de Tareas (F8.3)

WHEN a user with permission `tareas:gestionar` views all tareas,
the system SHALL return all tareas in the tenant with optional filters.

#### Scenario: Coordinador Ve Todas Las Tareas del Tenant
GIVEN a user with role COORDINADOR and permission `tareas:gestionar`
WHEN the user accesses the admin list endpoint
THEN the system SHALL return all tareas in the tenant
AND results SHALL NOT be filtered by `asignado_a`

#### Scenario: Filtrar por Estado
GIVEN tareas with various estados
WHEN the user filters by `estado` = "En progreso"
THEN the system SHALL return only tareas with estado "En progreso"

#### Scenario: Filtrar por Docente Asignado
GIVEN tareas assigned to various usuarios
WHEN the user filters by `asignado_a` = usuario_uuid
THEN the system SHALL return only tareas assigned to that usuario

#### Scenario: Filtrar por Materia
GIVEN tareas associated with various materias
WHEN the user filters by `materia_id` = materia_uuid
THEN the system SHALL return only tareas for that materia

#### Scenario: Paginación en Admin List
GIVEN more tareas than the page size
WHEN the user accesses the admin list with `offset` and `limit`
THEN the system SHALL return the requested page
AND the response SHALL include a total count

#### Scenario: Cannot Admin Without Permission
GIVEN a user WITHOUT permission `tareas:gestionar`
WHEN the user accesses the admin list
THEN the system SHALL return a 403 Forbidden response

---

### Requirement: Transiciones de Estado

WHEN a user with appropriate permission updates the estado of a tarea,
the system SHALL validate the transition and apply the change.

#### Scenario: Pendiente → En Progreso (Docente)
GIVEN a Tarea with estado "Pendiente" assigned to the authenticated user
WHEN the user updates estado to "En progreso"
THEN the system SHALL accept the transition
AND the record SHALL have estado = "En progreso"

#### Scenario: En Progreso → Resuelta (Docente)
GIVEN a Tarea with estado "En progreso" assigned to the authenticated user
WHEN the user updates estado to "Resuelta"
THEN the system SHALL accept the transition

#### Scenario: Cualquier Estado → Cancelada (Coordinador)
GIVEN a Tarea in any estado
WHEN a user with permission `tareas:gestionar` updates estado to "Cancelada"
THEN the system SHALL accept the transition

#### Scenario: Docente No Puede Cancelar
GIVEN a Tarea assigned to the authenticated user
WHEN the user (without `tareas:gestionar`) attempts to update estado to "Cancelada"
THEN the system SHALL return a 403 Forbidden response

---

### Requirement: Comentarios en Tareas

WHEN a user adds a comment to a tarea,
the system SHALL create a ComentarioTarea record associated with the tarea.

#### Scenario: Agregar Comentario
GIVEN an existing Tarea
WHEN any user with permission `tareas:ver` adds a comment with text
THEN the system SHALL create a ComentarioTarea record
AND the record SHALL have `tarea_id` matching the tarea
AND the record SHALL have `autor_id` matching the authenticated user
AND the record SHALL have `texto` with the provided text
AND the record SHALL have `creado_at` set to the current datetime

#### Scenario: Listar Comentarios de una Tarea
GIVEN a Tarea with 3 comments
WHEN a user with permission `tareas:ver` lists comments for the tarea
THEN the system SHALL return all 3 comments ordered by `creado_at` ascending
AND each comment SHALL include id, texto, autor_id, creado_at

#### Scenario: Cannot Comment on Non-Existent Tarea
GIVEN a tarea_id that does not exist
WHEN a user attempts to add a comment
THEN the system SHALL return a 404 Not Found response

#### Scenario: Soft-Delete Comentario
GIVEN an existing ComentarioTarea record
WHEN a user with permission `tareas:gestionar` deletes the comment
THEN the system SHALL set `deleted_at` to the current timestamp
AND the comment SHALL NOT appear in any queries

---

### Requirement: Permission Enforcement

WHEN a user accesses tareas endpoints,
the system SHALL enforce the corresponding permission.

#### Scenario: `tareas:crear` for PROFESOR and COORDINADOR
GIVEN a user with role PROFESOR or COORDINADOR and assigned permission `tareas:crear`
WHEN the user accesses create or edit endpoints
THEN the system SHALL allow the action

#### Scenario: `tareas:ver` for TUTOR, PROFESOR, COORDINADOR
GIVEN a user with permission `tareas:ver`
WHEN the user lists mis-tareas or reads a tarea detail
THEN the system SHALL return tareas scoped to the user's assignment context

#### Scenario: `tareas:gestionar` for COORDINADOR and ADMIN
GIVEN a user with permission `tareas:gestionar`
WHEN the user accesses admin endpoints (list all, change any estado, delete)
THEN the system SHALL allow the action

#### Scenario: Without Permission — 403
GIVEN a user WITHOUT the required permission
WHEN the user accesses a protected tareas endpoint
THEN the system SHALL return a 403 Forbidden response

---

### Requirement: Audit Trail

WHEN a tarea action is performed,
the system SHALL record the action in the audit log.

#### Scenario: Tarea Created
GIVEN a successful tarea creation
WHEN the action completes
THEN the system SHALL call AuditService.log_action
AND the action SHALL be `TAREA_CREAR`
AND the detalle SHALL include tarea_id, asignado_a, materia_id, descripcion

#### Scenario: Tarea Estado Updated
GIVEN a successful estado change
WHEN the action completes
THEN the system SHALL call AuditService.log_action
AND the action SHALL be `TAREA_ACTUALIZAR_ESTADO`
AND the detalle SHALL include tarea_id, estado_anterior, estado_nuevo

#### Scenario: Tarea Delegated
GIVEN a successful delegation (asignado_a changed)
WHEN the action completes
THEN the system SHALL call AuditService.log_action
AND the action SHALL be `TAREA_DELEGAR`
AND the detalle SHALL include tarea_id, asignado_anterior, asignado_nuevo

#### Scenario: Tarea Deleted
GIVEN a successful tarea soft-delete
WHEN the action completes
THEN the system SHALL call AuditService.log_action
AND the action SHALL be `TAREA_ELIMINAR`
AND the detalle SHALL include tarea_id

#### Scenario: Comentario Added
GIVEN a successful comment creation
WHEN the action completes
THEN the system SHALL call AuditService.log_action
AND the action SHALL be `TAREA_COMENTAR`
AND the detalle SHALL include tarea_id, comentario_id
