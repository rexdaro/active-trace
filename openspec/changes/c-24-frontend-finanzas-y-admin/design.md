# Design: C-24-frontend-finanzas-y-admin

## Pages
### Liquidaciones (/liquidaciones)
- Vista del perÃ­odo: tabla de docentes con base+plus=total
- SegmentaciÃ³n: general / NEXO / factura
- KPIs: total a pagar, cant docentes, etc.
- Cerrar liquidaciÃ³n (botÃ³n con confirmaciÃ³n)
- Historial de liquidaciones cerradas

### Facturas (/facturas)
- Listar facturas por perÃ­odo
- Cargar factura (detalle, referencia archivo)
- Marcar como abonada

### Grilla Salarial (/salarios)
- ABM SalarioBase: CRUD por rol con vigencia
- ABM SalarioPlus: CRUD por grupo+rol con vigencia

### Estructura AcadÃ©mica (/estructura)
- ABM Carreras
- ABM Cohortes por carrera
- ABM Materias

### AuditorÃ­a (/auditoria)
- Panel de mÃ©tricas (acciones por dÃ­a, etc.)
- Log completo con filtros (fechas, materia, usuario, acciÃ³n)

### Usuarios (/usuarios)
- Listar usuarios del tenant
- Administrar roles y asignaciones
