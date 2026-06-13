# Design: C-18-liquidaciones-y-honorarios

## Models

**SalarioBase:** id, tenant_id, rol (enum: PROFESOR/TUTOR/NEXO/COORDINADOR), monto (Decimal), desde (date), hasta (date nullable).

**SalarioPlus:** id, tenant_id, grupo (str), rol, descripcion, monto (Decimal), desde (date), hasta (date nullable).

**Liquidacion:** id, tenant_id, cohorte_id, periodo (str "YYYY-MM"), usuario_id, rol, comisiones (list[str]), monto_base, monto_plus, total, es_nexo (bool), excluido_por_factura (bool), estado (enum: Abierta/Cerrada).

**Factura:** id, tenant_id, usuario_id, periodo, detalle, referencia_archivo, tamano_kb, estado (Pendiente/Abonada), cargada_at, abonada_at.

## API
- `GET /api/v1/salarios` — listar grilla
- `POST /api/v1/salarios/base` — crear SalarioBase
- `POST /api/v1/salarios/plus` — crear SalarioPlus
- `GET /api/v1/liquidaciones?periodo=` — listar liquidaciones del período
- `POST /api/v1/liquidaciones/calcular` — calcular liquidaciones del período
- `POST /api/v1/liquidaciones/{id}/cerrar` — cerrar (inmutable)
- `GET /api/v1/liquidaciones/historial` — historial
- `GET /api/v1/facturas` — listar facturas
- `POST /api/v1/facturas` — cargar factura
- `PUT /api/v1/facturas/{id}/abonar` — marcar abonada

## Reglas de negocio
- Cierre inmutable: una liquidación Cerrada no puede modificarse (RN-22)
- Base vigente: se busca SalarioBase con rol coincidente y desde <= periodo <= hasta
- Plus: se suman todos los SalarioPlus del docente según sus comisiones
- Separación NEXO/factura/general en vista de liquidaciones (F10.6)
