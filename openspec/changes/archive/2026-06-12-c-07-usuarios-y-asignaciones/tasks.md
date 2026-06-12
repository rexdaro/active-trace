# Tasks: C-07-usuarios-y-asignaciones

## Phase 1: Planning and Setup
- [x] 1.1 Definir requerimientos de usuarios (PII cifrada, multi-tenant, vigencia)
- [x] 1.2 Diseñar esquema de asignaciones (Usuario ↔ Rol ↔ contexto, responsable_id)

## Phase 2: Implementation
- [x] 2.1 Implementar modelo `Usuario` con hybrid properties de cifrado AES-256-GCM
- [x] 2.2 Implementar modelo `Asignacion` con vigencia y jerarquía
- [x] 2.3 Schema Pydantic con CBU opcional y email validado
- [x] 2.4 Endpoint `POST /api/admin/usuarios` con guard `usuarios:gestionar` y tenant desde JWT
- [x] 2.5 Endpoint `POST /api/asignaciones` con guard `equipos:asignar` y tenant desde JWT
- [x] 2.6 Migración Alembic `814fd5c777fb` (tablas `usuarios`, `asignaciones`)
- [x] 2.7 Fix: tenant_id hardcodeado reemplazado por `user.tenant_id` del JWT
- [x] 2.8 Fix: `cbu` hecho nullable en modelo y schema

## Phase 3: Testing and Verification
- [x] 3.1 Tests unitarios: cifrado round-trip de PII (test_models/test_user.py)
- [x] 3.2 Tests de integración: validación de asignaciones (test_routers/test_asignaciones.py)
