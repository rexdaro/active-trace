# encuentros-y-guardias — Specification Delta

## Requirements

### Requirement: Recurrent Slot Creation (F6.1, RN-13)
WHEN a user creates a recurrent slot for encuentros,
the system SHALL generate N individual InstanciaEncuentro records based on the slot's configuration.

#### Scenario: Slot Creates N Weekly Instances
GIVEN a user with permission `encuentros:gestionar`
WHEN the user creates a SlotEncuentro with:
  - `fecha_inicio` = "2026-03-16" (Monday)
  - `cant_semanas` = 4
  - `dia_semana` = 0 (Monday)
  - `hora` = "10:00"
THEN the system SHALL create a SlotEncuentro record
AND the system SHALL create 4 InstanciaEncuentro records
AND the first instance SHALL have fecha = "2026-03-16"
AND the second instance SHALL have fecha = "2026-03-23"
AND the third instance SHALL have fecha = "2026-03-30"
AND the fourth instance SHALL have fecha = "2026-04-06"
AND all instances SHALL have slot_id referencing the created slot
AND all instances SHALL have estado = "Programado"
AND each instance SHALL inherit titulo, hora, meet_url from the slot

#### Scenario: Slot Validation — cant_semanas Must Be Positive
GIVEN a slot creation request
WHEN `cant_semanas` is less than 1
THEN the system SHALL return a 422 validation error

#### Scenario: Slot Validation — fecha_inicio Must Match dia_semana
GIVEN a slot creation request with `fecha_inicio` = "2026-03-17" (Tuesday)
WHEN `dia_semana` = 0 (Monday)
THEN the system SHALL return a 422 validation error
AND the system SHALL NOT create any records

#### Scenario: Audit on Slot Creation
GIVEN a successful recurrent slot creation
WHEN the slot and instances are created
THEN the system SHALL log an audit entry with action `ENCUENTRO_CREAR`
AND the detalle SHALL include slot_id, materia_id, cant_semanas

---

### Requirement: Unique Encounter Creation (F6.2)
WHEN a user creates a unique encounter (without recurrence),
the system SHALL create a single InstanciaEncuentro record with slot_id = NULL.

#### Scenario: Create Single Instance
GIVEN a user with permission `encuentros:gestionar`
WHEN the user creates an InstanciaEncuentro without a slot_id
THEN the system SHALL create a single InstanciaEncuentro record
AND the record SHALL have slot_id = NULL
AND the record SHALL have estado = "Programado"
AND the record SHALL have the provided fecha, hora, titulo, meet_url, materia_id

---

### Requirement: Instance State Edit Independent of Slot (F6.3, RN-14)
WHEN a user edits an InstanciaEncuentro,
the system SHALL allow modifying estado, meet_url, video_url, and comentario independently.
The edit SHALL NOT affect the parent SlotEncuentro or sibling instances.

#### Scenario: Mark Instance as Realizado
GIVEN an InstanciaEncuentro in estado "Programado"
WHEN the user edits it with estado = "Realizado" and video_url = "https://example.com/grabacion.mp4"
THEN the system SHALL set estado to "Realizado"
AND the system SHALL set video_url to "https://example.com/grabacion.mp4"
AND the parent SlotEncuentro SHALL remain unchanged
AND sibling InstanciaEncuentro records SHALL remain in their original estados

#### Scenario: Cancel Single Instance
GIVEN an InstanciaEncuentro in estado "Programado"
WHEN the user edits it with estado = "Cancelado" and comentario = "Clase suspendida"
THEN the system SHALL set estado to "Cancelado"
AND the system SHALL set comentario to "Clase suspendida"
AND sibling instances SHALL NOT be affected

#### Scenario: Edit Meet URL on Instance
GIVEN an InstanciaEncuentro
WHEN the user edits its meet_url
THEN the system SHALL update only that instance's meet_url
AND the parent slot's meet_url SHALL remain unchanged

#### Scenario: Audit on Instance Edit
GIVEN a successful instance edit
WHEN the instance is updated
THEN the system SHALL log an audit entry with action `ENCUENTRO_EDITAR`
AND the detalle SHALL include instancia_id and the changed fields

---

### Requirement: HTML Block Generation for LMS (F6.4)
WHEN a user requests HTML generation for a materia,
the system SHALL generate a sanitized HTML block with upcoming encuentros ready for LMS embedding.

#### Scenario: Generate HTML with Upcoming Instances
GIVEN a materia with upcoming InstanciaEncuentro records (estado = "Programado" and fecha >= today)
WHEN the user requests HTML export
THEN the system SHALL return a string of HTML containing a table
AND the table SHALL have columns: Fecha, Hora, Título, Enlace, Grabación (if exists)
AND all user-provided text content SHALL be HTML-escaped
AND the block SHALL NOT include instances with estado = "Cancelado"

#### Scenario: Empty HTML When No Upcoming Instances
GIVEN a materia with no upcoming InstanciaEncuentro records
WHEN the user requests HTML export
THEN the system SHALL return an empty HTML block
OR a block with a single row indicating "No hay encuentros programados"

---

### Requirement: Admin Global View of Encuentros (F6.5)
WHEN a COORDINADOR or ADMIN accesses the encuentros admin view,
the system SHALL return all encounters across all materias in the tenant.

#### Scenario: Coordinator Sees All Encuentros
GIVEN a user with role COORDINADOR and permission `encuentros:ver`
WHEN the user accesses the admin encounters endpoint
THEN the system SHALL return InstanciaEncuentro records across ALL materias in the tenant
AND the response SHALL NOT be filtered by the user's own materia assignments

#### Scenario: Admin Sees All Encuentros
GIVEN a user with role ADMIN and permission `encuentros:ver`
WHEN the user accesses the admin encounters endpoint
THEN the system SHALL return all InstanciaEncuentro records in the tenant

#### Scenario: PROFESOR Cannot Access Admin View
GIVEN a user with role PROFESOR and only permission `encuentros:gestionar`
WHEN the user accesses the admin encounters endpoint
THEN the system SHALL return a 403 Forbidden response

---

### Requirement: Guardia Registration (F6.6)
WHEN a TUTOR registers a guardia,
the system SHALL create a Guardia record scoped to that TUTOR's assignments.

#### Scenario: Tutor Registers Own Guardia
GIVEN a user with role TUTOR and permission `guardias:registrar`
WHEN the user creates a Guardia with asignacion_id referencing their own assignment
THEN the system SHALL create a Guardia record
AND the record SHALL have estado = "Pendiente"
AND the record SHALL have the provided dia, horario, materia_id, carrera_id, cohorte_id

#### Scenario: Prevent Overlapping Guardia
GIVEN an existing Guardia record for user U with dia = "Lunes" and horario = "10:00–10:45"
WHEN the same user U attempts to create another Guardia with dia = "Lunes" and horario = "10:00–10:45"
THEN the system SHALL return a 409 Conflict error
AND the system SHALL NOT create the duplicate record

#### Scenario: Allow Non-Overlapping Guardia
GIVEN an existing Guardia record for user U with dia = "Lunes" and horario = "10:00–10:45"
WHEN the same user U creates a Guardia with dia = "Martes" and horario = "10:00–10:45"
THEN the system SHALL create the record successfully

#### Scenario: Audit on Guardia Registration
GIVEN a successful guardia registration
WHEN the guardia is created
THEN the system SHALL log an audit entry with action `GUARDIA_REGISTRAR`
AND the detalle SHALL include guardia_id, materia_id, asignacion_id

---

### Requirement: Guardia Global View and Export (F6.6)
WHEN a COORDINADOR or ADMIN accesses guardias,
the system SHALL return guardia records across the entire tenant with filter support.

#### Scenario: Coordinator Views All Guardias
GIVEN a user with role COORDINADOR and permission `guardias:ver`
WHEN the user lists guardias
THEN the system SHALL return Guardia records across ALL users in the tenant
AND the response SHALL support filters: materia_id, cohorte_id, estado, rango_fechas

#### Scenario: Export Guardias as CSV
GIVEN a user with permission `guardias:ver`
WHEN the user requests export
THEN the system SHALL return a CSV file with columns: id, tutor_nombre, materia, carrera, cohorte, dia, horario, estado, comentarios, creada_at
AND the response SHALL have Content-Type: text/csv

#### Scenario: Tutor Sees Only Own Guardias
GIVEN a user with role TUTOR and permission `guardias:registrar` but NOT `guardias:ver`
WHEN the user lists guardias
THEN the system SHALL return only Guardia records where asignacion_id belongs to the TUTOR's own assignments

---

### Requirement: Permission Enforcement
WHEN a user accesses encuentros or guardias endpoints,
the system SHALL enforce the corresponding permission.

#### Scenario: encuentros:gestionar for PROFESOR
GIVEN a user with role PROFESOR and assigned permission `encuentros:gestionar`
WHEN the user accesses slot or instancia endpoints
THEN the system SHALL allow the action
AND for write operations (create/edit), the system SHALL scope to the PROFESOR's own assigned materias

#### Scenario: encuentros:gestionar for COORDINADOR
GIVEN a user with role COORDINADOR and assigned permission `encuentros:gestionar`
WHEN the user accesses slot or instancia endpoints
THEN the system SHALL allow the action across any materia in the tenant

#### Scenario: Without Permission
GIVEN a user WITHOUT the required permission
WHEN the user accesses a protected encuentros or guardias endpoint
THEN the system SHALL return a 403 Forbidden response

#### Scenario: guardias:registrar for TUTOR
GIVEN a user with role TUTOR and assigned permission `guardias:registrar`
WHEN the user POSTs to /api/v1/guardias
THEN the system SHALL allow the action
AND the asignacion_id SHALL be validated to belong to the TUTOR's own assignments

---

### Requirement: Audit Trail
WHEN a encuentro or guardia action is performed,
the system SHALL record the action in the audit log.

#### Scenario: Encuentro Created
GIVEN a successful encuentro creation (recurrent or unique)
WHEN the action completes
THEN the system SHALL call AuditService.log_action
AND the action SHALL be `ENCUENTRO_CREAR`
AND the detalle SHALL include slot_id (if recurrent), instancia_ids, materia_id, tipo (recurrente/unico)

#### Scenario: Encuentro Edited
GIVEN a successful instance edit
WHEN the action completes
THEN the system SHALL call AuditService.log_action
AND the action SHALL be `ENCUENTRO_EDITAR`
AND the detalle SHALL include instancia_id, materia_id, and the fields that changed

#### Scenario: Guardia Registered
GIVEN a successful guardia registration
WHEN the action completes
THEN the system SHALL call AuditService.log_action
AND the action SHALL be `GUARDIA_REGISTRAR`
AND the detalle SHALL include guardia_id, materia_id, asignacion_id
