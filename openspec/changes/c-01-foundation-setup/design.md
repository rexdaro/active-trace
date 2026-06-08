# Design: C-01-foundation-setup

## Context
Initial project foundation setup to enable rapid development with clean architecture.

## Goals / Non-Goals
**Goals:**
- Implement structured FastAPI project with clean architecture patterns.
- Ensure all IO (DB) is async.
- Enable observability from day one.

**Non-Goals:**
- Production-grade deployment security (will be handled in later infrastructure changes).
- Comprehensive test coverage of initial scaffolding.

## Architecture Overview
- Clean Architecture (screaming architecture):
    - `src/core`: Domain models, abstract interfaces.
    - `src/services`: Business logic.
    - `src/repositories`: Data access.
    - `src/api`: FastAPI routers, dependencies.
    - `src/schemas`: Pydantic models.

## Infrastructure
- **FastAPI**: Main web framework.
- **SQLAlchemy 2.0**: Async database ORM.
- **Alembic**: Database migrations.
- **Docker Compose**: Orchestration of app and DB.
- **OpenTelemetry**: Tracing enabled on API endpoints and DB calls.

## Decisions
- Choice of async SQLAlchemy: Necessary for FastAPI performance/non-blocking IO.
- Use of Pydantic v2: Native support in FastAPI and high performance.

## Risks / Trade-offs
- [Risk] Async DB complexity → Mitigation: Use standard patterns from the beginning.
- [Risk] OTel overhead → Mitigation: Configure sampling.

## Migration Plan
- N/A (Initial setup).

## Open Questions
- None.
