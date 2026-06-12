# Design: C-07-usuarios-y-asignaciones

## Architecture Overview
Dos modelos nuevos (`Usuario`, `Asignacion`) que extienden `Base`, `TimestampMixin` y `TenantMixin`. Los atributos PII se cifran con AES-256-GCM vía hybrid properties que interceptan getter/setter. El tenant se obtiene del JWT autenticado (no se acepta como parámetro).

## Components
- **Modelos**: `Usuario` (app/models/user.py), `Asignacion` (app/models/asignacion.py)
- **Schemas**: `UsuarioCreate`, `UsuarioRead` (app/schemas/usuario.py), `AsignacionCreate`, `AsignacionRead` (app/schemas/asignacion.py)
- **Routers**: `admin.py` (/api/admin/usuarios), `asignaciones.py` (/api/asignaciones)
- **Auth**: guards `check_permission("usuarios:gestionar")` y `check_permission("equipos:asignar")`

## Data Model

### Usuario (tabla `usuarios`)
| Campo | Tipo | Notas |
|-------|------|-------|
| id | UUID | PK |
| tenant_id | UUID | FK → tenants.id |
| email | String (cifrado) | Unique por tenant |
| dni | String (cifrado) | |
| cuil | String (cifrado) | |
| cbu | String? (cifrado) | Nullable |
| created_at/updated_at/deleted_at | DateTime | TimestampMixin |

### Asignacion (tabla `asignaciones`)
| Campo | Tipo | Notas |
|-------|------|-------|
| id | UUID | PK |
| tenant_id | UUID | FK → tenants.id |
| user_id | UUID | FK → usuarios.id |
| role_id | UUID | FK → roles.id |
| contexto_id | UUID | Carrera/Materia/Cohorte |
| responsable_id | UUID? | FK → usuarios.id, jerarquía |
| desde | DateTime | Inicio vigencia |
| hasta | DateTime? | Fin vigencia (null = indefinido) |

## API Changes
- `POST /api/admin/usuarios` → crea usuario, requiere `usuarios:gestionar`
- `POST /api/asignaciones` → crea asignación, requiere `equipos:asignar`

## Implementation Notes
- Cifrado AES-256-GCM via `app/core/security.py` (encrypt/decrypt)
- Hybrid properties en `Usuario`: el setter cifra, el getter descifra
- `cbu` es nullable tanto en columna como en schema
- Los routers usan `user.tenant_id` del JWT autenticado — no hay tenant_id en el body
- La migración `814fd5c777fb` crea ambas tablas con FK correspondientes
- Las asignaciones vencidas se conservan como histórico
