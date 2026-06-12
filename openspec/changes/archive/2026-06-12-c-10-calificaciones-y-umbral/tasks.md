# Tasks: C-10 — Calificaciones y Umbral

## Phase 1: Foundation

1. [ ] Crear migración Alembic `0NN_calificaciones_umbral` con tablas `calificacion` y `umbral_materia`, índices únicos para (tenant_id, entrada_padron_id, actividad, materia_id) en calificaciones y (tenant_id, asignacion_id, materia_id) en umbrales, FK con CASCADE para UmbralMateria→Asignacion y RESTRICT para Calificacion→EntradaPadron.
2. [ ] Agregar modelo SQLAlchemy `Calificacion` en `app/models/calificacion.py`, extendiendo `Base, TimestampMixin, TenantMixin` con campos: id, tenant_id, entrada_padron_id, materia_id, actividad, nota_numerica, nota_textual, aprobado, origen (enum Importado|Manual), importado_at.
3. [ ] Agregar modelo SQLAlchemy `UmbralMateria` en `app/models/umbral_materia.py`, extendiendo `Base, TimestampMixin, TenantMixin` con campos: id, tenant_id, asignacion_id, materia_id, umbral_pct, valores_aprobatorios (ARRAY de strings).
4. [ ] Registrar nuevos modelos en `app/models/__init__.py`.

## Phase 2: Schemas y Repositorios

5. [ ] Implementar `app/schemas/calificacion.py`: esquemas Pydantic para `CalificacionRead`, `CalificacionListResponse`, `PreviewRequest/Response`, `ConfirmRequest/Response`, `FinalizacionPreviewRequest/Response`, `FinalizacionConfirmResponse`, `UmbralRead`, `UmbralUpdateRequest`, `VaciarResponse`.
6. [ ] Implementar `app/repositories/calificaciones.py` con queries scoped por tenant:
    - `get_by_materia(materia_id, filtros)` → lista paginada de calificaciones
    - `get_by_entrada_y_actividad(entrada_padron_id, actividad)` → calificación existente (para cruce finalización)
    - `bulk_insert(calificaciones_list)` → batch insert con derivación de aprobado
    - `vaciar_datos_usuario(materia_id, usuario_id)` → elimina calificaciones del usuario en materia
7. [ ] Implementar `app/repositories/umbral_materia.py` con queries scoped por tenant:
    - `get_by_asignacion_y_materia(asignacion_id, materia_id)` → UmbralMateria o None
    - `upsert(asignacion_id, materia_id, umbral_pct, valores_aprobatorios)` → crea o actualiza

## Phase 3: Servicio de Calificaciones

8. [ ] Implementar `app/services/calificaciones.py` con:
    - `preview(materia_id, file)` → parsea archivo (openpyxl para xlsx, csv module para csv), detecta columnas numéricas por sufijo `(Real)` (RN-01) y textuales por valores conocidos (RN-02), mapea alumnos contra EntradaPadron, genera preview_token
    - `confirm(preview_token, actividades_seleccionadas)` → valida token, para cada (entrada_padron × actividad) crea Calificacion, deriva aprobado, registra audit `CALIFICACIONES_IMPORTAR`
    - `derivar_aprobado(nota_numerica, nota_textual, materia_id, asignacion_id)` → resuelve umbral efectivo (configurado o defecto 60%) y aplica reglas de derivación
    - `preview_finalizacion(materia_id, file)` → parsea reporte, cruza contra calificaciones existentes, filtra solo textuales (RN-08), genera lista de "posibles sin corregir"
    - `confirm_finalizacion(preview_token)` → confirma detección, registra audit
    - `vaciar_datos(materia_id, usuario_id)` → elimina calificaciones del usuario, registra audit si hay datos

## Phase 4: Routing

9. [ ] Implementar routing `POST /api/v1/materias/{materia_id}/calificaciones/preview` con upload multipart, validación de extensión y tamaño, guard `calificaciones:importar`.
10. [ ] Implementar routing `POST /api/v1/materias/{materia_id}/calificaciones/confirm` con body `{ preview_token, actividades_seleccionadas }`, transacción atómica, guard `calificaciones:importar`.
11. [ ] Implementar routing `GET /api/v1/materias/{materia_id}/calificaciones` con filtros opcionales (entrada_padron_id, actividad, aprobado), paginación, guard `calificaciones:ver`.
12. [ ] Implementar routing `PUT /api/v1/materias/{materia_id}/umbral` con body `{ umbral_pct, valores_aprobatorios }`, guard `calificaciones:importar`.
13. [ ] Implementar routing `GET /api/v1/materias/{materia_id}/umbral` que retorna umbral configurado o defecto con flag `es_defecto`, guard `calificaciones:ver`.
14. [ ] Implementar routing `POST /api/v1/materias/{materia_id}/calificaciones/finalizacion/preview` con upload, guard `calificaciones:importar`.
15. [ ] Implementar routing `POST /api/v1/materias/{materia_id}/calificaciones/finalizacion/confirm` con body `{ preview_token }`, guard `calificaciones:importar`.
16. [ ] Implementar routing `DELETE /api/v1/materias/{materia_id}/calificaciones/datos` con guard `calificaciones:vaciar` y scope RN-04.
17. [ ] Registrar router en `app/main.py` con prefijo `/api/v1`.

## Phase 5: Quality & Documentation

18. [ ] Tests de derivación `aprobado`:
    - numérica >= umbral → true
    - numérica < umbral → false
    - valor textual aprobatorio → true
    - valor textual no aprobatorio → false
    - umbral por defecto 60% cuando no hay configuración
    - umbral personalizado se usa correctamente
19. [ ] Tests de import de calificaciones:
    - preview con archivo xlsx detecta columnas numéricas y textuales
    - preview con archivo csv funciona correctamente
    - confirmación crea calificaciones solo para actividades seleccionadas
    - confirmación deriva aprobado correctamente
    - archivo con formato inválido → 400
    - alumno no encontrado en padrón → aparece en errores
20. [ ] Tests de umbral:
    - crear umbral personalizado
    - actualizar umbral existente
    - obtener umbral por defecto cuando no hay configuración
    - umbral de un docente no afecta a otro en la misma materia
21. [ ] Tests de reporte de finalización:
    - detecta entregas sin calificar (solo textuales, RN-08)
    - no incluye actividades ya calificadas
    - no incluye actividades numéricas
    - confirmación registra audit
22. [ ] Tests de vaciado scope-isolated (RN-04):
    - usuario vacía solo sus propias calificaciones en la materia
    - usuario sin calificaciones → éxito sin audit
    - calificaciones de otros usuarios no se modifican
23. [ ] Tests de aislamiento multi-tenant:
    - calificaciones de tenant A no visibles en tenant B
    - umbral de tenant A no visible en tenant B

## Phase 6: Deployment

24. [ ] Correr migración Alembic en entorno de staging.
25. [ ] Verificar endpoints con integración real (archivo xlsx de calificaciones + reporte de finalización).
26. [ ] Validar que la derivación de aprobado funciona correctamente con distintos umbrales.
