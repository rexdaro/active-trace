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
| Migraciones | Alembic |
| Base de datos | PostgreSQL 15 |
| Validación | Pydantic v2 |
| Auth | JWT (access 15min + refresh rotation) + Argon2id |
| Cifrado en reposo | AES-256 para PII (DNI, CUIL, CBU, email) |
| Background jobs | Worker async (cola de comunicaciones) |
| Integraciones | N8N + Moodle Web Services |
| Observabilidad | OpenTelemetry + logs estructurados JSON |
| Testing | pytest + httpx, cobertura ≥80% líneas / ≥90% reglas de negocio |

### Frontend

| Componente | Tecnología |
|---|---|
| Framework | React 18 + TypeScript |
| Bundler | Vite |
| Server state | TanStack Query v5 |
| Formularios | React Hook Form + Zod |
| Estilos | Tailwind CSS |
| HTTP | Axios (cliente centralizado con refresh transparente) |
| Estructura | Feature-based modules |

### Infraestructura

| Componente | Tecnología |
|---|---|
| Contenedores | Docker + docker-compose |
| Deploy | Easypanel |
| Observabilidad | Logs estructurados JSON + OpenTelemetry |

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

Permisos granulares con la forma `modulo:accion` (ej: `comunicacion:aprobar`, `liquidaciones:cerrar`). Sin permiso explícito → 403. Fail-closed. El catálogo de roles y permisos vive en la base de datos, no hardcodeado.

### Auditoría

Registro append-only de toda acción significativa: actor, impersonación activa si corresponde, materia, código de acción estandarizado, IP, user agent, filas afectadas. Ningún registro puede modificarse ni eliminarse.

---

## Módulos principales

| Módulo | Descripción |
|---|---|
| Auth | Login, 2FA TOTP, refresh rotation, recuperación de contraseña, rate limiting |
| Estructura académica | Carreras, cohortes, materias (catálogo único por tenant) |
| Usuarios y asignaciones | PII cifrada, roles con vigencia temporal, jerarquía docente |
| Equipos docentes | Asignación masiva, clonar entre períodos, modificar vigencia en bloque |
| Padrón | Import xlsx/csv + Moodle WS, versionado (la carga nueva no destruye la anterior) |
| Calificaciones | Import desde LMS, notas numéricas y textuales, umbral configurable por docente |
| Análisis | Alumnos atrasados, ranking de actividades, TPs sin corregir, monitores por rol |
| Comunicaciones | Cola con worker async, preview obligatorio, flujo de aprobación configurable |
| Encuentros y guardias | Slots recurrentes, instancias, export para aula virtual |
| Coloquios | Convocatorias con cupo, reserva de turno por alumno, resultados consolidados |
| Avisos | Tablón con scope (materia/cohorte/rol), severidad, acknowledgment por actor |
| Tareas internas | Workflow entre docentes y coordinación, comentarios, seguimiento |
| Liquidaciones | Cálculo base + plus por docente, cierre inmutable, separación factura/general |
| Auditoría y métricas | Panel de interacciones, log completo con filtros, scope por coordinador |

---

## Estado del desarrollo

| Change | Módulo | Estado |
|---|---|---|
| C-01 | foundation-setup | ✅ |
| C-02 | core-models-y-tenancy | ✅ |
| C-03 | auth-jwt-2fa | ✅ |
| C-04 | rbac-permisos-finos | ✅ |
| C-05 | audit-log | ✅ |
| C-06 | estructura-academica | ✅ |
| C-07 | usuarios-y-asignaciones | ✅ |
| C-21 | frontend-shell-y-auth | ✅ |
| C-08 al C-20 | módulos de dominio | 🔄 en desarrollo |
| C-22 al C-24 | frontend features | 🔄 en desarrollo |

El camino crítico para tener el flujo principal (importar → analizar → comunicar) en producción es: `C-01 → C-02 → C-03 → C-04 → C-06 → C-07 → C-09 → C-10 → C-11 → C-12`.

---

## Correr localmente

### Requisitos

- Docker y docker-compose
- Python 3.13
- Node.js 20+

### Backend

```bash
# Clonar el repositorio
git clone https://github.com/rexdaro/active-trace.git
cd active-trace

# Copiar variables de entorno
cp .env.example .env

# Levantar servicios
docker-compose up -d

# Correr migraciones
docker-compose exec api alembic upgrade head
```

La API queda disponible en `http://localhost:8000`. Health check: `GET /health`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

El frontend queda disponible en `http://localhost:5173`.

### Tests

```bash
# Backend
docker-compose exec api pytest --cov=app tests/

# Frontend
cd frontend && npm run test
```

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
│   ├── core/             # Configuración, auth, cifrado
│   ├── integrations/     # Moodle WS, N8N
│   └── workers/          # Worker de cola de comunicaciones
├── frontend/             # SPA React + TypeScript
├── alembic/              # Migraciones de base de datos
├── tests/                # Tests pytest
├── knowledge-base/       # Documentación de dominio (agnóstica de tecnología)
├── docs/                 # Documentación técnica
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

La documentación técnica está en `docs/ARQUITECTURA.md`.
