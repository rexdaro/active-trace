# Implementation Tasks — C-14 evaluaciones-y-coloquios

Orden de implementación (respetar dependencias entre pasos):

1. [ ] **Model: entidades y enums** — crear `Evaluacion`, `ReservaEvaluacion`, `ResultadoEvaluacion` con `TimestampMixin` + `TenantMixin`. Enums: `TipoEvaluacion` (Parcial/TP/Coloquio/Recuperatorio), `EstadoReserva` (Activa/Cancelada). Alinear con KB E14.
2. [ ] **Migration: crear tablas** — migration Alembic `evaluacion`, `reserva_evaluacion`, `resultado_evaluacion` con FK a tenant, materia, cohorte, usuario (alumno). Índices: `(tenant_id, materia_id)`, `(tenant_id, evaluacion_id)` en reservas y resultados. Unique constraint `(evaluacion_id, alumno_id)` en `resultado_evaluacion`.
3. [ ] **Schemas: Pydantic v2** — request/response para convocatoria (create con materia_id, instancia, tipo, dias_disponibles, cupo_por_dia), importar alumnos (lista de entrada_padron_ids o usuario_ids), reservar turno (fecha_hora), cancelar, resultado (nota_final), métricas, listado con stats.
4. [ ] **Repository: ColoquiosRepository** — CRUD base para Evaluacion + filtrar por materia/tenant. Métodos: contar_reservas_activas(evaluacion_id, fecha), contar_reservas_por_evaluacion, contar_alumnos_importados, contar_notas_registradas, upsert_resultado. Scope tenant always.
5. [ ] **Service: ColoquiosService** — `crear_convocatoria(data)` crea Evaluacion con días disponibles. `importar_alumnos(evaluacion_id, alumno_ids)` vincula alumnos existentes del padrón. `reservar_turno(evaluacion_id, alumno_id, fecha_hora)` valida cupo diario, crea ReservaEvaluacion Activa. `cancelar_reserva(reserva_id)` cambia estado a Cancelada. `registrar_resultado(evaluacion_id, alumno_id, nota_final)` upsert en ResultadoEvaluacion. `get_metricas()` retorna total alumnos, instancias activas, reservas activas, notas registradas. `get_admin_view()` listado global con stats.
6. [ ] **Router: /api/v1/coloquios** — endpoints con guard `coloquios:gestionar` (COORDINADOR/ADMIN para gestión), `coloquios:reservar` (ALUMNO para reserva), `coloquios:ver` (consulta). Incluir auditoría con códigos `COLOQUIO_CREAR`, `RESERVA_CREAR`, `RESERVA_CANCELAR`, `RESULTADO_REGISTRAR`.
7. [ ] **Seed: permisos** — agregar `coloquios:gestionar` (COORDINADOR, ADMIN), `coloquios:reservar` (ALUMNO), `coloquios:ver` (COORDINADOR, ADMIN, PROFESOR) al seed de RBAC.
8. [ ] **Tests: crear convocatoria** — crear Evaluacion con datos válidos, verificar campos, verificar que el cupo por día se almacena correctamente.
9. [ ] **Tests: reserva con cupo** — crear Evaluacion con cupo_por_dia=2, hacer 2 reservas en distintas fechas, verificar que ambas quedan Activas.
10. [ ] **Tests: reserva sin cupo** — crear Evaluacion con cupo_por_dia=1, hacer reserva, intentar segunda en el mismo día → 409 Conflict.
11. [ ] **Tests: cancelar reserva** — reserva Activa se cancela, cupo se libera, nueva reserva en mismo día es exitosa.
12. [ ] **Tests: importar alumnos** — importar lista de alumno_ids a Evaluacion, verificar que aparecen en convocados.
13. [ ] **Tests: métricas** — verificar que total alumnos, instancias activas, reservas activas, notas registradas reflejan el estado actual.
14. [ ] **Tests: resultado consolidado** — registrar nota_final para alumno, consultar resultado, verificar persistencia y upsert.
15. [ ] **Tests: permisos** — ALUMNO sin `coloquios:gestionar` recibe 403 en endpoints de gestión. ALUMNO con `coloquios:reservar` accede a reserva. COORDINADOR/ADMIN accede sin restricción.
