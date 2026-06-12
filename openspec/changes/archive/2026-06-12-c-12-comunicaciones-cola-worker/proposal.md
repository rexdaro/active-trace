# Proposal: C-12 — Comunicaciones y Cola Worker

## Why

Activia-Trace ya detecta alumnos atrasados (C-11), pero los docentes no tienen forma de comunicarse con ellos desde el sistema. Hoy la comunicación se hace manualmente (email externo, WhatsApp, aula virtual) sin trazabilidad ni personalización.

**Context**: C-11 expone quiénes están atrasados. El paso siguiente (FL-02 pasos 7-8) es que el PROFESOR seleccione alumnos, previsualice mensajes personalizados y los envíe. Para envíos masivos (FL-04), se necesita un flujo de aprobación por COORDINADOR antes del despacho.

**Current state**: No hay modelo de comunicaciones. No hay cola de envío asíncrona. No hay plantillas con variables de sustitución. No hay preview ni aprobación.

**Desired state**: El sistema cuenta con un modelo `Comunicacion` con máquina de estados (RN-15), preview obligatorio antes de envío (RN-16), aprobación configurable por tenant para envíos masivos (RN-17), worker asíncrono de despacho, plantillas con variables de sustitución, y auditoría completa de todas las operaciones.

## What Changes

1. Modelo `Comunicacion` con estado Pendiente → Enviando → Enviado/Error/Cancelado, destinatario cifrado, lote_id para agrupar envíos masivos.
2. Preview obligatorio antes de encolar (F3.1, RN-16): preview_token en store en memoria, renderizado de plantillas con variables de sustitución (nombre, materia, comisión, etc.).
3. Confirmación de envío que crea registros `Comunicacion` en estado Pendiente agrupados por lote_id (F3.2).
4. Aprobación humana configurable por tenant (F3.3, RN-17): si el tenant requiere aprobación, los mensajes masivos permanecen Pendiente hasta que un usuario con `comunicacion:aprobar` apruebe el lote o mensajes individuales.
5. Worker asíncrono (`workers/comunicaciones.py`) que consume Pendiente → Enviando → envía email vía smtplib → Enviado o Error.
6. Cancelación de comunicaciones Pendiente (individual o por lote).
7. Endpoints REST bajo `/api/v1/comunicaciones` con guard `comunicacion:enviar`.
8. Auditoría con `COMUNICACION_ENVIAR`, `COMUNICACION_APROBAR`, `COMUNICACION_CANCELAR`.
9. Migración Alembic para tabla `comunicaciones`.
10. Seeds de permisos `comunicacion:enviar` y `comunicacion:aprobar`.

## Capabilities

### New Capabilities
- `comunicaciones`: modelo de comunicación saliente con máquina de estados, preview/confirm, worker de despacho asíncrono
- `plantillas`: motor de plantillas con variables de sustitución para personalización por destinatario
- `aprobacion-comunicaciones`: flujo de aprobación humana configurable por tenant para envíos masivos

### No Modified Capabilities
- C-11 (`analisis`): sin cambios, los endpoints de atrasados solo necesitan invocar el nuevo servicio de comunicaciones
- C-04 (`rbac`): se agregan nuevos permisos al catálogo existente

## Impact

### Affected Specifications
- `openspec/specs/comunicaciones/spec-delta.md` — nuevo spec de dominio

### Affected Code
- `app/models/` — nuevo `comunicacion.py` con estado enum
- `app/schemas/` — nuevos esquemas Pydantic para preview, confirm, aprobación, cancelación
- `app/services/` — nuevo `comunicaciones.py` con preview/confirm, template rendering, batch enqueue, approval, cancel
- `app/repositories/` — nuevo `comunicaciones.py`
- `app/routers/` — nuevo `comunicaciones.py`
- `app/workers/` — nuevo `comunicaciones.py` (worker asíncrono)
- `app/db/seed.py` — agregar permisos `comunicacion:enviar`, `comunicacion:aprobar`

### API Changes
- `POST /api/v1/comunicaciones/preview` — preview con lista de destinatarios, asunto, cuerpo (plantilla), retorna renderizados
- `POST /api/v1/comunicaciones/confirm` — confirma envío, crea registros Pendiente con lote_id
- `GET /api/v1/comunicaciones/lotes` — listar lotes de comunicaciones
- `GET /api/v1/comunicaciones/lotes/{lote_id}` — detalle de un lote con estados por destinatario
- `POST /api/v1/comunicaciones/lotes/{lote_id}/aprobar` — aprobar lote completo (`comunicacion:aprobar`)
- `POST /api/v1/comunicaciones/{id}/aprobar` — aprobar mensaje individual (`comunicacion:aprobar`)
- `POST /api/v1/comunicaciones/lotes/{lote_id}/rechazar` — rechazar/cancelar lote completo
- `POST /api/v1/comunicaciones/{id}/cancelar` — cancelar mensaje individual
- `GET /api/v1/comunicaciones/estados` — panel de estado de comunicaciones

### RBAC
- `comunicacion:enviar` → PROFESOR (propio), COORDINADOR, ADMIN
- `comunicacion:aprobar` → COORDINADOR, ADMIN

### Migration Required
- [x] Database migration (comunicaciones)
- [x] Seed de permisos (`comunicacion:enviar`, `comunicacion:aprobar`)
- [x] Configuración por tenant (requiere_aprobacion flag — agregar a modelo Tenant o tabla de config)
- [ ] API version bump
- [ ] User communication needed

## Timeline Estimate

Medium (3-4 semanas). Dependencies: C-11 already done. Governance: ALTO — requiere revisión antes de implementar.

## Risks

- [Risk] Worker de despacho bloqueante si el servidor SMTP es lento → Mitigation: worker con timeouts configurables; reintentos con backoff para fallos transitorios; no bloquea el request del usuario.
- [Risk] Volumen grande de envíos (>1000 destinatarios) → Mitigation: el worker procesa en batches; el preview solo muestra muestra representativa (primeros N).
- [Risk] Configuración SMTP por tenant (credenciales diferentes) → Mitigation: settings centralizados; si se requiere multi-tenant SMTP, diferir a versión posterior con vault de credenciales.
- [Risk] Plantillas con variables de sustitución pueden fallar si falta una variable → Mitigation: Jinja2 con `undefined=StrictUndefined` en preview para detectar errores temprano; error claro al usuario.
