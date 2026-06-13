# Proposal: C-19-panel-auditoria-metricas

## Why
El sistema necesita dashboards de uso (F9.1) y un log completo de auditoría consultable (F9.2) basado en el AuditLog implementado en C-05. Requerido para que ADMIN y COORDINADOR puedan monitorear la actividad del sistema.

## What Changes
1. Endpoint `GET /api/v1/auditoria/metricas` — panel de interacciones: acciones por día, estado comunicaciones por docente, últimas N acciones.
2. Endpoint `GET /api/v1/auditoria/log` — log completo con filtros (rango fechas, materia, usuario, estado).
3. Guard `auditoria:ver` (ADMIN, COORDINADOR `(propio)`, FINANZAS).
4. Solo lectura sobre `AuditLog` existente.

## Impact
- **API**: New router `app/routers/auditoria.py`.
- **Permissions**: New permission `auditoria:ver`.
- **Models**: No new models (reusa AuditLog de C-05).
