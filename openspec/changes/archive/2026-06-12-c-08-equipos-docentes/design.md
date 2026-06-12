# Design: C-08 — Equipos Docentes

## Context

El modelo `Asignacion` (C-07) ya existe y soporta tenant_id, user_id, role_id, contexto_id, responsable_id, desde, hasta. Este change construye **operaciones de gestión sobre conjuntos de asignaciones** — no agrega modelos nuevos.

## Goals / Non-Goals

**Goals:**
- Query "mis equipos" filtrando por user_id del JWT (docente autenticado)
- Asignación masiva: crear N asignaciones en un solo request con transacción atómica
- Clonar equipo: copiar asignaciones vigentes de origen a destino ajustando fechas
- Modificar vigencia: actualizar desde/hasta de todas las asignaciones de un equipo
- Export: generar CSV descargable con cabeceras estándar
- Audit `ASIGNACION_MODIFICAR` en cada operación mutante
- Aislamiento multi-tenant siempre activo

**Non-Goals:**
- Modificar el modelo Asignacion (no se agregan campos)
- Interfaz de usuario frontend (solo API)
- Validación de no solapamiento de vigencias (se puede agregar en versión futura)

## Architecture Overview

### Capas afectadas

```
routers/equipos.py          → GET /mis-equipos, GET /, POST /asignacion-masiva, POST /clonar, PUT /vigencia, GET /export
  └─ services/equipos.py    → Lógica de negocio: mis_equipos, asignar_masiva, clonar, modificar_vigencia, exportar
       └─ app/models/asignacion.py  → Queries vía SQLAlchemy con filtro tenant desde JWT
```

No se necesita capa de repositories nueva — las queries son directas sobre `Asignacion` con filtros estándar. Si en el futuro el volumen lo justifica, se extrae un repositorio.

## Data Model

Sin cambios. Se opera exclusivamente sobre `Asignacion` (tabla `asignaciones`):

| Campo | Tipo | Uso en C-08 |
|-------|------|-------------|
| id | UUID PK | Identificador de cada asignación |
| tenant_id | UUID FK | Filtro obligatorio desde JWT |
| user_id | UUID FK | Filtro en mis-equipos, destino en masiva/clonar |
| role_id | UUID FK | Rol del docente en el equipo |
| contexto_id | UUID | Materia/Carrera/Cohorte — identifica el equipo |
| responsable_id | UUID? | Se replica en clonado |
| desde | DateTime | Vigencia: se modifica en bloque o se ajusta en clonado |
| hasta | DateTime? | Vigencia: se modifica en bloque o se ajusta en clonado |

### Concepto de "equipo"

Un **equipo docente** se define como el conjunto de asignaciones que comparten el mismo `contexto_id` (materia×carrera×cohorte). No hay una tabla `Equipo` — es una agrupación lógica.

## API Design

### GET /api/equipos/mis-equipos

- **Response**: `AsignacionRead[]` filtrado por `user_id = current_user.id`
- **Permission**: `equipos:asignar`
- **F4.2**: docente autenticado ve sus propias comisiones

### GET /api/equipos

- **Query params**: `materia_id`, `carrera_id`, `cohorte_id`, `role_id`, `user_id`, `vigente` (bool)
- **Response**: `AsignacionRead[]` del tenant con filtros opcionales
- **Permission**: `equipos:asignar`
- **F4.3**: coordinación consulta todas las asignaciones del tenant

### POST /api/equipos/asignacion-masiva

- **Request**:
  ```json
  {
    "asignaciones": [
      {
        "user_id": "uuid",
        "role_id": "uuid",
        "contexto_id": "uuid",
        "responsable_id": "uuid|null",
        "desde": "2025-03-01T00:00:00",
        "hasta": "2025-12-31T00:00:00"
      }
    ]
  }
  ```
- **Response**: `{ creadas: int, asignaciones: AsignacionRead[] }`
- **Effect**: transacción atómica — todas se crean o ninguna. Registra audit `ASIGNACION_MODIFICAR` con `filas_afectadas = len(asignaciones)`.
- **Permission**: `equipos:asignar`
- **F4.4**: asignar múltiples docentes en bloque

### POST /api/equipos/clonar

- **Request**:
  ```json
  {
    "origen_contexto_id": "uuid",
    "destino_contexto_id": "uuid",
    "nuevo_desde": "2026-03-01T00:00:00",
    "nuevo_hasta": "2026-12-31T00:00:00"
  }
  ```
- **Response**: `{ clonadas: int, asignaciones: AsignacionRead[] }`
- **Effect**:
  1. Query todas las asignaciones activas (donde `hasta IS NULL OR hasta > now()`) para `origen_contexto_id`
  2. Duplica cada una con `contexto_id = destino_contexto_id`, `desde = nuevo_desde`, `hasta = nuevo_hasta`, nuevo UUID
  3. Transacción atómica. Audit con `filas_afectadas`.
- **Permission**: `equipos:asignar`
- **F4.5, RN-12**: clonar equipo entre cohortes

### PUT /api/equipos/vigencia

- **Request**:
  ```json
  {
    "contexto_id": "uuid",
    "nuevo_desde": "2026-03-01T00:00:00",
    "nuevo_hasta": "2026-12-31T00:00:00"
  }
  ```
- **Response**: `{ modificadas: int }`
- **Effect**: UPDATE all `Asignacion` con ese `contexto_id` AND `tenant_id = user.tenant_id`. Audit con `filas_afectadas`.
- **Permission**: `equipos:asignar`
- **F4.6**: modificar vigencia general del equipo

### GET /api/equipos/export

- **Query params**: `contexto_id` (obligatorio)
- **Response**: `text/csv` con UTF-8 BOM
- **CSV Headers**: `user_id, email, dni, nombre, rol, contexto_id, responsable_id, desde, hasta, estado_vigencia`
- **Permission**: `equipos:asignar`
- **F4.7**: exportar equipo a archivo

## Flows

### Flujo de clonado

```
POST /api/equipos/clonar
  → EquiposService.clonar(origen, destino, nuevo_desde, nuevo_hasta)
     → SELECT * FROM asignaciones
        WHERE tenant_id = $tenant
          AND contexto_id = $origen
          AND (hasta IS NULL OR hasta > now())
     → Para cada asignación activa:
          crear nueva Asignacion con:
            - mismo user_id, role_id, responsable_id
            - contexto_id = $destino
            - desde = $nuevo_desde
            - hasta = $nuevo_hasta
            - tenant_id = $tenant (del JWT)
     → db.commit()
     → AuditService.log_action("ASIGNACION_MODIFICAR", ...)
  → Response: { clonadas: N }
```

### Flujo de export

```
GET /api/equipos/export?contexto_id=X
  → EquiposService.exportar(contexto_id)
     → SELECT a.*, u.email, u.dni, r.nombre as rol
        FROM asignaciones a
        JOIN usuarios u ON a.user_id = u.id
        JOIN roles r ON a.role_id = r.id
        WHERE a.tenant_id = $tenant AND a.contexto_id = $contexto
     → Generar CSV en memoria con cabeceras
     → Determinar estado_vigencia: now() BETWEEN desde AND (hasta OR 'infinity')
  → StreamingResponse(media_type="text/csv", headers={"Content-Disposition": "attachment; filename=equipo-{contexto_id}.csv"})
```

## Decisions

| Decisión | Opción | Razón |
|----------|--------|-------|
| Sin repositorio nuevo | Queries directas desde service | Asignacion tiene queries simples; complejidad no justifica capa extra |
| Sin modelo Equipo | Agrupación lógica por contexto_id | No hay atributos de equipo que modelar; contexto_id es suficiente |
| Clonado sincrónico | Batch insert en request | Volumen esperado < 500 asignaciones; si escala se migra a worker |
| CSV con UTF-8 BOM | `\ufeff` al inicio | Garantiza que Excel abra los acentos correctamente en Windows |
| estado_vigencia derivado | Calculado al vuelo en export | No se guarda en DB; se deriva de desde/hasta vs now() |

## Risks / Trade-offs

- [Risk] Clonado con muchas asignaciones (>500) puede exceder timeout HTTP → Mitigation: monitorear en staging; si ocurre, implementar con worker asíncrono.
- [Risk] No hay validación de solapamiento de vigencias al clonar → Mitigation: se documenta como mejora post-MVP. El coordinador es responsable de no duplicar equipos en el mismo período.
- [Risk] Export expone PII (email, dni) del docente → Mitigation: el export requiere `equipos:asignar` (solo COORDINADOR/ADMIN), que ya tienen acceso a estos datos.

## Migration Plan

No se requiere migración. Todo el cambio es sobre el modelo `Asignacion` existente.
