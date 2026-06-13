## Why

El sistema trace gestiona la estructura académica (carreras, materias, cohortes) pero carece de dos componentes necesarios para la operación académica diaria: (1) los programas oficiales de materia (documento por materia×carrera×cohorte) y (2) la calendarización de instancias evaluativas (parciales, TPs, coloquios). Sin estos, no hay trazabilidad del programa vigente ni visibilidad del calendario de evaluaciones por materia y cohorte.

## What Changes

1. Nuevo modelo `ProgramaMateria` con referencia a materia×carrera×cohorte, título, referencia de archivo (opaca al sistema) y timestamp de carga.
2. Nuevo modelo `FechaAcademica` con tipo (Parcial | TP | Coloquio | Recuperatorio), número de instancia, período, fecha y título, asociado a materia×cohorte.
3. Endpoints CRUD `/api/v1/programas` con subida y asociación de programa oficial.
4. Endpoints CRUD `/api/v1/fechas-academicas` con listado tabular y filtros por materia/cohorte/tipo.
5. Endpoint de generación de fragmento HTML embebible en LMS (`/api/v1/fechas-academicas/:id/html`).
6. Migración Alembic con tablas `programa_materia` y `fecha_academica`.
7. Permisos `estructura:gestionar` para ADMIN y COORDINADOR sobre programas y fechas.

## Capabilities

### New Capabilities
- `programas-de-materia`: ABM de programas oficiales de materia con asociación a materia×carrera×cohorte, archivo opaco referenciado, listado y reemplazo.
- `fechas-academicas`: CRUD de fechas de evaluaciones (parciales, TPs, coloquios, recuperatorios) por materia×cohorte×número, vista tabular, y generación de fragmento HTML para LMS.

### Modified Capabilities
- Ninguna. No se modifican requerimientos de capacidades existentes.

## Impact

- **Database**: Nuevas tablas `programa_materia` y `fecha_academica`.
- **Models**: Nuevo archivo `app/models/programa_materia.py` y `app/models/fecha_academica.py`, registrados en `app/models/__init__.py`.
- **Repository**: Nuevos `app/repositories/programas_materia.py` y `app/repositories/fechas_academicas.py`.
- **Service**: Nuevos `app/services/programas_materia.py` y `app/services/fechas_academicas.py`.
- **Router**: Nuevos `app/routers/programas.py` y `app/routers/fechas_academicas.py`, registrados en `app/main.py`.
- **Schemas**: Nuevos `app/schemas/programa_materia.py` y `app/schemas/fecha_academica.py`.
- **Migration**: Una migración Alembic con las tablas `programa_materia` y `fecha_academica`.
- **Tests**: 8 archivos de test: modelo, repositorio, servicio y router para cada módulo.
