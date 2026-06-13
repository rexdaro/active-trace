# Proposal: C-18-liquidaciones-y-honorarios

## Why
El sistema necesita gestionar la liquidación de honorarios de docentes: grilla salarial (base + plus por grupo/rol), cálculo de liquidación por período, cierre (inmutable), historial y gestión de facturas de docentes que facturan. Requerido por épica 10 (F10.1-F10.6).

## What Changes
1. Modelos `SalarioBase` (rol, monto, vigencia), `SalarioPlus` (grupo, rol, monto, vigencia), `Liquidacion` (periodo, base+plus=total, estado Abierta/Cerrada), `Factura` (periodo, detalle, estado Pendiente/Abonada).
2. CRUD grilla salarial (`/api/v1/salarios/*`, FINANZAS).
3. Cálculo de liquidación del período (base vigente + plus por grupo de materias).
4. Cierre de liquidación (inmutable). Historial de liquidaciones.
5. Gestión de facturas de docentes que facturan. Separación contable NEXO/factura/no-factura.
6. Guards `liquidaciones:*` (FINANZAS).

## Impact
- **Database**: New tables `salarios_base`, `salarios_plus`, `liquidaciones`, `facturas`.
- **API**: New routers `app/routers/liquidaciones.py`, `app/routers/facturas.py`, `app/routers/salarios.py`.
- **Models**: New model files.
- **Permissions**: New permissions `liquidaciones:*`.
- **Audit**: Actions `LIQUIDACION_CERRAR`.
