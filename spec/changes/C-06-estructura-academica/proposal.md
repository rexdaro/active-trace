# Proposal: C-06 Estructura Académica

## Why
Necesitamos establecer las entidades core del dominio académico para permitir la gestión de carreras, cohortes y materias, base fundamental para el resto del sistema.

## What Changes
- Definición de modelos `Carrera`, `Cohorte`, `Materia` en `app/models/estructura.py`.
- Implementación de routers CRUD para dichas entidades en `app/routers/admin.py`.
- Alembic migration 004.
- Tests de CRUD y restricciones de unicidad.

## Impact
- Cambios en el modelo de datos.
- Nuevos endpoints API.
- Requerimiento de nuevas migraciones.
