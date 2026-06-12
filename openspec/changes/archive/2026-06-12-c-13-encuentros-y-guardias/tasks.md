# Implementation Tasks — C-13 encuentros-y-guardias

Orden de implementación (respetar dependencias entre pasos):

1. [ ] **Model: entidades y enums** — crear `SlotEncuentro`, `InstanciaEncuentro`, `Guardia` con `TimestampMixin` + `TenantMixin` + soft delete. Enums: `EstadoInstancia` (Programado/Realizado/Cancelado), `EstadoGuardia` (Pendiente/Realizada/Cancelada), `DiaSemana` (Lunes-Domingo). Alinear con KB E9, E10, E11.
2. [ ] **Migration: crear tablas** — migration Alembic `slot_encuentro`, `instancia_encuentro`, `guardia` con FK a tenant, materia, asignacion, usuario (slot.creado_por). Índices: `(tenant_id, materia_id)`, `(tenant_id, slot_id)` en instancias.
3. [ ] **Schemas: Pydantic v2** — request/response para slot (create con cant_semanas), instancia (create para encuentro único, patch para edición), guardia (create, list, export). Validaciones: horario formato `HH:MM–HH:MM`, fecha_inicio no pasada.
4. [ ] **Repository: SlotEncuentroRepository** — CRUD base + listar por materia, obtener slot con instancias. Scope tenant always.
5. [ ] **Repository: InstanciaEncuentroRepository** — CRUD base + listar por materia/estado/rango fechas, bulk_create para generación recurrente. Scope tenant always.
6. [ ] **Repository: GuardiaRepository** — CRUD base + listar por usuario/materia/cohorte, export. Scope tenant always.
7. [ ] **Service: EncuentrosService** — `crear_recurrente(slot_data)` genera fecha_inicio + `cant_semanas` instancias sumando 7 días (RN-13). `crear_unico(instancia_data)` sin slot_id. `editar_instancia(id, estado, meet_url, video_url, comentario)` (RN-14). `generar_html(materia_id)` produce bloque `<table>` sanitizado con encuentros pendientes/futuros.
8. [ ] **Service: GuardiasService** — `registrar(guardia_data)` con validación de no superposición. `listar(filtros)` con scope según rol. `exportar(filtros)` produce CSV/JSON.
9. [ ] **Router: /api/v1/encuentros** — endpoints con guard `encuentros:gestionar` (PROFESOR scoped a materias propias, COORDINADOR/ADMIN global). Audit `ENCUENTRO_CREAR` en creación, `ENCUENTRO_EDITAR` en edición.
10. [ ] **Router: /api/v1/guardias** — `POST` con guard `guardias:registrar` (TUTOR), `GET` con guard `guardias:ver` (COORDINADOR/ADMIN). Audit `GUARDIA_REGISTRAR`.
11. [ ] **Seed: permisos** — agregar `encuentros:gestionar`, `encuentros:ver`, `guardias:registrar`, `guardias:ver` al seed de RBAC.
12. [ ] **Tests: recurrente generation** — crear slot con cant_semanas=3, verificar que se generan 3 instancias con fechas correctas (día_semana + 7 días). Verificar RN-13 (modo recurrente vs único).
13. [ ] **Tests: encuentro único** — crear instancia sin slot_id, verificar campo slot_id es None. Verificar creación exitosa.
14. [ ] **Tests: edición de instancia** — cambiar estado a Realizado, agregar video_url, verificar persistencia. Verificar RN-14 (slot no afectado).
15. [ ] **Tests: guardia registro y export** — TUTOR registra guardia, COORDINADOR consulta global y exporta CSV. Verificar no superposición.
16. [ ] **Tests: permisos** — PROFESOR sin permiso `encuentros:gestionar` recibe 403. TUTOR sin `guardias:registrar` recibe 403. COORDINADOR/ADMIN accede sin restricción de materia.
