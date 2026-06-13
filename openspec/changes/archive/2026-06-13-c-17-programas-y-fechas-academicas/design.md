## Context

El sistema trace gestiona la estructura académica (carreras, materias, cohortes) vía C-06. Se necesita extender el modelo de datos con dos entidades: ProgramaMateria (documento oficial por materia×carrera×cohorte) y FechaAcademica (calendarización de evaluaciones por materia×cohorte×número de instancia). Ambos módulos siguen el patrón establecido: modelo → repositorio → servicio → router → schemas → tests → migración.

## Goals / Non-Goals

**Goals:**
- Modelo `ProgramaMateria` con FK a materia, carrera, cohorte; título, referencia_archivo (string opaco), cargado_at.
- Modelo `FechaAcademica` con FK a materia y cohorte; tipo enum (Parcial, TP, Coloquio, Recuperatorio), número, período, fecha, título.
- CRUD completo de programas: subir (POST), listar (GET), obtener (GET /:id), reemplazar (PUT), eliminar (DELETE).
- CRUD completo de fechas académicas: crear, listar con filtros (materia_id, cohorte_id, tipo), obtener, actualizar, eliminar.
- Endpoint de generación de fragmento HTML embebible para LMS en fechas académicas.
- Filtrado multi-tenant en todos los repositorios.
- Soft-delete en ambas entidades.
- Permiso `estructura:gestionar` para ADMIN y COORDINADOR.

**Non-Goals:**
- Almacenamiento real de archivos (la `referencia_archivo` es opaca; la gestión de archivos es responsabilidad de otro sistema/módulo).
- Notificaciones al cambiar fechas académicas.
- Validación de superposición de fechas (se asume que el coordinador gestiona el calendario de forma manual).
- Generación de calendario ICS o similar (solo fragmento HTML).
- Historial de versiones de programas (el reemplazo sobrescribe la referencia).

## Decisions

1. **Modelo de datos**: Se usa `TimestampMixin` (soft-delete via `deleted_at`) y `TenantMixin` como todas las entidades del sistema. `ProgramaMateria` referencia materia, carrera y cohorte como FK. `FechaAcademica` referencia materia y cohorte como FK. No se referencia carrera porque la cohorte ya vincula a carrera.

2. **Referencia de archivo opaca**: `referencia_archivo` es un string que contiene un identificador o ruta que solo el sistema de almacenamiento externo interpreta. El backend no valida su formato ni contenido.

3. **Tipo de fecha académica como enum**: Se usa SQLAlchemy enum con valores Parcial, TP, Coloquio, Recuperatorio. El `numero` identifica la instancia (1er parcial, 2do parcial, etc.).

4. **Permiso `estructura:gestionar`**: Se reutiliza el permiso existente de C-06. ADMIN y COORDINADOR tienen acceso completo a ambos módulos. No se crean permisos nuevos.

5. **API Structure**:
   - `/api/v1/programas` — CRUD de programas de materia
   - `/api/v1/fechas-academicas` — CRUD de fechas académicas
   - `/api/v1/fechas-academicas/{id}/html` — fragmento HTML embebible

6. **HTML fragment**: Endpoint GET que renderiza un template Jinja2 simple con tabla de fechas para una materia×cohorte. Sin estilos embebidos que choquen con el LMS.

## Risks / Trade-offs

- **Referencia de archivo opaca**: Si el sistema de almacenamiento externo cambia su esquema de referencias, habrá que migrar los valores existentes. Mitigación: se documenta que el formato de referencia_archivo es responsabilidad del sistema de almacenamiento.
- **Sin validación de superposición de fechas**: Los coordinadores pueden crear fechas superpuestas para la misma materia×cohorte. Mitigación: el UI puede advertir, pero el backend no bloquea.
- **Reemplazo sin historial**: Al reemplazar un programa, se pierde la referencia anterior. Mitigación: se audita vía AuditLog la acción de reemplazo, y el soft-delete permite recuperación.
