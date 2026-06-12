# Tasks: C-09 — Padrón Ingesta Moodle

## Phase 1: Foundation

1. [ ] Crear migración Alembic `0NN_version_padron` con tablas `version_padron` y `entrada_padron`, índices únicos parciales para activa por (materia, cohorte), y FK con CASCADE.
2. [ ] Agregar modelos SQLAlchemy `VersionPadron` y `EntradaPadron` en `app/models/`, extendiendo `Base, TimestampMixin, TenantMixin`.
3. [ ] Registrar nuevos modelos en `app/models/__init__.py`.
4. [ ] Agregar columna `moodle_ws_url` y `moodle_token` al modelo Tenant (si no existen de C-07).

## Phase 2: Core — Import de Padrón (Archivo)

5. [ ] Implementar `app/schemas/padron.py`: esquemas Pydantic para `PadronPreviewRequest/Response`, `PadronConfirmRequest/Response`, `VersionPadronRead`, `EntradaPadronRead`, `VaciarRequest`.
6. [ ] Implementar `app/repositories/padron.py` con queries scoped por tenant:
    - `get_activa(materia_id, cohorte_id)` → VersionPadron activa
    - `desactivar_anterior(materia_id, cohorte_id)` → desactiva versión activa previa
    - `crear_version(...)` → inserta nueva VersionPadron
    - `bulk_insert_entradas(version_id, entries)` → batch insert
    - `vaciar_datos_usuario(materia_id, usuario_id)` → elimina versiones del usuario en materia
7. [ ] Implementar `app/services/padron.py` con:
    - `preview(file, materia_id, cohorte_id)` → parsea archivo (openpyxl para xlsx, csv module para csv), mapea columnas esperadas (nombre, apellidos, email, comision, regional), genera preview_token
    - `confirm(preview_token)` → valida token, crea VersionPadron activa, desactiva anterior, bulk insert EntradaPadron, registra audit `PADRON_CARGAR`
    - `vaciar_datos(materia_id, usuario_id)` → elimina versiones del usuario, audita
8. [ ] Implementar routing de preview: `POST /api/v1/padron/preview` con upload multipart, validación de extensión y tamaño.
9. [ ] Implementar routing de confirm: `POST /api/v1/padron/confirm` con `preview_token`, transacción atómica.
10. [ ] Implementar routing de vaciado: `DELETE /api/v1/padron/{materia_id}/datos` con guard `padron:vaciar` y scope RN-04.
11. [ ] Implementar routing de versiones: `GET /api/v1/padron/{materia_id}/versiones` con guard `padron:ver`.

## Phase 3: Moodle WS Integration

12. [ ] Implementar `app/integrations/moodle_ws.py`:
    - Cliente HTTP asíncrono (`httpx.AsyncClient`) con token de servicio
    - `get_participants(materia_id)` → obtiene listado de alumnos desde WS Moodle
    - `get_activities(materia_id)` → obtiene actividades evaluables
    - Retry 3 veces con backoff exponencial
    - Timeout configurable por tenant
    - Error mapping: conexión fallida → `502 Bad Gateway`
13. [ ] Implementar sync on-demand: `POST /api/v1/padron/sync` que gatilla `PadronService.sync_from_moodle(materia_id)`, opcionalmente para todas las materias.
14. [ ] Implementar worker `app/workers/sync_nightly.py` (tarea programada vía APScheduler o similar) que recorre materias activas con `moodle_ws_url` configurado y ejecuta sync.

## Phase 4: Quality & Documentation

15. [ ] Tests de versionado: activar nueva versión desactiva la anterior para el mismo (materia, cohorte), no afecta otras materias/cohortes.
16. [ ] Tests de import xlsx: archivo bien formado → preview correcto + confirm → entradas en DB.
17. [ ] Tests de import csv: idem, con delimitador configurable.
18. [ ] Tests de entrada sin usuario_id: alumno sin cuenta → se crea EntradaPadron con `usuario_id = NULL`.
19. [ ] Tests de aislamiento tenant: datos del tenant A no visibles en tenant B.
20. [ ] Tests de Moodle WS mock: mockear `moodle_ws.get_participants()`, verificar que sync crea VersionPadron con `origen=MoodleWS`.
21. [ ] Tests de fallback 502: mockear error de conexión a Moodle WS, verificar que la sync retorna 502 con mensaje de error y reintento.
22. [ ] Tests de vaciado RN-04: usuario U1 vacía materia M1 → solo se borran versiones de U1 en M1, no las de U2.

## Phase 5: Deployment

23. [ ] Correr migración Alembic en entorno de staging.
24. [ ] Verificar endpoints con integración real (xlsx + csv).
25. [ ] Validar que el nightly sync no genera duplicados en ejecuciones concurrentes.
