# Proposal: C-07-usuarios-y-asignaciones

## Why
El sistema necesita un modelo de **Usuario** con datos PII (email, DNI, CUIL, CBU) cifrados en reposo, y un mecanismo de **Asignacion** que vincule usuarios con roles y contextos académicos (materia/carrera/cohorte) con vigencia temporal. Este es el piso para todos los módulos de dominio (equipos docentes, padrones, calificaciones, etc.).

## What Changes
- [x] Modelo `Usuario` con cifrado AES-256-GCM en atributos PII (email, dni, cuil, cbu opcional)
- [x] Modelo `Asignacion` (Usuario ↔ Rol ↔ contexto) con vigencia y jerarquía `responsable_id`
- [x] Schema Pydantic con CBU opcional y validación de email
- [x] Endpoint `POST /api/admin/usuarios` con guard `usuarios:gestionar` y tenant desde JWT
- [x] Endpoint `POST /api/asignaciones` con guard `equipos:asignar` y tenant desde JWT
- [x] Migración Alembic `814fd5c777fb` (tablas `usuarios`, `asignaciones`)
- [x] Tests: cifrado round-trip (test_models/test_user.py), validación asignaciones (test_routers/test_asignaciones.py)

## Impact
- Desbloquea C-08 (equipos-docentes), C-09 (padron-ingesta-moodle), C-13, C-14, C-16, C-18, C-20
- Los módulos existentes (auth, estructura académica) no se ven afectados
- CBU opcional permite usuarios sin datos bancarios (alumnos, tutores)
