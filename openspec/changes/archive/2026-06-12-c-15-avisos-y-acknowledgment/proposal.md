# Proposal: c-15-avisos-y-acknowledgment

## Why
The system needs a mechanism to publish announcements (avisos) that are targeted to specific audiences (by role, materia, cohorte, or global) with configurable visibility windows and optional read acknowledgment tracking. This is required by FL-09 (publicación de aviso) and F3.5 (ABM avisos).

## What Changes
1. New models `Aviso` (with scope: Global/PorMateria/PorCohorte/PorRol, severidad, vigencia, orden, requiere_ack) and `AcknowledgmentAviso` (aviso_id, usuario_id, confirmado_at).
2. ABM endpoints at `/api/avisos/*` with `avisos:publicar` permission (COORDINADOR/ADMIN).
3. Visualization endpoint filtered by audience scope (RN-20) and visibility window (RN-18).
4. Acknowledgment confirmation endpoint for any role (`avisos:confirmar`); contadores derivados de `AcknowledgmentAviso` (RN-19).
5. Priority ordering (orden column).

## Impact
- **Database**: New tables `avisos` and `acknowledgments_aviso`.
- **API**: New router `app/routers/avisos.py` with CRUD + visualization + acknowledgment endpoints.
- **Models**: New model file `app/models/aviso.py`.
- **Permissions**: New permissions `avisos:publicar`, `avisos:confirmar`, `avisos:ver`.
- **Audit**: Actions `AVISO_CREAR`, `AVISO_EDITAR`, `AVISO_ELIMINAR`, `AVISO_CONFIRMAR`.
