# Implementation Tasks

1. [x] Define SQLAlchemy 2.0 models for Aviso and AcknowledgmentAviso.
2. [x] Create Alembic migration for avisos and acknowledgments_aviso tables.
3. [x] Write model tests: defaults, enums, matería/cohorte/rol scopes, ack creation, unique constraint, vigencia window.
4. [ ] Create Pydantic v2 schemas for Aviso and AcknowledgmentAviso.
5. [ ] Implement repository layer for avisos (scope filtering, vigencia filtering, acknowledgment queries).
6. [ ] Create avisos router with endpoints:
    - `GET /api/avisos` — list visible avisos filtered by audience and vigencia (avisos:ver)
    - `POST /api/avisos` — create aviso (avisos:publicar)
    - `PUT /api/avisos/{id}` — edit aviso (avisos:publicar)
    - `DELETE /api/avisos/{id}` — delete aviso (avisos:publicar)
    - `POST /api/avisos/{id}/confirmar` — confirm acknowledgment (avisos:confirmar)
    - `GET /api/avisos/{id}/ack-count` — get acknowledgment count (avisos:ver)
7. [ ] Add audit trail actions (AVISO_CREAR, AVISO_EDITAR, AVISO_ELIMINAR, AVISO_CONFIRMAR).
8. [ ] Write integration tests: CRUD, scope filtering, vigencia window, ack flow, permissions, audit.
