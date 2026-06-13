# Design: C-19-panel-auditoria-metricas

## API (solo lectura sobre AuditLog)
- `GET /api/v1/auditoria/metricas` — panel:
  - acciones_por_dia: agregado COUNT GROUP BY DATE(fecha_hora)
  - comunicaciones_por_docente: COUNT de acciones COMUNICACION_* agrupado por actor_id
  - ultimas_acciones: últimas N (default 200) entradas ordenadas por fecha DESC
- `GET /api/v1/auditoria/log` — log completo paginado con filtros:
  - ?fecha_desde=, ?fecha_hasta=, ?materia_id=, ?usuario_id=, ?accion=, ?estado=
  - scope `(propio)` para COORDINADOR: solo ve acciones de usuarios de sus materias
