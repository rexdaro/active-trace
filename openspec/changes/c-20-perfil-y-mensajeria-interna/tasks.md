# Tasks: C-20-perfil-y-mensajeria-interna

## Implementation Checklist

- [x] 1. Create `MensajeInterno` model in `app/models/mensaje_interno.py`
- [x] 2. Register model in `app/models/__init__.py`
- [x] 3. Create Alembic migration `add_mensajes_internos`
- [x] 4. Create Pydantic schemas in `app/schemas/perfil.py` and `app/schemas/inbox.py`
- [x] 5. Create `app/routers/perfil.py` with GET/PUT perfil
- [x] 6. Create router for inbox (listar, enviar, responder) in `app/routers/inbox.py`
- [x] 7. Register routers in `app/main.py`
- [x] 8. Write tests: perfil, inbox CRUD, mensajes hilo
