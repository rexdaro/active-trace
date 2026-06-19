# activia-trace

Plataforma de gestión académica y trazabilidad multi-tenant que opera como capa de orquestación sobre Moodle. Consolida calificaciones, detecta alumnos atrasados, gestiona comunicaciones salientes con flujo de aprobación, equipos docentes, encuentros, coloquios, liquidaciones de honorarios y auditoría completa. Cada institución opera como un tenant aislado — sus datos nunca se cruzan.

---

## ¿Qué problema resuelve?

Un LMS estándar como Moodle no permite:

- Ver en una sola vista el estado de avance de todos los alumnos por comisión
- Detectar y comunicar atrasos de forma masiva y personalizada
- Coordinar equipos docentes con vigencias, jerarquías y clonado entre períodos
- Calcular liquidaciones de honorarios contra la actividad efectiva del docente
- Auditar con precisión quién hizo qué, cuándo y sobre qué dato académico

activia-trace resuelve todo eso sin reemplazar al LMS: lo complementa.

---

## Stack

### Backend

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.13 |
| Framework | FastAPI (async) |
| ORM | SQLAlchemy 2.0 async |
| Migraciones | Startup automático con `create_all` + migraciones por código |
| Base de datos | PostgreSQL 15 (SQLite en tests) |
| Validación | Pydantic v2 |
| Auth | JWT (access + refresh rotation) |
| Cifrado en reposo | AES-256 para PII |
| Integraciones | Moodle Web Services |
| Testing | pytest + httpx, ~720 tests, suite completa verde |

### Frontend

| Componente | Tecnología |
|---|---|
| Framework | React 18 + TypeScript |
| Bundler | Vite |
| Estado global | Context + hooks locales (feature-based) |
| HTTP | Axios (cliente centralizado con refresh transparente) |
| Rutas | React Router v6 con guards de rol por ruta (`RoleRoute`) |
| Estilos | CSS vanilla con variables + layout system propio |

### Infraestructura

| Componente | Tecnología |
|---|---|
| Contenedores | Docker + docker-compose |
| Deploy | Easypanel |

---

## Arquitectura

El sistema sigue Clean Architecture con flujo unidireccional estricto:

```
Router → Service → Repository → Model
```

Las queries SQL viven exclusivamente en los repositories. Los services contienen la lógica de negocio. Los routers no conocen la base de datos.

### Multi-tenancy

Toda entidad lleva `tenant_id`. Los repositories filtran por tenant por defecto — un query sin scope de tenant falla en code review. Los datos de una institución son completamente inaccesibles desde otra.

### RBAC

Permisos granulares con la forma `modulo:accion` (ej: `comunicacion:aprobar`, `liquidaciones:cerrar`). Roles y permisos en base de datos, ruteo protegido por `check_permission()` + `RoleRoute` en frontend. Las rutas frontend están agrupadas por rol:

| Ruta | Roles |
|---|---|
| Dashboard, Avisos | Todos los autenticados |
| Calificaciones, Atrasados, Tareas, Encuentros | PROFESOR, TUTOR, COORDINADOR, ADMIN |
| Comunicaciones | PROFESOR, COORDINADOR, ADMIN |
| Equipos docentes | COORDINADOR, ADMIN |
| Liquidaciones, Facturas, Salarios | FINANZAS, ADMIN |
| Coloquios | ALUMNO, PROFESOR, COORDINADOR, ADMIN |
| Auditoría | COORDINADOR, ADMIN, FINANZAS |
| Estructura, Usuarios | ADMIN |

### Auditoría

Registro append-only de toda acción significativa: actor, impersonación activa si corresponde, materia, código de acción estandarizado, IP, user agent, filas afectadas. Ningún registro puede modificarse ni eliminarse (triggers SQLAlchemy `before_update` / `before_delete`).

---

## Módulos principales

| Módulo | Descripción |
|---|---|
| Auth | Login JWT con refresh rotation, 2FA TOTP, rate limiting |
| Estructura académica | Carreras, cohortes, materias (catálogo único por tenant) |
| Usuarios y asignaciones | PII cifrada, roles con vigencia temporal, jerarquía docente |
| Equipos docentes | Asignación masiva, clonar entre períodos, modificar vigencia en bloque |
| Padrón | Import xlsx/csv + Moodle WS, versionado (la carga nueva no destruye la anterior) |
| Calificaciones | Import desde LMS con preview/confirm, notas numéricas y textuales, umbral configurable por docente, finalización por materia |
| Análisis | Alumnos atrasados, ranking de actividades, TPs sin corregir, monitores por rol con scope |
| Comunicaciones | Envío masivo con flujo de aprobación, preview obligatorio, cola async |
| Encuentros y guardias | Slots recurrentes, instancias, export |
| Coloquios | Convocatorias con cupo, reserva de turno por alumno, resultados consolidados |
| Avisos | Tablón con scope (materia/cohorte/rol), severidad, acknowledgment por actor |
| Tareas internas | Workflow entre docentes y coordinación, comentarios, seguimiento |
| Liquidaciones | Grilla salarial (base + plus), cálculo por docente, cierre inmutable, separación factura/general |
| Facturas | Carga con fecha, monto y período, registro contable |
| Auditoría y métricas | Panel de interacciones, log completo con filtros y paginación, scope por coordinador |

---

## Estado del desarrollo

| Módulo | Backend | Frontend |
|---|---|---|
| Auth + 2FA | ✅ | ✅ |
| Estructura académica | ✅ | ✅ |
| Usuarios y asignaciones | ✅ | ✅ |
| Equipos docentes | ✅ | ✅ |
| Padrón | ✅ | — |
| Calificaciones | ✅ | ✅ |
| Análisis + Atrasados | ✅ | ✅ |
| Comunicaciones | ✅ | ✅ |
| Encuentros y guardias | ✅ | ✅ |
| Coloquios | ✅ | ✅ |
| Avisos | ✅ | ✅ |
| Tareas internas | ✅ | ✅ |
| Liquidaciones | ✅ | ✅ |
| Facturas | ✅ | ✅ |
| Auditoría | ✅ | ✅ |
| Perfil | ✅ | ✅ |
| Inbox / mensajería | ✅ | ✅ |

### Pendiente / Mejora continua

- RBAC backend: pasar `check_permission` de demo mode a verificación real contra base de datos
- Integración Moodle real (el adapter está armado, falta conexión con instancia productiva)
- Tests frontend (actualmente la cobertura es backend)
- Migraciones formales con Alembic (hoy el startup crea tablas automáticamente)

---

## Correr localmente

### Requisitos

- Docker y docker-compose
- Python 3.13
- Node.js 20+

### Backend

```bash
git clone https://github.com/rexdaro/active-trace.git
cd active-trace
cp .env.example .env
docker-compose up -d
```

La API queda en `http://localhost:8000`. Health check: `GET /health`.
Las tablas se crean automáticamente al iniciar. Para seed de roles y permisos:

```bash
docker-compose exec api python -m app.db.seed
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Disponible en `http://localhost:5173`.

### Tests

```bash
docker-compose exec api pytest tests/ -v
```

Suite completa ~720 tests, todos verdes.

---

## Variables de entorno

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | Connection string de PostgreSQL |
| `SECRET_KEY` | Clave para firma de JWT |
| `AES_KEY` | Clave AES-256 para cifrado de PII |
| `MOODLE_URL` | URL base de la instancia Moodle |
| `MOODLE_TOKEN` | Token de Web Services de Moodle |

---

## Estructura del proyecto

```
activia-trace/
├── app/
│   ├── routers/          # Endpoints FastAPI
│   ├── services/         # Lógica de negocio
│   ├── repositories/     # Queries a la base de datos
│   ├── models/           # Modelos SQLAlchemy
│   ├── schemas/          # DTOs Pydantic
│   ├── core/             # Configuración, auth, cifrado, RBAC
│   ├── middleware/       # AuditLogMiddleware
│   ├── integrations/     # Moodle WS
│   └── db/               # Seed, migraciones
├── frontend/
│   └── src/
│       ├── pages/        # Páginas por módulo
│       ├── components/   # AppLayout, ProtectedRoute, RoleRoute
│       └── services/     # API client, auth helpers
├── tests/                # ~720 tests pytest
├── openspec/             # SDD artifacts (changes, specs)
└── docker-compose.yml
```

---

## Documentación

La fuente de verdad del dominio vive en `knowledge-base/`:

- `01_vision_y_objetivos.md` — propósito y valor por actor
- `03_actores_y_roles.md` — roles, RBAC y matriz de permisos
- `04_modelo_de_datos.md` — entidades y relaciones
- `05_reglas_de_negocio.md` — reglas codificadas (RN-XX)
- `07_flujos_principales.md` — flujos end-to-end
- `10_preguntas_abiertas.md` — decisiones de dominio pendientes

Documentos de diseño en `openspec/changes/`.
