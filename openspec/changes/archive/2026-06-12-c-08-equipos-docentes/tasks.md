# Tasks: C-08 — Equipos Docentes

## Phase 1: Schemas and Service Layer

1. [ ] Crear `app/schemas/equipos.py` con:
    - `AsignacionMasivaRequest` (asignaciones: list[AsignacionCreate])
    - `AsignacionMasivaResponse` (creadas: int, asignaciones: list[AsignacionRead])
    - `ClonarRequest` (origen_contexto_id, destino_contexto_id, nuevo_desde, nuevo_hasta)
    - `ClonarResponse` (clonadas: int, asignaciones: list[AsignacionRead])
    - `ModificarVigenciaRequest` (contexto_id, nuevo_desde, nuevo_hasta)
    - `ModificarVigenciaResponse` (modificadas: int)
    - `ExportRequest` como query param contexto_id

2. [ ] Implementar `app/services/equipos.py` con:
    - `mis_equipos(db, user)` → query Asignacion WHERE user_id = user.id AND tenant_id = user.tenant_id
    - `asignar_masiva(db, user, request)` → bulk create en transacción, audit ASIGNACION_MODIFICAR
    - `clonar(db, user, request)` → query activas de origen, duplicar con nuevo contexto y fechas, audit
    - `modificar_vigencia(db, user, request)` → UPDATE bulk desde/hasta WHERE contexto_id, audit
    - `exportar(db, user, contexto_id)` → query Asignacion + Usuario + Role join, armar CSV

## Phase 2: Router and Integration

3. [ ] Crear `app/routers/equipos.py` con prefix `/api/equipos` y guard `equipos:asignar`:
    - `GET /mis-equipos` → llama a `mis_equipos()`
    - `GET /` → query params opcionales (materia_id, carrera_id, cohorte_id, role_id, user_id, vigente)
    - `POST /asignacion-masiva` → recibe `AsignacionMasivaRequest`, llama a `asignar_masiva()`
    - `POST /clonar` → recibe `ClonarRequest`, llama a `clonar()`
    - `PUT /vigencia` → recibe `ModificarVigenciaRequest`, llama a `modificar_vigencia()`
    - `GET /export` → query param `contexto_id`, devuelve `StreamingResponse` con CSV (UTF-8 BOM)

4. [ ] Registrar router en `app/main.py`: `app.include_router(equipos_router)`

## Phase 3: Audit Integration

5. [ ] Verificar que el código de acción `ASIGNACION_MODIFICAR` existe en el seed de Audit (o agregarlo en `app/db/seed.py`)
6. [ ] Integrar `AuditService.log_action()` en cada operación mutante del service:
    - `asignar_masiva`: filas_afectadas = len(asignaciones)
    - `clonar`: filas_afectadas = cantidad clonada
    - `modificar_vigencia`: filas_afectadas = cantidad modificada

## Phase 4: Testing

7. [ ] Tests de `mis_equipos`: crear asignaciones para usuario U1 y U2, verificar que `mis_equipos(U1)` solo devuelve las de U1 y respeta tenant isolation.
8. [ ] Tests de asignación masiva: enviar N asignaciones válidas → verificar N filas creadas, audit registrada. Enviar lista vacía → 422. Enviar asignación con FK inválido → rollback completo.
9. [ ] Tests de clonado entre cohortes: crear 3 asignaciones activas en contexto origen, ejecutar clonar a contexto destino → verificar 3 nuevas asignaciones en destino con fechas ajustadas. Verificar que asignaciones vencidas NO se clonan.
10. [ ] Tests de clonado sin asignaciones activas: contexto origen sin asignaciones vigentes → response `clonadas: 0`, sin error.
11. [ ] Tests de modificación de vigencia en bloque: cambiar desde/hasta de un equipo → verificar que todas las asignaciones del contexto reflejan el cambio. Verificar que asignaciones de OTRO contexto no se modifican.
12. [ ] Tests de export CSV: endpoint devuelve `text/csv` con cabeceras esperadas, filas correctas, UTF-8 BOM al inicio.
13. [ ] Tests de autorización: endpoint sin token → 401. Token sin permiso `equipos:asignar` → 403.
14. [ ] Tests de tenant isolation: tenant A crea asignaciones, tenant B no las ve en ningún endpoint.
