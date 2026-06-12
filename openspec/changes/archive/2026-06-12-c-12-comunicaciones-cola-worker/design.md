# Design: C-12 — Comunicaciones y Cola Worker

## Context

Activia-Trace ya detecta alumnos atrasados (C-11), pero los docentes no tienen forma de comunicarse con ellos desde el sistema. Hoy la comunicación se hace manualmente sin trazabilidad.

Este cambio implementa el modelo `Comunicacion` con máquina de estados (RN-15), preview obligatorio (RN-16), aprobación configurable (RN-17), worker asíncrono de despacho, plantillas con variables, y auditoría completa.

## Goals / Non-Goals

**Goals:**
- Modelo `Comunicacion` con estado Pendiente → Enviando → Enviado/Error/Cancelado
- Preview obligatorio con renderizado de plantillas (Jinja2)
- Envío masivo con cola asíncrona
- Aprobación humana configurable por tenant (flag booleano en Tenant)
- Worker de despacho con reintentos y backoff
- Tracking de estados por lote
- Auditoría de todas las operaciones

**Non-Goals:**
- Mensajería interna (bandeja del docente) — será C-13 o posterior
- Tablón de avisos del sistema — será otro change
- Configuración SMTP multi-tenant (credenciales diferentes por tenant) — se difiere
- Cola externa (Redis/Celery) — alcance no lo justifica

## Decisions

### D1 — Worker in-process vs Celery/Redis
**Decisión**: Worker in-process con `asyncio.create_task` + loop con sleep.
**Rationale**: El volumen estimado (< 500 emails/día por tenant) no justifica la complejidad operativa de Redis/Celery. Si escala, se migra a cola externa sin cambiar el modelo de datos.
**Alternativa**: Celery + Redis → descartada por over-engineering para el alcance actual.

### D2 — Flag `requiere_aprobacion` en modelo Tenant
**Decisión**: Agregar columna `requiere_aprobacion: bool` a la tabla `tenants`.
**Rationale**: Es una decisión por tenant, naturalmente parte de su configuración. Evita una tabla separada de configuraciones.
**Alternativa**: Tabla `tenant_config` → más genérica pero introduce complejidad innecesaria para un solo flag.

### D3 — Cifrado de destinatario
**Decisión**: Mismo patrón que `EntradaPadron.email` — columna `_destinatario` cifrada vía `encrypt()/decrypt()`, property + setter públicos.
**Rationale**: Consistencia con el modelo existente. El email del alumno es dato sensible (GDPR).

### D4 — Jinja2 con StrictUndefined
**Decisión**: Las plantillas usan Jinja2 `Environment(undefined=StrictUndefined)`.
**Rationale**: Si falta una variable en el preview, falla temprano con error claro en lugar de renderizar silenciosamente "undefined". Esto evita comunicaciones con placeholders sin reemplazar.

### D5 — Elegibilidad del worker
**Decisión**: El worker solo procesa mensajes Pendiente cuyo tenant NO requiera aprobación, o que estén en un lote aprobado. Los mensajes Pendiente con `lote_aprobado = false` (o tenant con flag activo sin aprobación explícita) se saltan.
**Rationale**: No se necesita un campo adicional — se deriva de: `tenant.requiere_aprobacion == false OR lote_aprobado == true`.

### D6 — Preview store en memoria
**Decisión**: `_preview_store: dict[str, dict]` con TTL de 15 minutos, mismo patrón que `PadronService` y `CalificacionesService`.
**Rationale**: Consistencia con el resto del códigobase. Para entornos multi-instancia en el futuro, migrar a Redis.

## Architecture

### Data Model
```
Comunicacion {
  id              : UUID PK
  tenant_id       : UUID FK → Tenant
  enviado_por     : UUID FK → Usuario
  materia_id      : UUID FK → Materia
  _destinatario   : String (cifrado)
  asunto          : String
  cuerpo          : Text
  estado          : String (Pendiente | Enviando | Enviado | Error | Cancelado)
  lote_id         : UUID (nullable, agrupa envíos masivos)
  lote_aprobado   : Boolean (default false)
  enviado_at      : DateTime (nullable)
  created_at      : DateTime
  updated_at      : DateTime
  deleted_at      : DateTime (nullable)
}
```

### State Machine (RN-15)
```
Pendiente ──→ Enviando ──→ Enviado
    │                       (OK)
    │                   ──→ Error
    │                       (Fail)
    └──→ Cancelado
         (solo desde Pendiente)
```

### Endpoints
```
POST /api/v1/comunicaciones/preview         → preview_token
POST /api/v1/comunicaciones/confirm          → lote_id
GET  /api/v1/comunicaciones/lotes            → listar lotes
GET  /api/v1/comunicaciones/lotes/{id}       → detalle lote
POST /api/v1/comunicaciones/lotes/{id}/aprobar   → aprobar lote
POST /api/v1/comunicaciones/{id}/aprobar     → aprobar individual
POST /api/v1/comunicaciones/lotes/{id}/rechazar  → rechazar lote
POST /api/v1/comunicaciones/{id}/cancelar    → cancelar individual
GET  /api/v1/comunicaciones/estados          → panel de estados
```

### File Structure
```
app/models/comunicacion.py           → Modelo + Estado enum
app/schemas/comunicacion.py           → Pydantic schemas
app/repositories/comunicaciones.py    → Repository
app/services/comunicaciones.py        → Service (preview/confirm/approve/cancel)
app/workers/comunicaciones.py         → Worker de despacho
app/routers/comunicaciones.py         → Router (9 endpoints)
app/db/seed.py                        → + permisos comunicacion:enviar, comunicacion:aprobar
alembic/versions/0NN_comunicaciones.py → Migración
```

## Risks / Trade-offs

- **[Risk] Worker bloqueante con SMTP lento** → Mitigation: timeouts configurables por email (30s), reintentos con backoff (3 intentos), el worker no bloquea requests HTTP.
- **[Risk] Preview store en memoria perdida al reiniciar** → Acceptable: el usuario solo pierde previews no confirmados. Los confirmados ya están en DB.
- **[Risk] Alta concurrencia de aprobaciones** → Mitigation: transiciones atómicas en repositorio con verificación de estado origen.
- **[Risk] Jinja2 template injection** → Mitigation: las plantillas son provistas por el sistema (no por el usuario). Si se permiten plantillas custom, agregar sandboxing.

## Migration Plan

1. Agregar columna `requiere_aprobacion` a tabla `tenants` (default false) — migration separada o incluida
2. Crear tabla `comunicaciones` con índices
3. Migrar en staging primero
4. Rollback: `alembic downgrade -1` (drop table comunicaciones, drop column)
