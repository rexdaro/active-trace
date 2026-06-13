# Design: C-20-perfil-y-mensajeria-interna

## Models
**MensajeInterno:** id, tenant_id, remitente_id (FK->usuarios), destinatario_id (FK->usuarios), asunto, cuerpo, leido(bool), hilo_id (UUID, agrupa respuestas), created_at.

## API
- `GET /api/v1/perfil` — datos del usuario autenticado
- `PUT /api/v1/perfil` — editar nombre, datos fiscales/bancarios, regional, modalidad_cobro. CUIL no modificable.
- `GET /api/v1/inbox` — mensajes recibidos (no eliminados)
- `GET /api/v1/inbox/enviados` — mensajes enviados
- `POST /api/v1/inbox` — enviar mensaje a otro usuario del tenant
- `POST /api/v1/inbox/{id}/responder` — responder en hilo
- `PUT /api/v1/inbox/{id}/leer` — marcar como leído
