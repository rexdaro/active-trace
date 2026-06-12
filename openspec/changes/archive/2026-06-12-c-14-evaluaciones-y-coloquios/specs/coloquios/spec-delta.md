# evaluaciones-y-coloquios — Specification Delta

## ADDED Requirements

### Requirement: Crear Convocatoria de Coloquio (F7.3)
WHEN a COORDINADOR or ADMIN creates a convocatoria,
the system SHALL create an Evaluacion record with the specified configuration.

#### Scenario: Create Convocatoria with Days and Cupo
GIVEN a user with permission `coloquios:gestionar`
WHEN the user creates an Evaluacion with:
  - `materia_id` = a valid materia UUID
  - `cohorte_id` = a valid cohorte UUID
  - `tipo` = "Coloquio"
  - `instancia` = "Coloquio Final"
  - `dias_disponibles` = 5
  - `cupo_por_dia` = 3
THEN the system SHALL create an Evaluacion record
AND the record SHALL have tipo = "Coloquio"
AND the record SHALL have instancia = "Coloquio Final"
AND the record SHALL have dias_disponibles = 5
AND the record SHALL have cupo_por_dia = 3
AND the record SHALL have tenant_id matching the user's tenant

#### Scenario: Convocatoria Validation — dias_disponibles Must Be Positive
GIVEN a creation request
WHEN `dias_disponibles` is less than 1
THEN the system SHALL return a 422 validation error
AND the system SHALL NOT create any record

#### Scenario: Convocatoria Validation — cupo_por_dia Must Be Positive
GIVEN a creation request
WHEN `cupo_por_dia` is less than 1
THEN the system SHALL return a 422 validation error
AND the system SHALL NOT create any record

---

### Requirement: Importar Alumnos a Convocatoria (F7.2)
WHEN a COORDINADOR or ADMIN imports alumnos to a convocatoria,
the system SHALL register the alumnos as habilitados for that Evaluacion.

#### Scenario: Import Alumnos from Padron
GIVEN a user with permission `coloquios:gestionar`
AND an existing Evaluacion record
WHEN the user imports a list of alumno_ids (existing Usuario records with ALUMNO role)
THEN the system SHALL register each alumno as convocado for the Evaluacion
AND the system SHALL NOT create duplicate registrations for the same (evaluacion_id, alumno_id)
AND the convocados count SHALL reflect the current number of unique alumnos

#### Scenario: Import Empty List
GIVEN an existing Evaluacion
WHEN the user imports an empty list of alumno_ids
THEN the system SHALL accept the request
AND no convocados SHALL be registered

#### Scenario: Import Nonexistent Alumno
GIVEN an existing Evaluacion
WHEN the user imports an alumno_id that does not correspond to an existing Usuario
THEN the system SHALL return a 404 error
AND no convocados SHALL be registered for that evaluacion

---

### Requirement: Reservar Turno (FL-07)
WHEN an ALUMNO reserves a turno in a convocatoria,
the system SHALL create a ReservaEvaluacion with estado "Activa" if the daily cupo is available.

#### Scenario: Reserve Turno with Available Cupo
GIVEN a user with role ALUMNO and permission `coloquios:reservar`
AND an Evaluacion with cupo_por_dia = 3
AND the current reservas for that day are 0
WHEN the ALUMNO reserves with a fecha_hora matching an available day within the dias_disponibles window
THEN the system SHALL create a ReservaEvaluacion record
AND the record SHALL have estado = "Activa"
AND the record SHALL have evaluacion_id referencing the Evaluacion
AND the record SHALL have alumno_id matching the ALUMNO's user ID
AND the daily reserva count SHALL increment to 1

#### Scenario: Reserve on Day Within Window
GIVEN an Evaluacion created on 2026-06-01 with dias_disponibles = 5
WHEN an ALUMNO reserves with fecha_hora on 2026-06-03
THEN the system SHALL create the reserva successfully
AND the fecha_hora SHALL be within the valid window (created_at to created_at + dias_disponibles days)

#### Scenario: Reserve Outside Window
GIVEN an Evaluacion created on 2026-06-01 with dias_disponibles = 5
WHEN an ALUMNO attempts to reserve with fecha_hora on 2026-06-08 (day 7, outside window)
THEN the system SHALL return a 422 error
AND the system SHALL NOT create the reserva

#### Scenario: Audit on Reserva Creation
GIVEN a successful reserva creation
WHEN the reserva is created
THEN the system SHALL log an audit entry with action `RESERVA_CREAR`
AND the detalle SHALL include evaluacion_id, alumno_id, fecha_hora

---

### Requirement: Reservar Sin Cupo (FL-07)
WHEN an ALUMNO attempts to reserve on a day that has reached its maximum cupo,
the system SHALL reject the reserva.

#### Scenario: Reject When Daily Cupo Reached
GIVEN an Evaluacion with cupo_por_dia = 1
AND an existing ReservaEvaluacion Activa for that day already consuming the cupo
WHEN a second ALUMNO attempts to reserve on the same day
THEN the system SHALL return a 409 Conflict error
AND the system SHALL NOT create a new ReservaEvaluacion

#### Scenario: Reject When Alumno Already Has Active Reserva
GIVEN an ALUMNO with an existing ReservaEvaluacion Activa for a given Evaluacion
WHEN the same ALUMNO attempts to create another reserva for the same Evaluacion
THEN the system SHALL return a 409 Conflict error
AND the second reserva SHALL NOT be created

---

### Requirement: Cancelar Reserva (FL-07)
WHEN an ALUMNO cancels their active reserva,
the system SHALL set the estado to "Cancelada" and release the cupo.

#### Scenario: Cancel Active Reserva
GIVEN an ALUMNO with a ReservaEvaluacion in estado "Activa"
WHEN the ALUMNO cancels the reserva
THEN the system SHALL set estado to "Cancelada"
AND the daily cupo SHALL be released (a new reserva on the same day SHALL now succeed)

#### Scenario: Cancel Already Canceled Reserva
GIVEN a ReservaEvaluacion already in estado "Cancelada"
WHEN the ALUMNO attempts to cancel again
THEN the system SHALL return a 400 error
AND the estado SHALL remain "Cancelada"

#### Scenario: Audit on Reserva Cancelation
GIVEN a successful reserva cancelation
WHEN the reserva is canceled
THEN the system SHALL log an audit entry with action `RESERVA_CANCELAR`
AND the detalle SHALL include reserva_id, evaluacion_id, alumno_id

---

### Requirement: Panel de Métricas (F7.1)
WHEN a COORDINADOR or ADMIN accesses the metrics panel,
the system SHALL return aggregated numbers for the tenant.

#### Scenario: Metrics Show All Counts
GIVEN a tenant with:
  - 20 alumnos imported across all convocatorias
  - 3 Evaluacion records with estado activo
  - 12 ReservaEvaluacion records with estado "Activa"
  - 5 ResultadoEvaluacion records
WHEN a user with `coloquios:ver` accesses the metrics endpoint
THEN the response SHALL include:
  - total_alumnos = 20
  - instancias_activas = 3
  - reservas_activas = 12
  - notas_registradas = 5

#### Scenario: Metrics Empty Tenant
GIVEN a tenant with no convocatorias nor alumnos
WHEN a user accesses the metrics endpoint
THEN the response SHALL return:
  - total_alumnos = 0
  - instancias_activas = 0
  - reservas_activas = 0
  - notas_registradas = 0

---

### Requirement: Listado de Convocatorias (F7.4)
WHEN a user with `coloquios:ver` lists convocatorias,
the system SHALL return a table with operational metrics per convocatoria.

#### Scenario: List Convocatorias with Stats
GIVEN a tenant with 2 Evaluacion records
AND each has associated alumnos, reservas, and resultados
WHEN the user lists convocatorias
THEN the response SHALL include per-convocatoria:
  - materia (nombre)
  - instancia
  - dias_disponibles
  - total_convocados (count of alumnos imported)
  - reservas_activas (count of ReservaEvaluacion Activa)
  - cupos_libres (dias_disponibles × cupo_por_dia - reservas_activas)

#### Scenario: List Filtered by Materia
GIVEN convocatorias for materia A and materia B
WHEN the user lists convocatorias filtered by materia_id = materia_A
THEN the response SHALL contain only convocatorias for materia A

---

### Requirement: Resultado Consolidado (F7.5)
WHEN a COORDINADOR or ADMIN registers a nota final for an ALUMNO in a convocatoria,
the system SHALL create or update the ResultadoEvaluacion record.

#### Scenario: Register Nota Final
GIVEN a user with permission `coloquios:gestionar`
AND an Evaluacion with an imported ALUMNO
WHEN the user registers nota_final = "8 (Ocho)" for that ALUMNO
THEN the system SHALL create a ResultadoEvaluacion record
AND the record SHALL have nota_final = "8 (Ocho)"
AND the record SHALL have evaluacion_id and alumno_id matching

#### Scenario: Update Existing Nota Final (Upsert)
GIVEN an existing ResultadoEvaluacion with nota_final = "6 (Seis)"
WHEN the user registers a new nota_final = "7 (Siete)" for the same (evaluacion_id, alumno_id)
THEN the system SHALL update the existing record
AND the record SHALL have nota_final = "7 (Siete)"
AND the system SHALL NOT create a duplicate record

#### Scenario: Consult Resultados Consolidados
GIVEN an Evaluacion with multiple ResultadoEvaluacion records
WHEN a user with `coloquios:ver` accesses the resultados endpoint
THEN the response SHALL return all resultados for that Evaluacion
AND each resultado SHALL include: alumno_id, alumno_nombre, nota_final

#### Scenario: Audit on Resultado Registration
GIVEN a successful resultado registration
WHEN the resultado is created or updated
THEN the system SHALL log an audit entry with action `RESULTADO_REGISTRAR`
AND the detalle SHALL include evaluacion_id, alumno_id, nota_final

---

### Requirement: Admin Global (F7.5)
WHEN an ADMIN accesses the coloquios admin view,
the system SHALL return a consolidated dashboard with all convocatorias, results, and agenda.

#### Scenario: Admin Sees All Convocatorias
GIVEN a tenant with multiple Evaluacion records
WHEN a user with ADMIN role accesses the admin endpoint
THEN the response SHALL include:
  - ALL convocatorias across all materias
  - Each with its alumnos, reservas activas, and resultados
  - Agenda of all active reservas ordered by fecha_hora

#### Scenario: COORDINADOR Sees All Convocatorias
GIVEN a user with COORDINADOR role and permission `coloquios:ver`
WHEN the user accesses the admin endpoint
THEN the response SHALL include all convocatorias in the tenant
AND NOT be filtered by materia assignments

#### Scenario: PROFESOR Cannot Access Admin View
GIVEN a user with role PROFESOR and only permission `coloquios:ver`
WHEN the user accesses the admin endpoint
THEN the system SHALL return a 403 Forbidden response

---

### Requirement: Permission Enforcement
WHEN a user accesses coloquios endpoints,
the system SHALL enforce the corresponding permission.

#### Scenario: coloquios:gestionar for COORDINADOR
GIVEN a user with role COORDINADOR and assigned permission `coloquios:gestionar`
WHEN the user accesses create, import, or result registration endpoints
THEN the system SHALL allow the action across any materia in the tenant

#### Scenario: coloquios:reservar for ALUMNO
GIVEN a user with role ALUMNO and assigned permission `coloquios:reservar`
WHEN the user POSTs to /api/v1/coloquios/{id}/reservar
THEN the system SHALL allow the action
AND the reserva SHALL be created with alumno_id matching the authenticated user

#### Scenario: coloquios:ver for PROFESOR
GIVEN a user with role PROFESOR and assigned permission `coloquios:ver`
WHEN the user lists convocatorias or views resultados
THEN the system SHALL return only convocatorias for materias assigned to that PROFESOR

#### Scenario: Without Permission
GIVEN a user WITHOUT the required permission
WHEN the user accesses a protected coloquios endpoint
THEN the system SHALL return a 403 Forbidden response

---

### Requirement: Audit Trail
WHEN a coloquios action is performed,
the system SHALL record the action in the audit log.

#### Scenario: Coloquio Created
GIVEN a successful convocatoria creation
WHEN the action completes
THEN the system SHALL call AuditService.log_action
AND the action SHALL be `COLOQUIO_CREAR`
AND the detalle SHALL include evaluacion_id, materia_id, instancia, dias_disponibles, cupo_por_dia

#### Scenario: Reserva Created
GIVEN a successful reserva creation
WHEN the action completes
THEN the system SHALL call AuditService.log_action
AND the action SHALL be `RESERVA_CREAR`
AND the detalle SHALL include reserva_id, evaluacion_id, alumno_id, fecha_hora

#### Scenario: Reserva Canceled
GIVEN a successful reserva cancelation
WHEN the action completes
THEN the system SHALL call AuditService.log_action
AND the action SHALL be `RESERVA_CANCELAR`
AND the detalle SHALL include reserva_id, evaluacion_id, alumno_id

#### Scenario: Resultado Registered
GIVEN a successful resultado registration
WHEN the action completes
THEN the system SHALL call AuditService.log_action
AND the action SHALL be `RESULTADO_REGISTRAR`
AND the detalle SHALL include evaluacion_id, alumno_id, nota_final
