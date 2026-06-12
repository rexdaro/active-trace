# Design: C-06-estructura-academica

## Context
Implement the core academic structure (Carreras, Cohortes, Materias) based on the Domain Data Model (knowledge-base/04_modelo_de_datos.md).

## Goals / Non-Goals
**Goals:**
- Implement Carrera, Cohorte, and Materia models.
- Establish relationships as defined in the ERD.
- Ensure tenant isolation (tenant_id).

**Non-Goals:**
- Implement assignment or padrón loading in this change.

## Architecture Overview
- Domain Models in `src/core`.
- ORM mappings in `src/repositories/models`.

## Infrastructure
- SQLAlchemy models.
- Alembic migrations.

## Decisions
- Strict mapping to domain model entities defined in KB.

## Risks / Trade-offs
- [Risk] Tenant consistency → Mitigation: Base repository will enforce tenant isolation.

## Migration Plan
- Generate alembic migrations.

## Open Questions
- None.
