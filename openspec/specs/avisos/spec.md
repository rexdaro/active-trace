# avisos-y-acknowledgment — Specification Delta

## Requirements

### Requirement: ABM Avisos with Scope (F3.5)
WHEN a user with permission `avisos:publicar` creates, edits, or deletes an aviso,
the system SHALL manage Aviso records with the specified scope configuration.

#### Scenario: Create Global Aviso
GIVEN a user with role COORDINADOR or ADMIN and permission `avisos:publicar`
WHEN the user creates an Aviso with:
  - `alcance` = "Global"
  - `titulo` = "Inicio de inscripciones"
  - `cuerpo` = "Las inscripciones comienzan el 15/03."
  - `inicio_en` = "2026-03-01T00:00:00"
  - `fin_en` = "2026-04-01T00:00:00"
  - `severidad` = "Info"
  - `orden` = 0
  - `requiere_ack` = false
THEN the system SHALL create an Aviso record
AND the record SHALL have `activo` = true
AND the record SHALL have `tenant_id` matching the user's tenant
AND the record SHALL have the provided alcance, titulo, cuerpo, inicio_en, fin_en

#### Scenario: Create Aviso with Materia Scope
GIVEN a user with permission `avisos:publicar`
WHEN the user creates an Aviso with `alcance` = "PorMateria" and a valid `materia_id`
THEN the system SHALL create the Aviso record
AND the record SHALL have `materia_id` matching the provided materia
AND the record SHALL have `cohorte_id` = null
AND the record SHALL have `rol_destino` = null

#### Scenario: Create Aviso with Cohorte Scope
GIVEN a user with permission `avisos:publicar`
WHEN the user creates an Aviso with `alcance` = "PorCohorte" and a valid `cohorte_id`
THEN the system SHALL create the Aviso record
AND the record SHALL have `cohorte_id` matching the provided cohorte
AND the record SHALL have `materia_id` = null
AND the record SHALL have `rol_destino` = null

#### Scenario: Create Aviso with Rol Scope
GIVEN a user with permission `avisos:publicar`
WHEN the user creates an Aviso with `alcance` = "PorRol" and `rol_destino` = "PROFESOR"
THEN the system SHALL create the Aviso record
AND the record SHALL have `rol_destino` = "PROFESOR"
AND the record SHALL have `materia_id` = null
AND the record SHALL have `cohorte_id` = null

#### Scenario: Edit Aviso
GIVEN an existing Aviso record
WHEN a user with permission `avisos:publicar` edits the aviso
THEN the system SHALL update the specified fields
AND the `updated_at` timestamp SHALL be refreshed

#### Scenario: Delete Aviso (Soft)
GIVEN an existing Aviso record
WHEN a user with permission `avisos:publicar` deletes the aviso
THEN the system SHALL set `deleted_at` to the current timestamp
AND the aviso SHALL NOT appear in any queries

#### Scenario: Validation — inicio_en Must Be Before fin_en
GIVEN a creation or edit request
WHEN `inicio_en` >= `fin_en`
THEN the system SHALL return a 422 validation error
AND the system SHALL NOT create or update the record

#### Scenario: Validation — alcance Requires Matching Context
GIVEN a creation request with `alcance` = "PorMateria"
WHEN `materia_id` is null
THEN the system SHALL return a 422 validation error

GIVEN a creation request with `alcance` = "PorCohorte"
WHEN `cohorte_id` is null
THEN the system SHALL return a 422 validation error

---

### Requirement: Visualización Filtrada por Audiencia (RN-20)
WHEN a user views avisos,
the system SHALL return only avisos matching the user's scope based on alcance and user's role/context.

#### Scenario: Global Aviso Visible to All
GIVEN an Aviso with `alcance` = "Global"
WHEN any user in the tenant views avisos
THEN the aviso SHALL appear in the response

#### Scenario: Materia Aviso Visible Only to Assigned Users
GIVEN an Aviso with `alcance` = "PorMateria" and `materia_id` = M1
WHEN a user assigned to materia M1 views avisos
THEN the aviso SHALL appear in the response

GIVEN an Aviso with `alcance` = "PorMateria" and `materia_id` = M1
WHEN a user NOT assigned to materia M1 views avisos
THEN the aviso SHALL NOT appear in the response

#### Scenario: Cohorte Aviso Visible to Cohort Members
GIVEN an Aviso with `alcance` = "PorCohorte" and `cohorte_id` = C1
WHEN a user assigned to cohorte C1 views avisos
THEN the aviso SHALL appear in the response

GIVEN an Aviso with `alcance` = "PorCohorte" and `cohorte_id` = C1
WHEN a user NOT assigned to cohorte C1 views avisos
THEN the aviso SHALL NOT appear in the response

#### Scenario: Rol Aviso Visible to Matching Role
GIVEN an Aviso with `alcance` = "PorRol" and `rol_destino` = "PROFESOR"
WHEN a user with role PROFESOR views avisos
THEN the aviso SHALL appear in the response

GIVEN an Aviso with `alcance` = "PorRol" and `rol_destino` = "PROFESOR"
WHEN a user with role ALUMNO views avisos
THEN the aviso SHALL NOT appear in the response

#### Scenario: Null rol_destino Means All Roles
GIVEN an Aviso with `alcance` = "PorRol" and `rol_destino` = null
WHEN any user views avisos
THEN the aviso SHALL appear in the response

---

### Requirement: Ventana de Vigencia (RN-18)
WHEN a user views avisos,
the system SHALL return only avisos whose visibility window includes the current datetime.

#### Scenario: Visible Within Window
GIVEN an Aviso with `inicio_en` = "2026-03-01T00:00:00" and `fin_en` = "2026-04-01T00:00:00"
WHEN the current datetime is "2026-03-15T12:00:00" (within the window)
THEN the aviso SHALL appear in the response

#### Scenario: Hidden Before Window
GIVEN an Aviso with `inicio_en` = "2026-03-01T00:00:00"
WHEN the current datetime is "2026-02-15T12:00:00" (before inicio_en)
THEN the aviso SHALL NOT appear in the response

#### Scenario: Hidden After Window
GIVEN an Aviso with `fin_en` = "2026-04-01T00:00:00"
WHEN the current datetime is "2026-04-15T12:00:00" (after fin_en)
THEN the aviso SHALL NOT appear in the response

---

### Requirement: Confirmación de Lectura (RN-19)
WHEN a user with permission `avisos:confirmar` confirms an aviso,
the system SHALL create an AcknowledgmentAviso record.

#### Scenario: Confirm Aviso
GIVEN an Aviso with `requiere_ack` = true
AND the aviso is visible to the user
WHEN the user POSTs to `/api/avisos/{id}/confirmar`
THEN the system SHALL create an AcknowledgmentAviso record
AND the record SHALL have `aviso_id` matching the aviso
AND the record SHALL have `usuario_id` matching the authenticated user
AND the record SHALL have `confirmado_at` set to the current datetime

#### Scenario: Acknowledged Aviso No Longer Shows as Pending
GIVEN an Aviso with `requiere_ack` = true
WHEN the user has already confirmed the aviso
THEN the aviso SHALL still appear in the list
AND the response SHALL indicate that the user has already acknowledged it

#### Scenario: Cannot Confirm Non-Existent Aviso
GIVEN an aviso_id that does not exist
WHEN a user attempts to confirm it
THEN the system SHALL return a 404 error

#### Scenario: Cannot Confirm Same Aviso Twice
GIVEN an existing AcknowledgmentAviso for (aviso_id, usuario_id)
WHEN the same user attempts to confirm again
THEN the system SHALL return a 409 Conflict error
AND the system SHALL NOT create a duplicate AcknowledgmentAviso

---

### Requirement: Ack Counters Derived from AcknowledgmentAviso (RN-19)
WHEN a user queries acknowledgment counts,
the system SHALL compute the count from the AcknowledgmentAviso table.

#### Scenario: Get Ack Count
GIVEN an Aviso with 5 AcknowledgmentAviso records
WHEN a user accesses the ack-count endpoint
THEN the response SHALL include `total_acknowledgments` = 5

#### Scenario: Get Ack Count for Aviso Without Ack Required
GIVEN an Aviso with `requiere_ack` = false
WHEN a user accesses the ack-count endpoint
THEN the response SHALL include `total_acknowledgments` = 0

#### Scenario: Count Per User
GIVEN an Aviso with `requiere_ack` = true
WHEN a user accesses the ack-count endpoint
THEN the response SHALL NOT expose which specific users acknowledged

---

### Requirement: Orden de Prioridad
WHEN a user views avisos,
the system SHALL order avisos by the `orden` column (lower = higher priority).

#### Scenario: Ordered by Orden Ascending
GIVEN Aviso A with orden = 0 and Aviso B with orden = 10
WHEN a user views avisos
THEN aviso A SHALL appear before aviso B

#### Scenario: Same Orden — Order by created_at Descending
GIVEN Aviso A and Aviso B both with orden = 0
WHEN aviso A was created before aviso B
THEN aviso B SHALL appear before aviso A

---

### Requirement: Permission Enforcement
WHEN a user accesses avisos endpoints,
the system SHALL enforce the corresponding permission.

#### Scenario: avisos:publicar for COORDINADOR
GIVEN a user with role COORDINADOR and assigned permission `avisos:publicar`
WHEN the user accesses create, edit, or delete endpoints
THEN the system SHALL allow the action

#### Scenario: avisos:ver for All Roles
GIVEN a user with permission `avisos:ver`
WHEN the user lists avisos
THEN the system SHALL return visible avisos scoped to the user's context

#### Scenario: avisos:confirmar for All Roles
GIVEN a user with permission `avisos:confirmar`
WHEN the user confirms an aviso
THEN the system SHALL allow the action

#### Scenario: Without Permission
GIVEN a user WITHOUT the required permission
WHEN the user accesses a protected avisos endpoint
THEN the system SHALL return a 403 Forbidden response

---

### Requirement: Audit Trail
WHEN an aviso action is performed,
the system SHALL record the action in the audit log.

#### Scenario: Aviso Created
GIVEN a successful aviso creation
WHEN the action completes
THEN the system SHALL call AuditService.log_action
AND the action SHALL be `AVISO_CREAR`
AND the detalle SHALL include aviso_id, alcance, titulo, severidad

#### Scenario: Aviso Edited
GIVEN a successful aviso edit
WHEN the action completes
THEN the system SHALL call AuditService.log_action
AND the action SHALL be `AVISO_EDITAR`
AND the detalle SHALL include aviso_id and the changed fields

#### Scenario: Aviso Deleted
GIVEN a successful aviso soft-delete
WHEN the action completes
THEN the system SHALL call AuditService.log_action
AND the action SHALL be `AVISO_ELIMINAR`
AND the detalle SHALL include aviso_id, titulo

#### Scenario: Aviso Confirmed
GIVEN a successful acknowledgment
WHEN the action completes
THEN the system SHALL call AuditService.log_action
AND the action SHALL be `AVISO_CONFIRMAR`
AND the detalle SHALL include aviso_id, usuario_id
