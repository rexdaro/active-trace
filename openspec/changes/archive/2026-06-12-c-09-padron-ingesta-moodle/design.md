# Design: C-09 — Padrón Ingesta Moodle

## Context

El sistema necesita poblar el modelo de alumnos por materia×cohorte para que las épicas de calificaciones, rankings y comunicaciones tengan datos sobre los cuales operar. El padrón es la base de toda la trazabilidad académica.

## Goals / Non-Goals

**Goals:**
- Modelo versionado de padrón: cada import crea una `VersionPadron`; solo una activa por materia×cohorte.
- Import desde archivo xlsx/csv con preview y confirmación en dos pasos.
- Integración Moodle WS para sync automática (nocturna + on-demand).
- Vaciado de datos con scope aislado por usuario (RN-04), auditado como `PADRON_CARGAR`.
- Aislamiento multi-tenant en todas las queries.

**Non-Goals:**
- Sincronización bidireccional (solo lectura desde Moodle).
- Transformación ni normalización de nombres de alumnos.
- Interfaz de usuario frontend (solo API).

## Architecture Overview

### Capas afectadas

```
routers/padron.py          → POST /preview, /confirm, /{materia_id}/v2, DELETE /{materia_id}/datos, POST /sync
  └─ services/padron.py    → Lógica de versionado, import, preview, confirm, vaciado
       ├─ repositories/padron.py  → Queries scoped por tenant sobre VersionPadron + EntradaPadron
       ├─ integrations/moodle_ws.py → Cliente Moodle WS (sync usuarios/actividades)
       └─ workers/sync_nightly.py → Tarea programada de sync nocturna
```

### Flujo de Import (archivo)

1. Usuario sube archivo a `POST /preview`
2. `services.padron.PadronService.preview()` parsea el archivo (xlsx via openpyxl, csv via csv module), genera preview con filas detectadas, columnas mapeadas, errores de formato
3. Usuario revisa preview y confirma vía `POST /confirm` con `preview_token`
4. `services.padron.PadronService.confirm()` crea `VersionPadron` con `activa=True`, desactiva versión anterior para (materia, cohorte), inserta `EntradaPadron` masivamente
5. Se registra audit `PADRON_CARGAR`

### Flujo de Sync Moodle WS

1. On-demand: `POST /sync` con `materia_id` opcional gatilla sync inmediata
2. Nocturna: worker `sync_nightly` recorre materias activas, llama a `moodle_ws.get_participants(materia_id)` y `moodle_ws.get_activities(materia_id)`
3. El cliente WS usa token de servicio configurado por tenant (`moodle_token` en modelo Tenant)
4. Errores de conexión → retry 3 veces con backoff → si persiste → `502 Bad Gateway`
5. Fallback: si el tenant no tiene `moodle_ws_url`, la sync se salta (solo import manual)

## Data Model

### VersionPadron

```yaml
Table: versiones_padron
  id: UUID PK
  tenant_id: UUID FK → Tenant
  materia_id: UUID FK → Materia
  cohorte_id: UUID FK → Cohorte
  archivo_nombre: str       # nombre original del archivo subido / "moodle-sync"
  archivo_hash: str         # SHA-256 del contenido (evitar reimport idéntico)
  origen: enum              # Archivo | MoodleWS
  cargado_por: UUID FK → Usuario
  cargado_at: datetime
  activa: bool              # única activa por (materia_id, cohorte_id)
```

### EntradaPadron

```yaml
Table: entradas_padron
  id: UUID PK
  version_id: UUID FK → VersionPadron
  tenant_id: UUID FK → Tenant
  usuario_id: UUID FK → Usuario (nullable — alumno puede no tener cuenta aún)
  nombre: str               # desnormalizado
  apellidos: str            # desnormalizado
  email: str                # cifrado AES-256-GCM
  comision: str | null
  regional: str | null
```

### Constraints
- Unique index `(tenant_id, materia_id, cohorte_id)` where `activa = true`
- FK de EntradaPadron → VersionPadron con CASCADE delete
- Tenant isolation via `tenant_id` en todas las tablas

## API Design

### POST /api/v1/padron/preview
- **Request**: multipart/form-data con archivo xlsx/csv + `materia_id` + `cohorte_id`
- **Response**: `{ preview_token, columnas_detectadas, filas_count, errores[] }`
- **Permission**: `padron:importar`

### POST /api/v1/padron/confirm
- **Request**: `{ preview_token }`
- **Response**: `{ version_id, entradas_count }`
- **Effect**: crea VersionPadron activa, desactiva anterior, inserta entradas, audita
- **Permission**: `padron:importar`

### DELETE /api/v1/padron/{materia_id}/datos
- **Effect**: elimina SOLO las versiones de padrón cargadas por el usuario autenticado en esa materia (scope RN-04). Registra audit `PADRON_CARGAR`.
- **Permission**: `padron:vaciar`

### POST /api/v1/padron/sync
- **Request**: `{ materia_id (opcional) }`
- **Response**: `{ status, materias_procesadas, errores[] }`
- **Permission**: `padron:sincronizar`

### GET /api/v1/padron/{materia_id}/versiones
- **Response**: lista de VersionPadron con metadata (activa, fecha, origen, entradas_count)
- **Permission**: `padron:ver`

## Decisions

| Decisión | Opción | Razón |
|----------|--------|-------|
| Versionado no destructivo | Activar nueva → desactivar anterior | Conserva histórico; el borrado solo ocurre explícitamente (F1.5) |
| Preview en dos pasos | Token efímero en memoria/cache | Evita re-procesar el archivo; el cliente confirma explícitamente |
| Email cifrado en EntradaPadron | AES-256-GCM via `app/core/security.py` | Consistente con política de PII cifrado del proyecto |
| usuario_id nullable | FK nullable | Alumno puede existir en el padrón antes de tener cuenta en el sistema |
| CASCADE en VersionPadron→EntradaPadron | ON DELETE CASCADE | Si se elimina una versión, las entradas se limpian automáticamente |

## Risks / Trade-offs

- [Risk] Archivos xlsx grandes causan timeout en request sincrónica → Mitigation: preview es rápida (lee cabeceras + sample); confirm procesa en worker si > 500 filas
- [Risk] RN-04 vs RN-05: RN-05 dice "reemplazo completo del padrón de esa materia", pero RN-04 dice "scope aislado por usuario" → Mitigation: el versionado de padrón NO es por usuario, es por materia×cohorte. La RN-04 aplica al VACIADO, no al import. Clarificamos que son operaciones diferentes.
- [Risk] Moodle WS versiones distintas (2.x vs 4.x) → Mitigation: el cliente abstrae diferencias con adapter pattern

## Migration Plan

1. Crear migración Alembic con tablas `version_padron` y `entrada_padron`
2. Agregar índices únicos parciales para la constraint de versión activa única
3. No hay rollback de datos (schema-only migration)

## Open Questions

- ¿El nightly sync debe ser por tenant o global? → Inicialmente global, filtrado por tenants con `moodle_ws_url` configurado
- ¿Debemos soportar xlsx con macros (.xlsm)? → No en v1; solo `.xlsx` y `.csv`
