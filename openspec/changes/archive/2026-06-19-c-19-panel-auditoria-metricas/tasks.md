# Tasks: C-19-panel-auditoria-metricas

## Implementation Checklist

- [ ] 1. Add permission `auditoria:ver` to seed data
- [ ] 2. Create Pydantic schemas in `app/schemas/auditoria.py`
- [ ] 3. Create `AuditoriaService` in `app/services/auditoria.py`
- [ ] 4. Create router `app/routers/auditoria.py` with endpoints:
       - GET /api/v1/auditoria/metricas (panel interacciones)
       - GET /api/v1/auditoria/log (log completo con filtros)
- [ ] 5. Register router in `app/main.py`
- [ ] 6. Write tests: mÃ©tricas, filtros, permisos (scope propio coordinador)
