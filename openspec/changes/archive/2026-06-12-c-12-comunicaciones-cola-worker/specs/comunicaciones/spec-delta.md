# comunicaciones — Specification Delta

## ADDED Requirements

### Requirement: Comunicacion State Machine
WHEN a communication message transitions between states,
the system SHALL enforce the valid state transitions defined in RN-15.

#### Scenario: Message Created in Pendiente
GIVEN a user with permission `comunicacion:enviar`
WHEN the user confirms a send
THEN the system creates a Comunicacion record
AND the record SHALL have estado = "Pendiente"
AND the record SHALL have an auto-generated id and lote_id

#### Scenario: Worker Picks Up Pendiente
GIVEN a Comunicacion record in estado "Pendiente"
WHEN the dispatch worker selects it for processing
THEN the system SHALL transition estado to "Enviando"
AND the system SHALL attempt to send the email

#### Scenario: Delivery Confirmed
GIVEN a Comunicacion record in estado "Enviando"
WHEN the email delivery succeeds
THEN the system SHALL transition estado to "Enviado"
AND the system SHALL set enviado_at to the current timestamp

#### Scenario: Delivery Fails
GIVEN a Comunicacion record in estado "Enviando"
WHEN the email delivery fails
THEN the system SHALL transition estado to "Error"
AND the system SHALL NOT change enviado_at

#### Scenario: Cancel from Pendiente
GIVEN a Comunicacion record in estado "Pendiente"
WHEN a user with permission `comunicacion:enviar` cancels it
THEN the system SHALL transition estado to "Cancelado"
AND the system SHALL NOT send the email

#### Scenario: Invalid Transition Rejected
GIVEN a Comunicacion record NOT in estado "Pendiente"
WHEN a user or worker attempts to cancel it
THEN the system SHALL reject the transition
AND the system SHALL raise a validation error

---

### Requirement: Preview Before Send
WHEN a user initiates a preview for a communication,
the system SHALL render the subject and body per recipient BEFORE any records are created.

#### Scenario: Preview with Variables
GIVEN a user with permission `comunicacion:enviar`
WHEN the user sends a preview request with:
- a list of recipients
- a subject template containing variable placeholders
- a body template containing variable placeholders
THEN the system SHALL return a rendered preview for each recipient
AND the system SHALL substitute variables (nombre, apellido, comision, regional, materia) with actual values
AND the system SHALL NOT create any Comunicacion records
AND the system SHALL store the preview data under a unique preview_token

#### Scenario: Preview with Missing Variable
GIVEN a preview request with a template containing a variable
WHEN the variable is not found in the recipient data
THEN the system SHALL return an error indicating which variable is missing for which recipient
AND the system SHALL NOT generate a preview_token

---

### Requirement: Batch Enqueue
WHEN a user confirms a send after preview,
the system SHALL create a Comunicacion record for each recipient in estado "Pendiente".

#### Scenario: Confirm Creates Batch
GIVEN a valid preview_token from a preview request
WHEN the user sends a confirm request with that preview_token
THEN the system SHALL create one Comunicacion record per recipient
AND all records SHALL share the same auto-generated lote_id
AND each record SHALL have estado = "Pendiente"
AND the preview_token SHALL be invalidated after use

#### Scenario: Confirm Invalid Token
GIVEN an expired or non-existent preview_token
WHEN the user sends a confirm request
THEN the system SHALL return a 400 error
AND the system SHALL NOT create any records

#### Scenario: Confirm Without Approval (Tenant Config)
GIVEN a tenant with `requiere_aprobacion = false`
WHEN the batch enqueue completes
THEN the records SHALL be immediately eligible for the dispatch worker

#### Scenario: Confirm With Approval (Tenant Config)
GIVEN a tenant with `requiere_aprobacion = true`
WHEN the batch enqueue completes
THEN the records SHALL remain in estado "Pendiente"
AND the records SHALL NOT be eligible for the dispatch worker
AND the records SHALL only transition to "Enviando" when explicitly approved

---

### Requirement: Approval Flow
WHEN a mass communication requires approval,
the system SHALL enforce that only users with `comunicacion:aprobar` can authorize dispatch.

#### Scenario: Approve Lote
GIVEN a user with permission `comunicacion:aprobar`
WHEN the user approves a lote by lote_id
THEN the system SHALL transition ALL records in that lote with estado "Pendiente" to "Enviando"
AND the system SHALL NOT affect records NOT in estado "Pendiente"
AND the system SHALL log an audit entry with action `COMUNICACION_APROBAR`

#### Scenario: Approve Individual Message
GIVEN a user with permission `comunicacion:aprobar`
WHEN the user approves a single Comunicacion by id
THEN the system SHALL transition that record from "Pendiente" to "Enviando"
AND the system SHALL NOT affect other records in the same lote
AND the system SHALL log an audit entry with action `COMUNICACION_APROBAR`

#### Scenario: Reject Lote
GIVEN a user with permission `comunicacion:aprobar`
WHEN the user rejects/cancels a lote by lote_id
THEN the system SHALL transition ALL records in that lote with estado "Pendiente" to "Cancelado"
AND the system SHALL log an audit entry with action `COMUNICACION_CANCELAR`

#### Scenario: Unauthorized Approval Attempt
GIVEN a user WITHOUT permission `comunicacion:aprobar`
WHEN the user attempts to approve a lote or individual message
THEN the system SHALL return a 403 Forbidden response

---

### Requirement: Worker Dispatch
WHEN the dispatch worker runs,
the system SHALL process eligible Pendiente messages asynchronously.

#### Scenario: Worker Processes Message
GIVEN Comunicacion records in estado "Pendiente" that are eligible (tenant without approval or approved)
WHEN the worker picks up a record
THEN the system SHALL transition estado to "Enviando"
AND the system SHALL send the email via SMTP with the configured settings
WHEN the email is sent successfully
THEN the system SHALL transition estado to "Enviado"
AND the system SHALL set enviado_at to the current timestamp
WHEN the email send fails
THEN the system SHALL transition estado to "Error"

#### Scenario: Worker Retry on Transient Failure
GIVEN an email send fails with a transient error
WHEN the worker has retry attempts remaining
THEN the system SHALL retry the send after a backoff delay
AND the system SHALL mark as "Error" only after exhausting all retries

#### Scenario: Worker Skips Non-Eligible Messages
GIVEN a Comunicacion record in estado "Pendiente" requiring approval
WHEN the worker runs
THEN the system SHALL NOT process that record
AND the record SHALL remain in "Pendiente" until approved

---

### Requirement: Permissions
WHEN a user accesses a communication endpoint,
the system SHALL enforce the corresponding permission.

#### Scenario: comunicacion:enviar
GIVEN a user with role PROFESOR, COORDINADOR, or ADMIN
WHEN the user accesses any endpoint under comunicaciones (except approval endpoints)
THEN the system SHALL allow the action IF the user has the assigned permission `comunicacion:enviar`
AND for PROFESOR, the system SHALL scope data to their own assigned materias

#### Scenario: comunicacion:aprobar
GIVEN a user with role COORDINADOR or ADMIN
WHEN the user accesses approval endpoints (approve/reject lote or individual)
THEN the system SHALL allow the action IF the user has the assigned permission `comunicacion:aprobar`

#### Scenario: Without Permission
GIVEN a user WITHOUT the required permission
WHEN the user accesses a protected endpoint
THEN the system SHALL return a 403 Forbidden response

---

### Requirement: Audit Trail
WHEN a communication action is performed,
the system SHALL record the action in the audit log.

#### Scenario: Communication Sent
GIVEN a confirmed send
WHEN records are created
THEN the system SHALL call AuditService.log_action
AND the action SHALL be `COMUNICACION_ENVIAR`
AND the detalle SHALL include lote_id, cantidad, materia_id

#### Scenario: Communication Approved
GIVEN an approved lote or individual communication
WHEN the approval is processed
THEN the system SHALL call AuditService.log_action
AND the action SHALL be `COMUNICACION_APROBAR`
AND the detalle SHALL include lote_id and tipo (lote/individual)

#### Scenario: Communication Cancelled
GIVEN a cancelled lote or individual communication
WHEN the cancellation is processed
THEN the system SHALL call AuditService.log_action
AND the action SHALL be `COMUNICACION_CANCELAR`
AND the detalle SHALL include lote_id and tipo (lote/individual)
