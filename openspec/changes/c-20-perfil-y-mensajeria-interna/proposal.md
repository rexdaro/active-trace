# Proposal: C-20-perfil-y-mensajeria-interna

## Why
Los usuarios necesitan poder editar su perfil (nombre, datos fiscales/bancarios, regional, modalidad de cobro) y tener una bandeja de mensajes interna para comunicarse entre usuarios registrados. Requerido por F11.1, F3.4/F11.2, F11.3.

## What Changes
1. Endpoint GET/PUT `/api/v1/perfil` para ver y editar perfil propio (CUIL solo lectura).
2. Modelo `MensajeInterno` con hilos de mensajes entre usuarios del mismo tenant.
3. Endpoints `/api/v1/inbox/*` para bandeja de entrada: listar, leer, enviar, responder.
4. Reusa logout de C-03.

## Impact
- **Database**: New table `mensajes_internos`.
- **API**: New routers `app/routers/perfil.py`, `app/routers/inbox.py`.
- **Models**: New model file `app/models/mensaje_interno.py`.
- **Permissions**: Ninguna nueva (cualquier usuario autenticado).
