# Tasks: C-12 — Comunicaciones y Cola Worker

## Phase 0: Governance — Design Review

- [ ] Presentar proposal.md y spec-delta.md para review de arquitectura (Governance ALTO).
- [ ] Confirmar con el área académica el esquema de plantillas y variables de sustitución.
- [ ] Confirmar flag `requiere_aprobacion` en modelo Tenant o tabla de configuración por tenant.

## Phase 1: Model & Migration

1. [ ] Agregar `ComunicacionEstado` enum (`Pendiente`, `Enviando`, `Enviado`, `Error`, `Cancelado`) en `app/models/comunicacion.py`.
2. [ ] Implementar modelo `Comunicacion` en `app/models/comunicacion.py`, extendiendo `Base, TimestampMixin, TenantMixin` con campos:
     - id (UUID PK), tenant_id, enviado_por (FK→usuarios), materia_id (FK→materias)
     - `_destinatario` (columna "destinatario", String, cifrado vía encrypt/decrypt)
     - asunto (String), cuerpo (Text), estado (String, enum)
     - lote_id (UUID, nullable, agrupa envíos masivos)
     - enviado_at (DateTime, nullable)
   - Property `destinatario` con decrypt, setter con encrypt (mismo patrón que EntradaPadron.email).
   - Index on (tenant_id, lote_id), (tenant_id, estado).
3. [ ] Registrar `Comunicacion` en `app/models/__init__.py`.
4. [ ] Crear migración Alembic `0NN_comunicaciones` con tabla `comunicaciones`, índices, y FK constraints.

## Phase 2: Schemas & Repository

5. [ ] Implementar `app/schemas/comunicacion.py` con esquemas Pydantic:
     - `ComunicacionRead`, `ComunicacionListResponse`
     - `PreviewRequest` (destinatarios: list[str], asunto: str, cuerpo: str, materia_id: UUID, variables_opcionales)
     - `PreviewItem` (destinatario, asunto_renderizado, cuerpo_renderizado)
     - `PreviewResponse` (preview_token, items: list[PreviewItem], total, errores)
     - `ConfirmRequest` (preview_token)
     - `ConfirmResponse` (lote_id, cantidad, estados_iniciales)
     - `LoteRead` (lote_id, enviado_por, materia_id, total, pendientes, enviados, fallidos, cancelados, created_at)
     - `AprobarLoteRequest`, `AprobarIndividualRequest`, `RechazarLoteRequest`
     - `CancelarResponse`
6. [ ] Implementar `app/repositories/comunicaciones.py` heredando `BaseRepository[Comunicacion]`:
     - `create(tenant_id, enviado_por, materia_id, destinatario, asunto, cuerpo, lote_id)` → crea en Pendiente
     - `bulk_create(entries: list[dict], tenant_id)` → batch insert
     - `get_by_lote(lote_id, tenant_id)` → listar comunicaciones de un lote
     - `get_lotes(tenant_id, materia_id, offset, limit)` → listar lotes agrupados
     - `get_lote_summary(lote_id, tenant_id)` → resumen de estados del lote
     - `get_pendientes_for_worker(tenant_id, limit)` → next batch de Pendiente para worker
     - `transition_state(id, from_state, to_state, tenant_id)` → transición atómica con verificación
     - `cancel_by_lote(lote_id, tenant_id)` → Pendiente → Cancelado para todo el lote
     - `cancel_single(id, tenant_id)` → Pendiente → Cancelado para un mensaje
     - `count_by_lote(lote_id, tenant_id)` → total de mensajes en un lote

## Phase 3: Service

7. [ ] Implementar `app/services/comunicaciones.py`:
     - `_preview_store: dict[str, dict]` (token → datos de preview, mismo patrón que PadronService)
     - `preview(db, destinatarios, asunto, cuerpo, materia_id, user)`:
         - Valida destinatarios contra EntradaPadron activa de la materia (opcional)
         - Renderiza plantilla con Jinja2 para cada destinatario (variables: nombre, apellido, comision, regional, materia)
         - Genera preview_token, almacena en _preview_store
         - Retorna renderizados (sample si > N, con total count)
     - `confirm(db, preview_token, user)`:
         - Valida token, pop de _preview_store
         - Genera lote_id = uuid4()
         - Para cada destinatario: crea Comunicacion(id, lote_id, estado=Pendiente)
         - Si tenant requiere aprobación: mensajes quedan Pendiente (no dispatcheables aún)
         - Si NO requiere aprobación: mensajes quedan Pendiente y son elegibles para worker
         - Audit `COMUNICACION_ENVIAR` con lote_id y cantidad
         - Retorna lote_id, cantidad
     - `aprobar_lote(db, lote_id, user)`:
         - Verifica permiso `comunicacion:aprobar`
         - Transiciona todos los Pendiente del lote a Enviando (worker los toma)
         - Audit `COMUNICACION_APROBAR` con lote_id
     - `aprobar_individual(db, comunicacion_id, user)`:
         - Verifica permiso `comunicacion:aprobar`
         - Transiciona Pendiente → Enviando
         - Audit `COMUNICACION_APROBAR`
     - `rechazar_lote(db, lote_id, user)`:
         - Transiciona todos los Pendiente del lote a Cancelado
         - Audit `COMUNICACION_CANCELAR`
     - `cancelar_individual(db, comunicacion_id, user)`:
         - Transiciona Pendiente → Cancelado
         - Audit `COMUNICACION_CANCELAR`
     - `get_lotes(db, materia_id, user)` → listar lotes
     - `get_lote_detalle(db, lote_id, user)` → detalle de lote con estados
     - `get_estados_panel(db, materia_id, user)` → métricas de estados
8. [ ] Implementar helpers de template rendering:
     - `_render_template(template_str, variables)` → usa Jinja2 Environment with StrictUndefined
     - `_build_variables(entrada_padron, materia)` → construye dict de variables disponibles

## Phase 4: Worker

9. [ ] Implementar `app/workers/comunicaciones.py`:
     - Función `process_pending_messages(db, tenant_id, batch_size=50)`:
         - Query comunicaciones en estado Pendiente (elegibles para worker)
         - Para cada una: transiciona a Enviando → envía email vía smtplib → Enviado o Error
         - Timeout por email configurable (default 30s)
         - Reintentos: hasta 3 con backoff exponencial para errores transitorios
     - Función `run_comunicaciones_worker(app)`:
         - Loop infinito con sleep configurable (default 10s)
         - Por cada tenant activo: process_pending_messages
         - Manejo de excepciones: log y continue
     - Función `start_worker()` para arrancar desde `app/main.py` con `background_tasks` o thread separado

## Phase 5: Routing

10. [ ] Implementar `app/routers/comunicaciones.py` con prefijo `/api/v1/comunicaciones`:
     - `POST /preview` → `ComunicacionesService.preview()` — guard `comunicacion:enviar`
     - `POST /confirm` → `ComunicacionesService.confirm()` — guard `comunicacion:enviar`
     - `GET /lotes` → `ComunicacionesService.get_lotes()` — guard `comunicacion:enviar`
     - `GET /lotes/{lote_id}` → `ComunicacionesService.get_lote_detalle()` — guard `comunicacion:enviar`
     - `POST /lotes/{lote_id}/aprobar` → `ComunicacionesService.aprobar_lote()` — guard `comunicacion:aprobar`
     - `POST /{id}/aprobar` → `ComunicacionesService.aprobar_individual()` — guard `comunicacion:aprobar`
     - `POST /lotes/{lote_id}/rechazar` → `ComunicacionesService.rechazar_lote()` — guard `comunicacion:aprobar`
     - `POST /{id}/cancelar` → `ComunicacionesService.cancelar_individual()` — guard `comunicacion:enviar`
     - `GET /estados` → `ComunicacionesService.get_estados_panel()` — guard `comunicacion:enviar`
11. [ ] Registrar router en `app/main.py` con prefijo `/api/v1`.
12. [ ] Agregar seed de permisos `comunicacion:enviar` y `comunicacion:aprobar` en `app/db/seed.py` con asignación:
     - `comunicacion:enviar` → PROFESOR, COORDINADOR, ADMIN
     - `comunicacion:aprobar` → COORDINADOR, ADMIN
13. [ ] Arrancar worker en background en `app/main.py` (lifespan event).

## Phase 6: Tests

14. [ ] Tests de máquina de estados (RN-15):
     - Pendiente → Enviando → Enviado (válida)
     - Pendiente → Enviando → Error (válida)
     - Pendiente → Cancelado (válida)
     - Enviando → Cancelado (inválida → debe fallar)
     - Enviado → cualquier estado (inválida → debe fallar)
     - Error → Enviando (inválida → debe fallar)
15. [ ] Tests de preview flow (RN-16):
     - preview con destinatarios válidos retorna renderizados
     - preview con variables de sustitución reemplaza correctamente nombre, materia
     - preview con variable faltante → error claro (StrictUndefined)
     - preview_token expirado/inválido en confirm → 400
16. [ ] Tests de confirmación y batch enqueue (F3.2):
     - confirm crea comunicaciones con lote_id único
     - confirm sin aprobación (tenant flag=false) → Pendiente elegible para worker
     - confirm con aprobación (tenant flag=true) → Pendiente NO elegible hasta aprobar
     - audit registrado en confirm
17. [ ] Tests de aprobación (F3.3, RN-17):
     - aprobar lote transiciona todos Pendiente → Enviando
     - aprobar individual transiciona solo ese mensaje
     - usuario sin `comunicacion:aprobar` recibe 403
     - mensajes ya Enviando no se ven afectados por aprobar lote
     - audit registrado
18. [ ] Tests de cancelación:
     - cancelar lote transiciona todos Pendiente → Cancelado
     - cancelar individual transiciona Pendiente → Cancelado
     - cancelar mensaje Enviando → debe fallar
     - audit registrado
19. [ ] Tests de worker:
     - worker toma Pendiente, transiciona a Enviando, envía email, queda Enviado
     - worker falla en envío SMTP → queda Error
     - worker con reintentos: falla transitorio → reintenta → OK o Error final
     - worker no toma mensajes que requieren aprobación (no elegibles)
     - worker no toma mensajes Cancelados
20. [ ] Tests de destinatario cifrado:
     - destinatario se almacena cifrado en DB
     - property destinatario descifra correctamente
     - setter cifra correctamente
     - destinatario no se expone en logs
21. [ ] Tests de aislamiento multi-tenant:
     - comunicaciones de tenant A no visibles en tenant B
     - worker de tenant A no procesa mensajes de tenant B
     - lotes separados por tenant

## Phase 7: Deployment

22. [ ] Correr migración Alembic en entorno de staging.
23. [ ] Ejecutar seed de permisos `comunicacion:enviar` y `comunicacion:aprobar`.
24. [ ] Verificar endpoints con envío real: preview → confirm → worker → tracking de estados.
25. [ ] Validar flujo de aprobación: confirm con flag=true → lotes Pendiente → aprobar → worker → Enviado.
26. [ ] Validar configuración SMTP (settings) y envío real de emails.
27. [ ] Verificar panel de estados muestra distribución correcta.
