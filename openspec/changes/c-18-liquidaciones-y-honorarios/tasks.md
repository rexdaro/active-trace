# Tasks: C-18-liquidaciones-y-honorarios

## Implementation Checklist

- [x] 1. Create models: `SalarioBase`, `SalarioPlus`, `Liquidacion`, `Factura`
- [x] 2. Register models in `app/models/__init__.py`
- [x] 3. Create Alembic migration `add_liquidaciones`
- [x] 4. Create Pydantic schemas for all 4 models
- [x] 5. Create repositories: `SalarioRepository`, `LiquidacionRepository`, `FacturaRepository`
- [x] 6. Create `LiquidacionService` (cálculo, cierre, historial)
- [x] 7. Create routers: `app/routers/salarios.py`, `app/routers/liquidaciones.py`, `app/routers/facturas.py`
- [x] 8. Add permission seeds for `liquidaciones:*`
- [x] 9. Register routers in `app/main.py`
- [x] 10. Write tests: cálculo, cierre inmutable, exclusión factura, NEXO
